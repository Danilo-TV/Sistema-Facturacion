# Security Rules — Sistema de Facturación

> Reglas obligatorias de seguridad para todas las capas del sistema.

---

## 1. Autenticación y Autorización

### 1.1. LoginRequiredMixin — OBLIGATORIO

Toda vista que no sea login/register debe incluir `LoginRequiredMixin` como **primer padre**.

```python
from django.contrib.auth.mixins import LoginRequiredMixin

class FacturaListView(LoginRequiredMixin, ListView):
    model = CabeceraFactura
    # ...
```

- `LoginRequiredMixin` redirige automáticamente al login si el usuario no está autenticado.
- Configurar `LOGIN_URL` en settings.py.
- **Excepción**: solo `LoginView` y `PasswordResetView` no lo llevan.

### 1.2. @login_required para vistas función

Si por alguna razón excepcional se usa una vista función (no recomendado, ver backend_rules.md):

```python
from django.contrib.auth.decorators import login_required

@login_required
def mi_vista(request):
    ...
```

### 1.3. Verificación por Roles

Cuando un endpoint requiera un rol específico (admin, contador), usar `UserPassesTestMixin`:

```python
from django.contrib.auth.mixins import UserPassesTestMixin

class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    def test_func(self):
        return self.request.user.rol in ['admin', 'contador']
```

- `test_func()` debe ser explícita y legible.
- No confiar solo en `is_staff` o `is_superuser`.

---

## 2. Validación de Endpoints

### 2.1. IDs con UUID

- Todos los modelos usan UUID como PK. Las URLs deben aceptar UUIDs.
- Usar `uuid` path converter de Django:

```python
from django.urls import path

path('producto/<uuid:pk>/editar/', ProductoUpdateView.as_view(), name='producto_edit')
```

### 2.2. Protección contra manipulación de IDs

- Nunca confiar en que el usuario autenticado tiene permiso sobre un recurso solo porque conoce su UUID.
- Verificar propiedad en cada endpoint:

```python
class FacturaUpdateView(LoginRequiredMixin, UpdateView):
    def get_queryset(self):
        return CabeceraFactura.objects.filter(usuario=self.request.user)
```

---

## 3. CSRF y AJAX

### 3.1. CSRF Token en AJAX

Toda petición AJAX con método POST/PUT/DELETE debe incluir el token CSRF.

```javascript
// OPCIÓN 1 — Obtener del cookie (recomendada)
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const c = cookie.trim();
        if (c.startsWith(name + '=')) {
            return decodeURIComponent(c.substring(name.length + 1));
        }
    }
    return '';
}

$.ajax({
    url: '/api/guardar-detalle/',
    method: 'POST',
    data: formData,
    headers: { 'X-CSRFToken': getCSRFToken() },
    success: function(response) { ... }
});
```

- **Nunca** deshabilitar CSRF con `@csrf_exempt` en vistas de producción.
- **Nunca** enviar CSRF token por GET.

### 3.2. Sanitización de Inputs AJAX

```python
from django.views import View
from django.http import JsonResponse
from django.core.exceptions import ValidationError

class DetalleCreateAJAXView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        producto_id = request.POST.get('producto_id')
        cantidad = request.POST.get('cantidad')

        # Validar tipos
        try:
            cantidad = int(cantidad)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Cantidad inválida.'}, status=400)

        if cantidad <= 0:
            return JsonResponse({'success': False, 'error': 'La cantidad debe ser mayor a cero.'}, status=400)

        # Validar existencia del producto
        try:
            producto = Producto.objects.get(pk=producto_id, is_active=True)
        except Producto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Producto no encontrado.'}, status=404)

        # Validar stock
        if not producto.permite_stock_negativo and cantidad > producto.stock_actual:
            return JsonResponse({
                'success': False,
                'error': f'Stock insuficiente. Disponible: {producto.stock_actual}'
            }, status=400)

        # Procesar…
        return JsonResponse({'success': True, 'data': ...})
```

---

## 4. Protección contra Inyecciones

### 4.1. ORM — Nunca SQL crudo

```python
# MAL — inyección SQL
Producto.objects.raw(f"SELECT * FROM facturacion_producto WHERE codigo = '{request.GET.get('q')}'")

# BIEN — parámetros seguros
Producto.objects.filter(codigo=request.GET.get('q'))
```

### 4.2. Django Templates — Escape automático

Django escapa por defecto con `{{ variable }}`. **No usar `safe` ni `autoescape off`** a menos que sea estrictamente necesario y el contenido esté sanitizado.

```html
<!-- MAL — si variable contiene HTML malicioso -->
{{ variable|safe }}

<!-- BIEN — escape automático -->
{{ variable }}
```

### 4.3. JSON puro en AJAX

```python
# MAL
from django.http import HttpResponse
return HttpResponse(str(data))

# BIEN
from django.http import JsonResponse
return JsonResponse(data)
```

---

## 5. Configuración en settings.py

```python
# Seguridad
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

SESSION_COOKIE_AGE = 28800      # 8 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True     # Django 5 permite esto

# En producción (no desarrollo):
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

---

## 6. Buenas Prácticas Generales

| Regla | Descripción |
|---|---|
| DEBUG=False en producción | Nunca dejar DEBUG=True en producción |
| SECRET_KEY en .env | Usar `python-decouple` o `django-environ` |
| CORS | Si hay frontend separado, usar `django-cors-headers` |
| Rate limiting | Usar `django-ratelimit` en endpoints AJAX |
| Logging | Registrar intentos de acceso no autorizados |
