# Especificación Técnica — Hito 4: Envío Automático de Facturas por Correo con PDF Adjunto

## Overview
Implementación del envío automático de facturas por correo electrónico con PDF adjunto, permitiendo a los usuarios enviar facturas generadas directamente desde la interfaz del sistema.

---

## 1. Configuración de Correo en Django (`settings.py`)

### 1.1 Configuración por Entorno

```python
# core/settings.py

# Configuración de email según entorno
import os

if DEBUG:
    # Desarrollo/Tests: usa backend en memoria o consola
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    # Alternativa para ver en consola: 'django.core.mail.backends.console.EmailBackend'
else:
    # Producción: SMTP real
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Configuración común
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Sistema Facturación <noreply@facturacion.com>')
EMAIL_SUBJECT_PREFIX = '[Facturación] '
```

### 1.2 Variables de Entorno Requeridas (`.env`)

```env
# Desarrollo
EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend

# Producción
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=facturacion@empresa.com
EMAIL_HOST_PASSWORD=tu_password_app
DEFAULT_FROM_EMAIL=Sistema Facturación <noreply@empresa.com>
```

---

## 2. Generación del PDF Adjunto en Memoria

### 2.1 Utilidad para Generar PDF en Memoria

```python
# facturacion/utils/pdf.py
from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML

def generar_pdf_factura(factura):
    """
    Genera el PDF de una factura en memoria y retorna bytes.
    """
    from facturacion.models import DetalleVenta
    
    contexto = {
        'factura': factura,
        'detalles': factura.detalles.select_related('producto').all(),
        'cliente': factura.cliente,
        'usuario': factura.usuario,
    }
    
    html_string = render_to_string('facturacion/factura_pdf.html', contexto)
    
    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(
        pdf_file, 
        base_url=None,  # No necesitamos base_url para PDF adjunto
        presentational_hints=True
    )
    
    pdf_file.seek(0)
    return pdf_file.read()
```

---

## 3. Vista `FacturaEmailView` (CBV)

### 3.1 Especificación de la Vista

| Atributo | Valor |
|----------|-------|
| **Herencia** | `PermissionRequiredMixin` + `LoginRequiredMixin` + `View` |
| **Permiso requerido** | `facturacion.view_cabecerafactura` |
| **Método HTTP** | `POST` (envío bajo demanda) |
| **URL** | `facturas/<uuid:pk>/email/` |
| **Nombre URL** | `factura_email` |

### 3.2 Lógica de la Vista

```python
# facturacion/views.py
from django.views import View
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class FacturaEmailView(PermissionRequiredMixin, LoginRequiredMixin, View):
    """
    Envía una factura por correo electrónico con PDF adjunto.
    
    POST /facturacion/facturas/<uuid:pk>/email/
    Body JSON: {"destinatario": "cliente@email.com", "asunto": "...", "mensaje": "..."}
    """
    permission_required = ('facturacion.view_cabecerafactura',)
    
    def post(self, request, *args, **kwargs):
        factura = self.get_object()
        
        # Validar datos de entrada
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
        
        destinatario = data.get('destinatario', '').strip()
        asunto = data.get('asunto', '').strip()
        mensaje = data.get('mensaje', '').strip()
        
        if not destinatario:
            return JsonResponse({'success': False, 'error': 'Destinatario requerido'}, status=400)
        
        if not asunto:
            asunto = f'Factura {factura.numero_factura}'
        
        if not mensaje:
            mensaje = 'Adjunto encontrará la factura correspondiente.'
        
        try:
            # 1. Generar PDF en memoria
            pdf_bytes = generar_pdf_factura(factura)
            
            # 2. Renderizar template HTML del email
            html_message = render_to_string('emails/factura_email.html', {
                'factura': factura,
                'mensaje_personalizado': mensaje,
            })
            
            # 3. Crear y enviar email
            email = EmailMessage(
                subject=asunto,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destinatario],
            )
            email.content_subtype = 'html'
            
            # Adjuntar PDF
            nombre_archivo = f"factura_{factura.numero_factura}.pdf"
            email.attach(nombre_archivo, pdf_bytes, 'application/pdf')
            
            # Enviar (fail_silently=False para detectar errores)
            email.send(fail_silently=False)
            
            return JsonResponse({
                'success': True,
                'message': f'Factura {factura.numero_factura} enviada a {destinatario}'
            })
            
        except Exception as e:
            logger.error(f"Error enviando factura {factura.numero_factura}: {e}")
            return JsonResponse({
                'success': False, 
                'error': f'Error al enviar correo: {str(e)}'
            }, status=500)
```

### 3.3 Registro en URLs

```python
# facturacion/urls.py
path('facturas/<uuid:pk>/email/', views.FacturaEmailView.as_view(), name='factura_email'),
```

---

## 4. Plantilla HTML del Email (`templates/emails/factura_email.html`)

### 4.1 Estructura del Template

```html
<!-- templates/emails/factura_email.html -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Factura {{ factura.numero_factura }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .container { background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #1e3a5f; color: #fff; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .header p { margin: 10px 0 0; opacity: 0.9; font-size: 14px; }
        .content { padding: 30px; }
        .greeting { font-size: 16px; margin-bottom: 20px; }
        .message { background: #f8f9fa; border-left: 4px solid #1e3a5f; padding: 15px; margin: 20px 0; border-radius: 4px; white-space: pre-wrap; }
        .invoice-summary { background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .invoice-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
        .invoice-row:last-child { border-bottom: none; }
        .label { color: #666; }
        .value { font-weight: 600; color: #333; }
        .total-row { font-size: 18px; font-weight: 700; color: #1e3a5f; border-top: 2px solid #1e3a5f; margin-top: 10px; padding-top: 15px; }
        .footer { text-align: center; padding: 20px; color: #999; font-size: 12px; border-top: 1px solid #eee; }
        .btn { display: inline-block; background: #1e3a5f; color: #fff; padding: 12px 24px; border-radius: 4px; text-decoration: none; font-weight: 600; }
        .attachment-note { background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 12px; margin: 20px 0; font-size: 13px; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 Factura {{ factura.numero_factura }}</h1>
            <p>Sistema de Facturación - {{ factura.fecha_emision|date:"d/m/Y H:i" }}</p>
        </div>
        
        <div class="content">
            <p class="greeting">Estimado/a {{ cliente.nombre_razon_social }},</p>
            
            <div class="message">{{ mensaje_personalizado|default:"Adjunto encontrará la factura correspondiente a su compra."|linebreaksbr }}</div>
            
            <div class="invoice-summary">
                <h3 style="margin-top: 0;">Resumen de la Factura</h3>
                <div class="invoice-row">
                    <span class="label">N° Factura:</span>
                    <span class="value">{{ factura.numero_factura }}</span>
                </div>
                <div class="invoice-row">
                    <span class="label">Fecha:</span>
                    <span class="value">{{ factura.fecha_emision|date:"d/m/Y H:i" }}</span>
                </div>
                <div class="invoice-row">
                    <span class="label">Cliente:</span>
                    <span class="value">{{ cliente.nombre_razon_social }}</span>
                </div>
                <div class="invoice-row">
                    <span class="label">Tipo:</span>
                    <span class="value">{{ factura.get_tipo_documento_display }}</span>
                </div>
                <div class="invoice-row total-row">
                    <span class="label">Total Bs:</span>
                    <span class="value">{{ factura.total_bs|floatformat:2 }} Bs</span>
                </div>
                <div class="invoice-row total-row">
                    <span class="label">Total USD:</span>
                    <span class="value">${{ factura.total_usd|floatformat:2 }}</span>
                </tr>
            </div>
            
            <div class="attachment-note">
                📎 <strong>Adjunto:</strong> Se ha incluido el PDF de la factura ({{ factura.numero_factura }}.pdf) con el detalle completo de los productos, impuestos y totales.
            </div>
            
            <p style="text-align: center; margin-top: 30px;">
                <a href="{{ url_factura }}" class="btn">Ver Factura en Sistema</a>
            </p>
        </div>
        
        <div class="footer">
            <p>Este correo fue enviado automáticamente por el Sistema de Facturación.</p>
            <p>Si no reconoce esta transacción, por favor contacte a soporte.</p>
            <p>&copy; {{ now|date:"Y" }} Sistema de Facturación. Todos los derechos reservados.</p>
        </div>
    </div>
</body>
</html>
```

---

## 5. JavaScript en Frontend (SweetAlert2)

### 5.1 Botón "Enviar por Correo" en `factura_detail.html` y `factura_list.html`

```html
<!-- En factura_detail.html - botón en acciones -->
<a href="#" class="btn btn-outline-primary btn-sm" onclick="enviarFacturaPorEmail('{{ factura.pk }}')"
   title="Enviar por correo">
    <i class="fas fa-envelope"></i>
</a>

<!-- En factura_list.html - columna acciones -->
<a href="#" class="btn btn-sm btn-outline-primary ms-1" onclick="enviarFacturaPorEmail('{{ f.pk }}')" title="Enviar por correo">
    <i class="fas fa-envelope"></i>
</a>

<script>
function enviarFacturaPorEmail(facturaPk) {
    Swal.fire({
        title: 'Enviar factura por correo',
        html: `
            <div class="text-start">
                <div class="mb-3">
                    <label class="form-label">Destinatario *</label>
                    <input type="email" id="email_destinatario" class="form-control" placeholder="cliente@email.com" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Asunto</label>
                    <input type="text" id="email_asunto" class="form-control" value="Factura {{ factura.numero_factura|default:'' }}">
                </div>
                <div class="mb-3">
                    <label class="form-label">Mensaje</label>
                    <textarea id="email_mensaje" class="form-control" rows="3" placeholder="Mensaje personalizado (opcional)..."></textarea>
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: '<i class="fas fa-paper-plane"></i> Enviar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#1e3a5f',
        preConfirm: () => {
            const destinatario = document.getElementById('email_destinatario').value.trim();
            const asunto = document.getElementById('email_asunto').value.trim();
            const mensaje = document.getElementById('email_mensaje').value.trim();
            
            if (!destinatario) {
                Swal.showValidationMessage('El destinatario es obligatorio');
                return false;
            }
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(destinatario)) {
                Swal.showValidationMessage('Email inválido');
                return false;
            }
            return { destinatario, asunto: asunto || `Factura {{ factura.numero_factura|default:'' }}`, mensaje };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            enviarFacturaEmail(facturaPk, result.value);
        }
    });
}

async function enviarFacturaEmail(facturaPk, data) {
    const loadingAlert = Swal.fire({
        title: 'Enviando...',
        text: 'Generando PDF y enviando correo',
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
    });
    
    try {
        const response = await fetch(`/facturacion/facturas/${facturaPk}/email/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        loadingAlert.close();
        
        if (result.success) {
            Swal.fire('¡Enviado!', result.message, 'success');
        } else {
            Swal.fire('Error', result.error || 'Error al enviar', 'error');
        }
    } catch (error) {
        loadingAlert.close();
        Swal.fire('Error', 'Error de conexión: ' + error.message, 'error');
    }
}
</script>
```

---

## 6. Estrategia TDD - Casos de Prueba

### 6.1 Tests en `facturacion/tests/test_email.py`

```python
# facturacion/tests/test_email.py
import json
from decimal import Decimal
from django.core import mail
from django.urls import reverse
from django.test import TestCase, override_settings
from django.contrib.auth.models import Permission

from facturacion.tests.factories import (
    UsuarioFactory, ClienteFactory, ProductoFactory, 
    CabeceraFacturaFactory, DetalleVentaFactory
)
from facturacion.models import CabeceraFactura, TurnoCaja
from facturacion.utils.pdf import generar_pdf_factura

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TestFacturaEmailView(TestCase):
    """Tests para el envío de facturas por email con PDF adjunto."""
    
    def setUp(self):
        # Configurar permisos y usuario cajero
        self.usuario = UsuarioFactory(username='cajero_test')
        from django.contrib.auth.models import Group, Permission
        grupo, _ = Group.objects.get_or_create(name='Cajeros')
        self.usuario.groups.add(grupo)
        
        # Asignar permisos necesarios
        permisos = [
            'add_cabecerafactura', 'view_cabecerafactura',
            'add_cliente', 'view_cliente', 'change_cliente',
            'view_producto', 'view_categoria',
            'add_turnocaja', 'view_turnocaja',
        ]
        for codename in ['add_cabecerafactura', 'view_cabecerafactura', 'view_producto',
                         'add_cliente', 'view_cliente', 'change_cliente',
                         'add_turnocaja', 'change_turnocaja', 'view_turnocaja']:
            perm = Permission.objects.get(content_type__app_label='facturacion', codename=codename)
            self.usuario.user_permissions.add(perm)
        
        # Crear turno abierto
        self.turno = TurnoCaja.objects.create(
            cajero=self.usuario,
            monto_inicial=Decimal('100.00'),
            estatus=TurnoCaja.Estatus.ABIERTA
        )
        
        self.client.force_login(self.usuario)
        
        # Crear datos de prueba
        self.cliente = ClienteFactory(nombre_razon_social='Cliente Test Email')
        self.producto = ProductoFactory(precio_bs=Decimal('100.00'), precio_usd=Decimal('2.00'), stock_actual=50)
        
        # Crear factura de prueba
        self.factura = CabeceraFacturaFactory(
            cliente=self.cliente,
            usuario=self.usuario,
            estatus='pagada',
            total_bs=Decimal('348.00'),
            total_usd=Decimal('6.96'),
        )
        DetalleVentaFactory(
            cabecera=self.factura,
            producto=self.producto,
            cantidad=3,
            precio_unitario_bs=Decimal('100.00'),
        )

    def test_get_report_data_helper_method(self):
        """Verificar método helper _get_report_data retorna estructura correcta."""
        from facturacion.views import ReportSaleView
        view = ReportSaleView()
        data = view._get_report_data_for_current_month()
        
        self.assertIn('data', data)
        self.assertIn('totals', data)
        self.assertIn('subtotal_usd', data['totals'])
        self.assertIn('total_bs', data['totals'])

    def test_generar_pdf_factura_retorna_bytes(self):
        """Verificar que generar_pdf_factura retorna bytes válidos."""
        pdf_bytes = generar_pdf_factura(self.factura)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 0)
        # Verificar que es un PDF válido (header %PDF)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_post_enviar_factura_exitoso(self):
        """POST a /factura/<pk>/email/ envía email con PDF adjunto."""
        url = reverse('facturacion:factura_email', kwargs={'pk': self.factura.pk})
        
        payload = {
            'destinatario': 'cliente@test.com',
            'asunto': 'Su factura',
            'mensaje': 'Adjunto su factura.',
        }
        
        response = self.client.post(
            reverse('facturacion:factura_email', kwargs={'pk': self.factura.pk}),
            data=json.dumps({'destinatario': 'cliente@test.com', 'asunto': 'Test', 'mensaje': 'Hola'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('enviada', data['message'].lower())
        
        # Verificar que se envió el email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['cliente@test.com'])
        self.assertIn('Factura', email.subject)
        
        # Verificar adjunto PDF
        self.assertEqual(len(email.attachments), 1)
        attachment = email.attachments[0]
        self.assertEqual(attachment[0], 'factura_FAC-XXXXXX.pdf')  # nombre esperado
        self.assertEqual(attachment[2], 'application/pdf')
        self.assertTrue(len(attachment[1]) > 0)  # PDF tiene contenido

    def test_post_sin_destinatario_retorna_400(self):
        """POST sin destinatario retorna 400."""
        response = self.client.post(
            reverse('facturacion:factura_email', kwargs={'pk': self.factura.pk}),
            data=json.dumps({'asunto': 'Test', 'mensaje': 'Test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('destinatario', response.json()['error'].lower())

    def test_post_destinatario_invalido_retorna_400(self):
        """POST con email inválido retorna 400."""
        response = self.client.post(
            reverse('facturacion:factura_email', kwargs={'pk': self.factura.pk}),
            data=json.dumps({'destinatario': 'email-invalido', 'asunto': 'Test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_post_factura_inexistente_retorna_404(self):
        """POST a factura inexistente retorna 404."""
        from django.urls import reverse
        import uuid
        response = self.client.post(
            reverse('facturacion:factura_email', kwargs={'pk': '00000000-0000-0000-0000-000000000000'}),
            data=json.dumps({'destinatario': 'test@test.com'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_get_request_retorna_405(self):
        """GET a la vista de email retorna 405 Method Not Allowed."""
        response = self.client.get(reverse('facturacion:factura_email', kwargs={'pk': self.factura.pk}))
        self.assertEqual(response.status_code, 405)

    def test_sin_permiso_retorna_403(self):
        """Usuario sin permiso view_cabecerafactura recibe 403."""
        from django.contrib.auth.models import User
        from django.contrib.auth.models import Group
        
        usuario_sin_permiso = UsuarioFactory(username='sin_permiso')
        grupo, _ = Group.objects.get_or_create(name='Cajeros')
        # NO agregar permisos de facturacion.view_cabecerafactura
        
        self.client.force_login(usuario_sin_permiso)
        response = self.client.post(
            reverse('facturacion:factura_email', kwargs={'pk': self.factura.pk}),
            data=json.dumps({'destinatario': 'test@test.com'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_pdf_adjunto_tiene_contenido_valido(self):
        """Verificar que el PDF adjunto es válido y contiene datos de la factura."""
        from facturacion.utils.pdf import generar_pdf_factura
        
        pdf_bytes = generar_pdf_factura(self.factura)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 1000)  # PDF debe tener contenido sustancial
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
```

---

## 6.2 Tests de Plantilla Email (`test_email_templates.py`)

```python
# facturacion/tests/test_email_templates.py
from django.test import TestCase
from django.template.loader import render_to_string
from facturacion.tests.factories import CabeceraFacturaFactory, ClienteFactory
from decimal import Decimal

class TestFacturaEmailTemplate(TestCase):
    """Tests para la plantilla de email de factura."""
    
    def setUp(self):
        self.factura = CabeceraFacturaFactory(
            numero_factura='FAC-2026001',
            total_bs=Decimal('1000.00'),
            total_usd=Decimal('20.00'),
        )
        self.cliente = self.factura.cliente
    
    def test_template_renderiza_correctamente(self):
        """Verificar que el template se renderiza sin errores."""
        html = render_to_string('emails/factura_email.html', {
            'factura': self.factura,
            'cliente': self.factura.cliente,
            'mensaje_personalizado': 'Mensaje de prueba',
            'url_factura': 'http://testserver/facturacion/facturas/123/',
        })
        
        self.assertIn('FAC-', html)  # Número de factura
        self.assertIn('Cliente Test', html)  # Nombre cliente
        self.assertIn('1.000,00', html)  # Total Bs formateado
        self.assertIn('PDF', html)  # Mención al adjunto
        self.assertIn('window.print()', html)  # Script auto-print
        self.assertIn('fa-print', html)  # Botón imprimir
    
    def test_template_con_mensaje_vacio(self):
        """Template funciona sin mensaje personalizado."""
        html = render_to_string('emails/factura_email.html', {
            'factura': self.factura,
            'cliente': self.factura.cliente,
            'mensaje_personalizado': '',
        })
        self.assertIn('Adjunto encontrará la factura', html)
```

---

## 7. Resumen de Entregables

| Archivo | Descripción |
|---------|-------------|
| `facturacion/views.py` | `FacturaEmailView` (POST `/facturas/<pk>/email/`) |
| `facturacion/utils/pdf.py` | `generar_pdf_factura(factura)` → bytes |
| `facturacion/urls.py` | `path('facturas/<uuid:pk>/email/', ...)` |
| `templates/emails/factura_email.html` | Template HTML responsive del email |
| `facturacion/tests/test_email.py` | Tests de envío, adjuntos, validaciones |
| `facturacion/tests/test_email_templates.py` | Tests de renderizado template |
| `settings.py` | Configuración `EMAIL_BACKEND` por entorno |

---

## 8. Checklist de Verificación Pre-Merge

| Verificación | Comando | Esperado |
|--------------|---------|----------|
| Check Django | `python manage.py check` | 0 issues |
| Tests unitarios | `pytest facturacion/tests/test_email.py -v` | All pass |
| Tests templates | `pytest facturacion/tests/test_email_templates.py -v` | All pass |
| Suite completa | `pytest facturacion/tests/ -q` | 89+ passed |
| Check deploy | `python manage.py check --deploy` | 0 issues |
| Email en outbox | `len(mail.outbox) == 1` | True |
| Adjunto PDF | `len(mail.outbox[0].attachments) == 1` | True |
| PDF válido | `attachment[0][1].startswith(b'%PDF')` | True |

---

## 8. Próximos Pasos

1. **Developer**: Implementar `FacturaEmailView`, `generar_pdf_factura()`, template email
2. **Tester**: Ejecutar `pytest facturacion/tests/test_email.py -v`
3. **Inspector**: Verificar permisos, CSRF, validación de email, adjunto PDF
4. **Merge**: Solo tras 100% tests passing + `manage.py check --deploy`

---

*Documento generado bajo metodología Spec-Driven Development*
*Próximo: Developer implementa según esta especificación*