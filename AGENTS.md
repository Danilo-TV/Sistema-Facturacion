# AGENTS.md — Gentle-AI v4 Project Rules & Skill Router (Django POS)

> **Propósito**: Reglas globales del proyecto de facturación y punto de venta.
> Actúa como enrutador de habilidades.

---

### Reglas Globales del Proyecto 

### Core Principles 
- **TDD Estricto**: Test-Driven Development es obligatorio. Escribir tests PRIMERO, luego la implementación. 
- **Django 5.x / Python 3.11+**: Usar únicamente Class-Based Views (CBVs). Prohibidas las Function-Based Views (FBVs). 
- **Zonas Horarias**: Usar exclusivamente el módulo nativo `zoneinfo` (`ZoneInfo('America/Caracas')`). Prohibido `pytz`. 
- **Memoria Persistente**: Consultar `MEMORY.md` para conocer el contexto acumulado entre iteraciones.

### Tech Stack
- **Backend**: Django 5.x, Python 3.11+, Pytest, Factory Boy, WeasyPrint, pytest-django.
- **Database**: SQLite (dev/test), PostgreSQL (prod)
- **Frontend**: Bootstrap 5, Select2, DataTables, jQuery,adminLTE 3, Select2, SweetAlert2.
- **Timezone**: America/Caracas (zoneinfo)
- **Moneda Dual & Impuestos**: Campos dobles para Bolívares (bs) y Dólares (USD). IVA 16% calculando automáticamente. 

### Arquitectura & Seguridad Backend (OWASP Top 10) 
- **Control de Acceso e IDOR (OWASP A01)**: Proteger vistas con `LoginRequiredMixin` y `PermissionRequiredMixin`. En `get_queryset()`, filtrar siempre por la empresa/usuario autenticado. 
- **Prevención de Inyección (OWASP A03)**: Usar exclusivamente la API parametrizada del ORM. Prohibido usar `extra()` o raw SQL con cadenas concatenadas. 
- **Concurrencia en Stock (OWASP A04)**: Usar `transaction.atomic()` y `select_for_update()` en operaciones de caja, ventas y descuento de inventario. 
- **Asignación Masiva (OWASP A05)**: NUNCA usar `fields = '__all__'` en formularios o serializadores. 
- **Respuestas AJAX**: Para peticiones asíncronas no autorizadas, retornar HTTP 403 JSON (`{"success": false, "error": "Forbidden"}`), no redirecciones HTML.

### Code Style
- **Imports**: Group stdlib, third-party, local
- **Type Hints**: Use type hints where practical
- **Docstrings**: Google style for public methods
- **Logging**: Use structlog or stdlib logging

---

## Skill Router 

| Disparador (Trigger) | Skill a Leer | Regla Principal | 
| :--- | :--- | :--- | 
| **Modelos, ORM, CBVs, Vistas, Lógica POS** | `.agents/skills/backend_rules.md` | CBVs, ORM optimizado, `transaction.atomic()`, stock estricto. | 
| **Templates, Bootstrap, JS, DataTables, AJAX** | `.agents/skills/frontend_rules.md` | Bootstrap 5, headers CSRF en AJAX, prohibido `|safe`. | 
| **Autenticación, Permisos, Endpoints, OWASP** |
`.agents/skills/security_rules.md` | IDOR, Anti-SQLi, Mass Assignment, 403 JSON. | 
| **Pruebas, Fixtures, Factory Boy, Cobertura** | `.agents/skills/testing_rules.md` | TDD Primero, Factory Boy, pruebas de concurrencia/permisos. | 
--- 
## Comandos Estándar 
- Servidor: `python manage.py runserver` 
- Tests: `pytest facturacion/tests/ -v` 
- Integridad: `python manage.py check` 
- Despliegue: `python manage.py check --deploy`