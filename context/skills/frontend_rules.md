# Frontend Rules — Interfaz de Facturación

> Reglas obligatorias para toda interfaz del sistema de facturación.
> Stack: **AdminLTE 3 (Bootstrap 4)** + Select2 + DataTables + jQuery + AJAX + FontAwesome.

---

## 1. Template Base

- Todo template hereda de `base.html`.
- `base.html` incluye: AdminLTE 3 CSS/JS, Bootstrap 4, jQuery, Select2 con tema `bootstrap4`, DataTables, FontAwesome.
- Bloques obligatorios: `{% block title %}`, `{% block page_title %}`, `{% block content %}`, `{% block extra_css %}`, `{% block extra_js %}`.
- Estructura AdminLTE3: `body.hold-transition.sidebar-mini` → `.wrapper` → `.main-header.navbar` + `.main-sidebar.sidebar-dark-primary` + `.content-wrapper`.

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Facturación{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/select2-bootstrap4-theme@1.0.0/dist/select2-bootstrap4.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap4.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2.0/dist/css/adminlte.min.css">
    {% block extra_css %}{% endblock %}
</head>
<body class="hold-transition sidebar-mini">
<div class="wrapper">
    {% include 'facturacion/_navbar.html' %}
    {% include 'facturacion/_sidebar.html' %}

    <div class="content-wrapper">
        <section class="content-header">
            <div class="container-fluid">
                <div class="row mb-2">
                    <div class="col-sm-6">
                        <h1 class="m-0">{% block page_title %}Dashboard{% endblock %}</h1>
                    </div>
                </div>
            </div>
        </section>
        <section class="content">
            <div class="container-fluid">
                {% include 'facturacion/_alerts.html' %}
                {% block content %}{% endblock %}
            </div>
        </section>
    </div>

    <footer class="main-footer">
        <strong>Sistema de Facturación</strong>
        <div class="float-right d-none d-sm-block"><b>Versión</b> 1.0</div>
    </footer>
</div>

<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap4.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2.0/dist/js/adminlte.min.js"></script>
<script>
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
    var csrf_token = getCSRFToken();
</script>
{% block extra_js %}{% endblock %}
</body>
</html>
```

---

## 2. Diseño Responsivo

- Usar el sistema de grillas de Bootstrap 4 (`container-fluid`, `row`, `col-*-*`).
- Sidebar colapsable mediante el botón hamburguesa (data-widget="pushmenu").
- Tablas con `table-responsive` wrapper.

---

## 3. Select2 para Búsquedas

Obligatorio en todo campo que sea ForeignKey con más de 10 opciones.
Usar **SIEMPRE** el tema `bootstrap4`.

```html
<select class="form-control select2-search" name="cliente" id="id_cliente">
    <option value="">Buscar cliente…</option>
</select>

<script>
$(document).ready(function() {
    $('.select2-search').select2({
        theme: 'bootstrap4',
        width: '100%',
        placeholder: 'Escriba para buscar…',
        allowClear: true,
        ajax: {
            url: '{% url "facturacion:cliente_search" %}',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return { q: params.term };
            },
            processResults: function(data) {
                return { results: data.items };
            }
        }
    });
});
</script>
```

### Estructura del endpoint JSON

```json
{
    "items": [
        { "id": 1, "text": "Juan Pérez — V-12345678" },
        { "id": 2, "text": "Empresa XYZ — J-98765432" }
    ]
}
```

---

## 4. DataTables para Grillas

Obligatorio en todo listado. Usar `dataTables.bootstrap4.min.css` y `dataTables.bootstrap4.min.js`.

```html
<div class="table-responsive">
    <table class="table table-striped table-hover" id="tabla-productos">
        <thead class="thead-dark">
            <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Precio Bs</th>
                <th>Stock</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            {% for p in productos %}
            <tr>
                <td>{{ p.codigo }}</td>
                <td>{{ p.nombre }}</td>
                <td class="text-right">{{ p.precio_bs|floatformat:2 }}</td>
                <td>{{ p.stock_actual }}</td>
                <td>
                    <a href="{% url 'facturacion:producto_edit' p.pk %}" class="btn btn-sm btn-warning">
                        <i class="fas fa-edit"></i>
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<script>
$(document).ready(function() {
    $('#tabla-productos').DataTable({
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13/i18n/es-ES.json'
        },
        pageLength: 25,
        ordering: true,
        searching: true,
    });
});
</script>
```

---

## 5. AJAX para Guardar Sin Recargar

Obligatorio en formularios de facturación (agregar productos a la factura, calcular totales).

```javascript
function guardarDetalle(url, data) {
    $.ajax({
        url: url,
        method: 'POST',
        data: data,
        headers: { 'X-CSRFToken': csrf_token },
        success: function(response) {
            if (response.success) {
                actualizarTablaDetalles(response.detalles);
                actualizarTotales(response.totales);
                mostrarAlerta('success', 'Producto agregado');
            }
        },
        error: function(xhr) {
            mostrarAlerta('danger', xhr.responseJSON?.error || 'Error al guardar');
        }
    });
}
```

### Reglas AJAX

- **Incluir CSRF token** en toda petición POST.
- **Respuesta siempre JSON** con estructura `{ success: bool, data?: …, error?: string }`.
- **Mostrar feedback visual** con alertas Bootstrap 4 (`.alert`).
- **Nunca recargar la página** en operaciones de creación/edición dentro de la factura.

---

## 6. Maquetación Profesional — AdminLTE3

- Usar **Cards de AdminLTE3** (`.card`) para agrupar secciones del formulario:
  - Una Card para "Datos del Cliente"
  - Una Card para "Productos / Detalles" con DataTables
- Navbar AdminLTE3 con botón hamburguesa para toggle del sidebar.
- Sidebar oscuro (`sidebar-dark-primary`) con menú anidado (treeview).
- Botones con iconos de FontAwesome.
- Colores: usar variables de Bootstrap 4 (`bg-primary`, `bg-success`, etc.), sin colores inline.
- Loading spinner (`<span class="spinner-border spinner-border-sm">`) en toda operación AJAX que tome >500ms.
- Alineación de texto: `text-right` / `text-left` / `text-center` (Bootstrap 4).
- Margen/padding: `mr-*` / `ml-*` / `pr-*` / `pl-*` (Bootstrap 4).

---

## 7. Estructura de Templates

```
templates/
  registration/
    login.html
  facturacion/
    base.html
    _navbar.html
    _sidebar.html
    _alerts.html
    dashboard.html
    producto_list.html
    producto_form.html
    cliente_list.html
    cliente_form.html
    categoria_list.html
    categoria_form.html
    factura_form.html          # formulario principal de facturación
    factura_detail.html        # vista de factura emitida
    factura_list.html          # historial de facturas
```

- Los partials comienzan con `_`: `_navbar.html`, `_sidebar.html`, `_alerts.html`.
- El sidebar contiene la navegación principal; el navbar solo el toggle y menú de usuario.
