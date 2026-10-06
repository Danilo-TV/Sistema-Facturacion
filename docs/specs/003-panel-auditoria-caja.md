# Especificación Técnica — Hito 5: Panel de Control y Auditoría de Cierres de Caja desde el Admin (Supervisión)

## Overview
Implementación de un panel de control y auditoría centralizado para la supervisión de cierres de caja, permitiendo a administradores/supervisores monitorear, filtrar, auditar y exportar información de cierres de caja realizados por los cajeros.

---

## 1. Vistas de Supervisión y Auditoría (`CajaHistorialView` / `CajaAuditoriaDetailView`)

### 1.1 `CajaHistorialView` — Lista de Cierres de Caja (Admin/Supervisor)

| Atributo | Valor |
|----------|-------|
| **Herencia** | `ValidarPermisosMixin` + `LoginRequiredMixin` + `ListView` |
| **Permiso requerido** | `facturacion.view_turnocaja_audit` (custom permission) + `is_staff=True` o rol Admin/Supervisor |
| **Modelo** | `TurnoCaja` (filtrado: `estatus=CERRADA`) |
| **Template** | `facturacion/caja_historial_audit.html` |
| **Paginación** | 25 por página |
| **Ordenamiento** | `-fecha_cierre` (más reciente primero) |

#### Métricas Clave a Mostrar en la Tabla

| Columna | Descripción | Fuente |
|---------|-------------|--------|
| **Fecha Apertura** | `fecha_apertura` (formato dd/mm/YYYY HH:mm) | `TurnoCaja.fecha_apertura` |
| **Fecha Cierre** | `fecha_cierre` (formato dd/mm/YYYY HH:mm) | `TurnoCaja.fecha_cierre` |
| **Cajero** | Nombre completo + username | `TurnoCaja.cajero.get_full_name()` + username |
| **Efectivo Sistema (Bs)** | `monto_efectivo_sistema` | `TurnoCaja.monto_efectivo_sistema` |
| **Tarjeta/Transferencia Sistema** | `monto_tarjeta_sistema` | `TurnoCaja.monto_tarjeta_sistema` |
| **Total Sistema (Bs)** | `monto_efectivo_sistema + monto_tarjeta_sistema` | Calculado |
| **Efectivo Declarado** | `efectivo_declarado` | `TurnoCaja.efectivo_declarado` |
| **Tarjeta Declarada** | `tarjeta_declarada` | `TurnoCaja.tarjeta_declarada` |
| **Total Declarado (Bs)** | `efectivo_declarado + tarjeta_declarada` | Calculado |
| **Diferencia (Bs)** | `Total Declarado - Total Sistema` | `diferencia` |
| **Estado** | Badge: `Cuadrado` / `Faltante` / `Sobrante` | Según `diferencia` |

### 1.2 `CajaAuditoriaDetailView` — Detalle de Cierre (Admin/Supervisor)

| Atributo | Valor |
|----------|-------|
| **Herencia** | `ValidarPermisosMixin` + `LoginRequiredMixin` + `DetailView` |
| **Permiso requerido** | `facturacion.view_turnocaja_audit` |
| **Modelo** | `TurnoCaja` (solo `estatus=CERRADA`) |
| **Template** | `facturacion/caja_auditoria_detail.html` |

#### Secciones en el Detalle

1. **Información General del Turno**
   - Cajero, Fechas (apertura/cierre), Duración del turno
   - Monto inicial de caja

2. **Métricas del Sistema (Calculadas)**
   - Ventas en Efectivo (Bs): Suma `total_bs` de facturas PAGADA en efectivo
   - Ventas en Tarjeta/Transferencia (USD): Suma `total_usd` de facturas PAGADA en tarjeta/transferencia
   - Total Sistema (Bs): Efectivo + (Tarjeta × Tasa Cambio Promedio)

3. **Arqueo del Cajero (Declarado)**
   - Efectivo Declarado (Bs)
   - Tarjeta/Transferencia Declarada (USD)
   - Total Declarado (Bs) = Efectivo + (Tarjeta × Tasa Cambio Promedio)

4. **Diferencias (Descuadres)**
   - Diferencia Efectivo (Bs): Declarado - Sistema
   - Diferencia Tarjeta (USD): Declarado - Sistema
   - **Diferencia Total (Bs)**: Total Declarado - Total Sistema

4. **Listado de Facturas del Turno**
   - Tabla paginada: N° Factura, Cliente, Fecha, Tipo, Efectivo/Tarjeta, Total Bs, Total USD, Estatus

5. **Detalle de Productos Vendidos** (Opcional/Colapsable)
   - Producto, Cantidad, Precio Unitario, Subtotal, IVA, Total

---

## 2. Filtros y Búsqueda Avanzada

### 2.1 Parámetros de Filtro (GET Parameters)

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `fecha_inicio` | date | Fecha desde (inclusive) — filtra por `fecha_apertura` |
| `fecha_fin` | date | Fecha hasta (inclusive) — filtra por `fecha_cierre` |
| `cajero` | uuid | ID del cajero (ForeignKey a Usuario) |
| `estatus` | choice | `ABIERTA`, `CERRADA`, `TODAS` |
| `tipo_descuadre` | choice | `CUADRADO` (diff=0), `FALTANTE` (diff<0), `SOBRANTE` (diff>0), `TODOS` |
| `cajero_username` | string | Búsqueda parcial por username/name |

### 2.2 Implementación en `get_queryset()`

```python
def get_queryset(self):
    queryset = super().get_queryset()
    
    # Filtro por fechas
    fecha_inicio = self.request.GET.get('fecha_inicio')
    fecha_fin = self.request.GET.get('fecha_fin')
    if fecha_inicio:
        queryset = queryset.filter(fecha_apertura__date__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_cierre__date__lte=fecha_fin)
    
    # Filtro por cajero
    cajero_id = self.request.GET.get('cajero')
    if cajero_id:
        queryset = queryset.filter(cajero_id=cajero_id)
    
    # Filtro por estatus
    estatus = self.request.GET.get('estatus')
    if estatus and estatus != 'TODAS':
        queryset = queryset.filter(estatus=estatus)
    
    # Filtro por tipo de descuadre
    tipo_descuadre = self.request.GET.get('tipo_descuadre')
    if tipo_descuadre == 'CUADRADO':
        queryset = queryset.filter(diferencia=Decimal('0'))
    elif tipo_descuadre == 'FALTANTE':
        queryset = queryset.filter(diferencia__lt=Decimal('0'))
    elif tipo_descuadre == 'SOBRANTE':
        queryset = queryset.filter(diferencia__gt=Decimal('0'))
    
    # Búsqueda por cajero (username/nombre)
    q = self.request.GET.get('q')
    if q:
        queryset = queryset.filter(
            Q(cajero__username__icontains=q) | 
            Q(cajero__first_name__icontains=q) | 
            Q(cajero__last_name__icontains=q)
        )
    
    return queryset.order_by('-fecha_cierre')
```

---

## 3. Reportes y Exportación

### 3.1 Opciones de Exportación

| Formato | Descripción | Implementación |
|---------|-------------|----------------|
| **PDF** | Reporte imprimible con tabla completa y métricas | WeasyPrint (reutilizar `ticket_pos_80mm.html` adaptado) |
| **Excel (xlsx)** | Tabla cruda para análisis en Excel | `openpyxl` / `pandas` |
| **CSV** | Datos crudos para importar en otros sistemas | `csv` module nativo |

### 3.2 Endpoints de Exportación

| Endpoint | Método | Parámetros | Descripción |
|----------|--------|------------|-------------|
| `/caja/historial/export/pdf/` | GET | Mismos filtros que lista | PDF imprimible |
| `/caja/historial/export/excel/` | GET | Mismos filtros | XLSX descargable |
| `/caja/historial/export/csv/` | GET | Mismos filtros | CSV descargable |

### 3.3 Estructura del Reporte PDF

```
┌─────────────────────────────────────────────────────────────┐
│  REPORTE DE CIERRES DE CAJA                                 │
│  Período: [fecha_inicio] - [fecha_fin]                      │
│  Generado: [fecha_hora]  Usuario: [usuario]                 │
├─────────────────────────────────────────────────────────────┤
│  RESUMEN EJECUTIVO                                          │
│  ─────────────────────────────────────────────────────────  │
│  Total Turnos Cerrados:           [N]                       │
│  Total Efectivo Sistema (Bs):     [Bs XXXX.XX]              │
│  Total Tarjeta Sistema (USD):     [USD XXXX.XX]             │
│  Total Sistema (Bs):              [Bs XXXX.XX]              │
│  Total Declarado (Bs):            [Bs XXXX.XX]              │
│  Diferencia Total (Bs):           [+/- Bs XXX.XX]           │
│  Turnos Cuadrados:                [N]                       │
│  Turnos con Faltante:             [N]                       │
│  Turnos con Sobrante:             [N]                       │
├─────────────────────────────────────────────────────────────┤
│  DETALLE POR TURNO                                          │
│  ┌──────┬───────────┬────────┬──────────┬────────┬────────┐│
│  │Fecha │ Cajero    │Efectivo│  Tarjeta │ Total  │  Diff  ││
│  │Cierre│           │Sistema │  Sistema │ Sistema│ (Bs)   ││
│  ├──────┼───────────┼────────┼──────────┼────────┼────────┤│
│  │...   │...        │...     │...       │...     │...     ││
│  └──────┴───────────┴────────┴──────────┴────────┴────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Seguridad y Control de Acceso

### 4.1 Permisos Requeridos

| Permiso | Descripción | Asignado a |
|---------|-------------|------------|
| `facturacion.view_turnocaja_audit` | Ver historial y detalles de cierres | Admin, Supervisor |
| `facturacion.export_turnocaja_audit` | Exportar reportes PDF/Excel/CSV | Admin, Supervisor |

### 4.2 Implementación en Vistas

```python
class CajaHistorialAuditView(ValidarPermisosMixin, LoginRequiredMixin, ListView):
    permission_required = ('facturacion.view_turnocaja_audit',)
    
    def dispatch(self, request, *args, **kwargs):
        # Validar que es staff o tiene permiso específico
        if not (request.user.is_staff or request.user.has_perm('facturacion.view_turnocaja_audit')):
            raise PermissionDenied("Acceso denegado: Solo administradores/supervisores")
        return super().dispatch(request, *args, **kwargs)

class CajaAuditoriaDetailView(ValidarPermisosMixin, LoginRequiredMixin, DetailView):
    permission_required = ('facturacion.view_turnocaja_audit',)
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.has_perm('facturacion.view_turnocaja_audit')):
            raise PermissionDenied("Acceso denegado: Solo administradores/supervisores")
        return super().dispatch(request, *args, **kwargs)
```

### 4.3 Bloqueo para Cajeros Estándar

```python
# En mixins.py o decorador personalizado
class SoloAdminSupervisorMixin:
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.has_perm('facturacion.view_turnocaja_audit')):
            messages.error(request, "Acceso denegado: Solo administradores/supervisores")
            return redirect('facturacion:dashboard')
        return super().dispatch(request, *args, **kwargs)
```

### 4.4 Respuesta 403 para Cajeros

- **GET** a URLs de auditoría → **HTTP 403 Forbidden** + mensaje flash
- **AJAX** → JSON `{"error": "Acceso denegado", "redirect": "/dashboard/"}` con status 403

---

## 5. Estrategia TDD — Tests en `facturacion/tests/test_caja_auditoria.py`

### 5.1 Tests de Permisos

```python
@pytest.mark.django_db
class TestCajaAuditoriaPermisos:
    """Tests de control de acceso a vistas de auditoría."""
    
    def test_cajero_sin_permiso_recibe_403_en_historial(self, client, usuario_cajero):
        """Cajero estándar recibe 403 al acceder a /caja/historial/."""
        client.force_login(usuario_cajero)
        response = client.get(reverse('facturacion:caja_historial_audit'))
        assert response.status_code == 403
    
    def test_cajero_sin_permiso_recibe_403_en_detalle(self, client, usuario_cajero, turno_cerrado):
        """Cajero recibe 403 en detalle de cierre."""
        client.force_login(usuario_cajero)
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_cerrado.pk}))
        assert response.status_code == 403
    
    def test_admin_accede_historial_200(self, client, usuario_admin):
        """Admin/Supervisor accede a historial con 200."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'))
        assert response.status_code == 200
    
    def test_admin_accede_detalle_200(self, client, usuario_admin, turno_cerrado):
        """Admin accede a detalle de cierre."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_cerrado.pk}))
        assert response.status_code == 200
    
    def test_ajax_sin_permiso_retorna_403_json(self, client, usuario_cajero):
        """AJAX a exportación retorna 403 JSON."""
        client.force_login(usuario_cajero)
        response = client.get('/facturacion/caja/historial/export/excel/', 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert response.status_code == 403
        assert response.json()['error'] == 'Acceso denegado'
```

### 5.2 Tests de Métricas y Cálculos

```python
@pytest.mark.django_db
class TestCajaAuditoriaMetricas:
    """Verificar cálculos exactos de métricas en auditoría."""
    
    def test_diferencia_cuadrada_cero(self, turno_cuadrado):
        """Turno cuadrado: diferencia = 0."""
        assert turno_cerrado.diferencia == Decimal('0')
    
    def test_faltante_negativo(self, turno_faltante):
        """Faltante: diferencia < 0."""
        assert turno_faltante.diferencia < Decimal('0')
    
    def test_sobrante_positivo(self, turno_sobrante):
        """Sobrante: diferencia > 0."""
        assert turno_sobrante.diferencia > Decimal('0')
    
    def test_totales_sistema_calculo_correcto(self, turno_con_ventas):
        """Total sistema = efectivo_sistema + tarjeta_sistema."""
        turno = turno_con_ventas
        total_sistema = turno.monto_efectivo_sistema + turno.monto_tarjeta_sistema
        assert turno.total_sistema_calculado == total_sistema
    
    def test_diferencia_calculo_correcto(self, turno_con_datos):
        """Diferencia = Total Declarado - Total Sistema."""
        turno = turno_con_datos
        total_declarado = (turno.efectivo_declarado or 0) + (turno.tarjeta_declarada or 0)
        total_sistema = (turno.monto_efectivo_sistema or 0) + (turno.monto_tarjeta_sistema or 0)
        assert turno.diferencia == (total_declarado - total_sistema)
```

### 5.3 Tests de Filtros

```python
@pytest.mark.django_db
class TestCajaAuditoriaFiltros:
    """Tests de filtrado en CajaHistorialAuditView."""
    
    def test_filtro_fecha_inicio(self, client, admin_user, turnos_varios):
        """Filtrar por fecha_inicio funciona."""
        client.force_login(admin_user)
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'fecha_inicio': '2026-01-01'})
        assert response.status_code == 200
        # Verificar que solo retornan turnos >= fecha_inicio
    
    def test_filtro_tipo_descuadre_faltante(self, client, admin_user, turnos_varios):
        """Filtrar solo faltantes."""
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'tipo_descuadre': 'FALTANTE'})
        # Verificar solo turnos con diferencia < 0
    
    def test_filtro_cajero_especifico(self, client, admin_user, turnos_varios, cajero_especifico):
        """Filtrar por cajero específico."""
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'cajero': cajero_especifico.pk})
        # Solo turnos de ese cajero
```

### 5.4 Tests de Exportación

```python
@pytest.mark.django_db
class TestCajaAuditoriaExportacion:
    """Tests de exportación PDF/Excel/CSV."""
    
    def test_export_pdf_retorna_pdf_valido(self, client, admin_user):
        """Export PDF retorna PDF válido."""
        response = client.get(reverse('facturacion:caja_historial_export_pdf'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert response.content.startswith(b'%PDF')
    
    def test_export_excel_retorna_xlsx_valido(self, client, admin_user):
        """Export Excel retorna XLSX válido."""
        response = client.get(reverse('facturacion:caja_historial_export_excel'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    def test_export_csv_retorna_csv_valido(self, client, admin_user):
        """Export CSV retorna CSV válido."""
        response = client.get(reverse('facturacion:caja_historial_export_csv'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
    
    def test_export_respetan_filtros(self, client, admin_user, turnos_varios):
        """Export respeta filtros aplicados."""
        response = client.get(reverse('facturacion:caja_historial_export_pdf'),
                              {'fecha_inicio': '2026-01-01', 'tipo_descuadre': 'FALTANTE'})
        # Verificar que solo incluye turnos filtrados
```

---

## 6. URLs a Implementar

```python
# facturacion/urls.py

# Auditoría de Caja
path('caja/historial/', views.CajaHistorialAuditView.as_view(), name='caja_historial_audit'),
path('caja/historial/<uuid:pk>/', views.CajaAuditoriaDetailView.as_view(), name='caja_auditoria_detail'),

# Exportación
path('caja/historial/export/pdf/', views.CajaHistorialExportPDFView.as_view(), name='caja_historial_export_pdf'),
path('caja/historial/export/excel/', views.CajaHistorialExportExcelView.as_view(), name='caja_historial_export_excel'),
path('caja/historial/export/csv/', views.CajaHistorialExportCSVView.as_view(), name='caja_historial_export_csv'),
```

---

## 7. Modelos Requeridos (Actualizaciones)

### 7.1 Modelo `TurnoCaja` — Campos Adicionales

```python
# En facturacion/models.py (agregar a TurnoCaja existente)

class TurnoCaja(models.Model):
    # ... campos existentes ...
    
    # Permiso personalizado para auditoría
    class Meta:
        permissions = [
            ('view_turnocaja_audit', 'Puede ver auditoría de turnos de caja'),
            ('export_turnocaja_audit', 'Puede exportar reportes de turnos de caja'),
        ]
```

### 7.2 Permisos en Migración

```bash
python manage.py makemigrations facturacion
python manage.py migrate
```

---

## 8. Resumen de Entregables

| Archivo | Descripción |
|---------|-------------|
| `facturacion/views.py` | `CajaHistorialAuditView`, `CajaAuditoriaDetailView`, Export Views |
| `facturacion/urls.py` | Rutas `/caja/historial/`, `/caja/historial/<pk>/`, export endpoints |
| `templates/facturacion/caja_historial_audit.html` | Lista con filtros, tabla métricas, botones export |
| `templates/facturacion/caja_auditoria_detail.html` | Detalle completo con métricas y tabla facturas |
| `templates/emails/caja_audit_report.html` | Template para export PDF (reutilizable) |
| `facturacion/templatetags/` | Tags para formateo Bs/USD, badges estado |
| `facturacion/tests/test_caja_auditoria.py` | Tests completos (permisos, métricas, filtros, export) |
| `facturacion/urls.py` | Rutas nuevas |
| `facturacion/templatetags/` | Filtros de formato moneda, badges estado |

---

## 8. Criterios de Aceptación

| Criterio | Verificación |
|----------|--------------|
| Admin ve historial completo con métricas | ✅ |
| Cajero recibe 403 en URLs de auditoría | ✅ |
| Filtros funcionan (fecha, cajero, descuadre) | ✅ |
| Export PDF/Excel/CSV genera archivos válidos | ✅ |
| Métricas calculadas correctamente (diferencia, totales) | ✅ |
| Tests pasan: `pytest facturacion/tests/test_caja_auditoria.py -v` | ✅ |
| `python manage.py check` → 0 issues | ✅ |
| `pytest facturacion/tests/ -q` → 100% passing | ✅ |

---

## 8. Próximos Pasos

1. **Architect**: Aprobar esta especificación ✅
2. **Developer**: Implementar vistas, templates, URLs, exports
3. **Tester**: Crear `test_caja_auditoria.py` con tests descritos
4. **Inspector**: Validar permisos 403, migraciones, `manage.py check`
5. **Merge a main** tras 100% tests passing

---

*Documento generado bajo metodología Spec-Driven Development*
*Versión 1.0 — Listo para implementación*