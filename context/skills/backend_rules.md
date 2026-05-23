# Backend Rules — Django 5

> Reglas obligatorias para todo el código backend del sistema de facturación.

---

## 1. Vistas Basadas en Clases (CBVs)

**Obligatorio.** Prohibido usar funciones (`def view(request)`) como vistas.

| Propósito | CBV a usar |
|---|---|
| Listar | `ListView` |
| Crear | `CreateView` |
| Editar | `UpdateView` |
| Eliminar | `DeleteView` |
| Detalle | `DetailView` |
| Formulario sin modelo | `FormView` |
| AJAX / API | `View` con métodos |

### Ejemplo estructura

```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'facturacion/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 25
```

- Usar `LoginRequiredMixin` como primer padre SIEMPRE (ver security_rules.md).
- `context_object_name` explícito, no confiar en el automático.
- `paginate_by` en todo listado con más de 10 registros.

---

## 2. Optimización ORM

### 2.1. select_related y prefetch_related

Obligatorio en toda vista que renderice relaciones ForeignKey o ManyToMany.

```python
# MAL — N+1 queries
Producto.objects.all()

# BIEN — eager loading
Producto.objects.select_related('categoria').all()
CabeceraFactura.objects.select_related('cliente', 'usuario').prefetch_related('detalles__producto').all()
```

### 2.2. only() y defer()

Usar `only()` cuando solo se necesiten campos específicos.

```python
Producto.objects.only('id', 'nombre', 'precio_bs', 'stock_actual')
```

### 2.3. Contar con count()

```python
# MAL
len(Producto.objects.all())

# BIEN
Producto.objects.count()
```

### 2.4. exists()

```python
# MAL
if Producto.objects.filter(...):

# BIEN
if Producto.objects.filter(...).exists():
```

---

## 3. Modelos — Reglas de Facturación

### 3.1. IVA 16%

```python
class DetalleVenta(models.Model):
    IVA = Decimal('0.16')

    def save(self, *args, **kwargs):
        self.subtotal_bs = self.cantidad * self.precio_unitario_bs
        self.subtotal_usd = self.cantidad * self.precio_unitario_usd
        self.monto_iva_bs = (self.subtotal_bs * self.IVA).quantize(Decimal('0.01'))
        self.monto_iva_usd = (self.subtotal_usd * self.IVA).quantize(Decimal('0.01'))
        self.total_bs = self.subtotal_bs + self.monto_iva_bs
        self.total_usd = self.subtotal_usd + self.monto_iva_usd
        super().save(*args, **kwargs)
```

- Redondear con `quantize(Decimal('0.01'))` — **nunca** `round()` de Python.

### 3.2. Stock Estricto

- El stock se descuenta SOLO al confirmar la factura (estatus `pagada`), no al crearla como borrador.
- En `Producto.clean()`: si `permite_stock_negativo=False` y `stock_actual < 0`, lanzar `ValidationError`.

### 3.3. Moneda Dual

- Todo monto se almacena en `_bs` y `_usd`.
- `_usd` = `_bs / tasa_cambio`.
- `tasa_cambio` se guarda en la factura (histórico), no se consulta de una tabla externa.

### 3.4. Descuentos

- Máximo descuento permitido: 20% del subtotal.
- Validar en `CabeceraFactura.clean()`.

```python
def clean(self):
    if self.descuento_bs > self.subtotal_bs * Decimal('0.20'):
        raise ValidationError('El descuento no puede superar el 20% del subtotal.')
```

---

## 4. Formularios

- Usar `ModelForm` siempre que sea posible.
- Validaciones extra en `clean()` del formulario, no en la vista.
- CSRF token obligatorio en todo `<form>` (Django lo incluye por defecto con `{% csrf_token %}`).

---

## 5. URLs

- Namespace obligatorio: `app_name = 'facturacion'`.
- Nombres descriptivos: `path('productos/', ProductoListView.as_view(), name='producto_list')`.

---

## 6. Estructura de Archivos

```
templates/
  facturacion/
    base.html                  # template base con blocks
    producto_list.html
    producto_form.html
    cliente_list.html
    cliente_form.html
    factura_form.html
    factura_detail.html
    ...
```

---

## 7. Pruebas (cuando se agreguen)

- Tests en `facturacion/tests/` (paquete, no módulo).
- Factory Boy para datos de prueba.
- Al menos un test por modelo: creación, validación, string representation.
