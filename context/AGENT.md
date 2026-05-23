# AGENT.md — Enrutador de Skills

> **Propósito**: Este archivo NO contiene reglas técnicas. Es solo un enrutador.
> Si la tarea coincide con un trigger, lee la skill correspondiente ANTES de ejecutar.

---

## Enrutamiento

### backend_rules.md
**Trigger**: cualquier tarea que involucre modelos, vistas, URLS, serializers, ORM, migraciones, formularios, admin, o lógica de facturación.
**Leer antes de**: escribir o modificar cualquier archivo `.py` en `facturacion/` o `core/`.

Reglas que contiene: CBVs obligatorios, optimización ORM, IVA 16%, stock estricto, señales de descuento, estructura de proyectos Django 5.

### frontend_rules.md
**Trigger**: cualquier tarea que involucre HTML, CSS, JS, plantillas Django, AJAX, Select2, DataTables, o maquetación de interfaces.
**Leer antes de**: crear o modificar cualquier archivo en `templates/`, `static/`, o archivos `.html`, `.css`, `.js`.

Reglas que contiene: plantillas responsivas con Bootstrap 5, Select2 para búsquedas, DataTables para grillas, AJAX para operaciones sin recarga, estructura de templates.

### security_rules.md
**Trigger**: cualquier tarea que involucre autenticación, autorización, endpoints, AJAX, formularios, o暴露 de datos.
**Leer antes de**: crear o modificar cualquier vista, URL, endpoint AJAX, o template que maneje datos sensibles.

Reglas que contiene: LoginRequiredMixin, @login_required, validación de endpoints, CSRF en AJAX, sanitización de inputs, protección contra inyecciones.

### testing_rules.md
**Trigger**: cualquier tarea que involucre crear, ejecutar, o modificar tests, pruebas unitarias, fixtures, factories, cobertura de código, o verificación de lógica de negocio.
**Leer antes de**: crear o modificar archivos en `facturacion/tests/`, `conftest.py`, `pytest.ini`, o cualquier archivo `test_*.py`.

Reglas que contiene: estructura de tests con pytest, Factory Boy, tests de IVA 16%, moneda dual, stock estricto, descuento máximo, validación RIF, LoginRequiredMixin en vistas, seguridad AJAX, fixtures y configuración.

---

## Flujo de trabajo

1. El usuario pide una tarea.
2. Buscás el trigger que coincida en la tabla de arriba.
3. Leés el/los archivos de skill correspondientes.
4. Ejecutás la tarea cumpliendo las reglas.

Si la tarea cruza múltiples skills (ej: "formulario de facturación con AJAX"), leés **backend_rules.md + frontend_rules.md + security_rules.md** secuencialmente antes de escribir código.

Si la tarea involucra pruebas (ej: "testear factura con stock estricto"), leés **testing_rules.md** además de las skills relevantes al dominio.

---

*Fin del enrutador — este archivo no contiene reglas técnicas.*
