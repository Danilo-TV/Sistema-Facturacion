# AGENTS.md — Gentle-AI v4 Project Rules & Skill Router

> **Purpose**: This file contains the global project rules and acts as a skill router.
> If a task matches a trigger, read the corresponding skill BEFORE executing.

---

## Global Project Rules (Gentle-AI v4)

### Core Principles
- **TDD Estricto**: Test-Driven Development is mandatory. Write tests FIRST, then implementation.
- **Django 5.x**: Target framework is Django 5.x with modern practices.
- **zoneinfo para zonas horarias**: Use Python's native `zoneinfo` module (Python 3.9+) instead of `pytz`.
- **Django 5.x Best Practices**: CBVs obligatorias, NO FBVs. Use `LoginRequiredMixin`, proper ORM optimization.
- **Strict TDD**: Write tests FIRST, then implementation. No exceptions.

### Tech Stack
- **Backend**: Django 5.x, Python 3.11+
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Frontend**: Bootstrap 5, Select2, DataTables, jQuery
- **Testing**: pytest, Factory Boy, pytest-django
- **PDF Generation**: WeasyPrint
- **Timezone**: America/Caracas (zoneinfo)

### Architecture Rules
- **CBVs Obligatorias**: Never use Function-Based Views (FBVs)
- **ORM Optimization**: Use `select_related`, `prefetch_related`, `only()`, `defer()`
- **IVA 16%**: Always automatic calculation
- **Moneda Dual**: Both Bs and USD fields in every transaction
- **Stock Estricto**: Validate before adding line items
- **Security**: CSRF + LoginRequiredMixin on all views
- **Timezone**: Use `zoneinfo.ZoneInfo('America/Caracas')` - NO pytz

### Code Style
- **Imports**: Group stdlib, third-party, local
- **Type Hints**: Use type hints where practical
- **Docstrings**: Google style for public methods
- **Logging**: Use structlog or stdlib logging

---

## Skill Router

### backend_rules.md
**Trigger**: Any task involving models, views, URLs, serializers, ORM, migrations, forms, admin, or billing logic.
**Read before**: Writing or modifying any `.py` file in `facturacion/` or `core/`.

Rules: CBVs mandatory, ORM optimization, IVA 16%, strict stock, discount signals, Django 5 project structure.

### frontend_rules.md
**Trigger**: Any task involving HTML, CSS, JS, Django templates, AJAX, Select2, DataTables, or UI layout.
**Read before**: Creating or modifying any file in `templates/`, `static/`, or `.html`, `.css`, `.js` files.

Rules: Responsive Bootstrap 5 templates, Select2 for searches, DataTables for grids, AJAX for no-reload operations, template structure.

### security_rules.md
**Trigger**: Any task involving authentication, authorization, endpoints, AJAX, forms, or data exposure.
**Read before**: Creating or modifying any view, URL, AJAX endpoint, or template handling sensitive data.

Rules: LoginRequiredMixin, @login_required, endpoint validation, CSRF in AJAX, input sanitization, injection protection.

### testing_rules.md
**Trigger**: Any task involving creating, running, or modifying tests, unit tests, fixtures, factories, code coverage, or business logic verification.
**Read before**: Creating or modifying files in `facturacion/tests/`, `conftest.py`, `pytest.ini`, or any `test_*.py`.

Rules: pytest structure, Factory Boy, IVA 16% tests, dual currency tests, strict stock tests, max discount tests, RIF validation, LoginRequiredMixin in views, AJAX security, fixtures and configuration.

---

## Workflow

1. User requests a task.
2. Find matching trigger in the table above.
3. Read the corresponding skill file(s).
4. Execute the task following the rules.

If a task crosses multiple skills (e.g., "billing form with AJAX"), read **backend_rules.md + frontend_rules.md + security_rules.md** sequentially before writing code.

If the task involves testing (e.g., "test invoice with strict stock"), read **testing_rules.md** in addition to relevant domain skills.

---

*End of router — this file contains project rules and routing only.*