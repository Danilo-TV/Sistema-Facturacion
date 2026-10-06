# Documentación Técnica Oficial — Sistema de Facturación POS

**Versión:** 1.0 (MVP)  
**Fecha:** 2026-10-06  
**Estado:** ✅ **COMPLETADO** — 123/123 tests PASSED (100%)

---

## 1. Resumen Ejecutivo y Estado

### Visión General
Sistema de facturación y punto de venta (POS) desarrollado en Django 5.x, diseñado para cumplimiento fiscal venezolano (SENIAT) con IVA 16%, moneda dual (Bolívares/Dólares), control de stock estricto y auditoría completa de cierres de caja.

### Estado del Proyecto
| Métrica | Valor |
|---------|-------|
| **Tests Totales** | 123/123 ✅ PASSED |
| **Cobertura Funcional** | 100% módulos core |
| **Seguridad OWASP** | A01-A10 mitigados |
| **Despliegue** | Listo para producción |
| **Documentación** | Completa |

### Hitos Completados
1. ✅ **Hito 1** — Arquitectura base, modelos, autenticación, permisos
2. ✅ **Hito 2** — POS, facturación AJAX, IVA 16%, moneda dual, stock
3. ✅ **Hito 3** — Tickets 80mm, PDF, email, reportes
4. ✅ **Hito 4** — Caja (apertura/cierre/arqueo)
5. ✅ **Hito 5** — Auditoría de caja (admin/supervisor) + exportaciones
6. ✅ **Hardening** — django-environ, django-axes, logging seguridad

---

## 2. Arquitectura & Stack Tecnológico

### Backend
| Componente | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.11+ | Runtime principal |
| **Django** | 5.2 | Framework web (CBVs obligatorias) |
| **django-environ** | 0.11+ | Gestión de secretos (12-factor) |
| **django-axes** | 8.3+ | Protección fuerza bruta |
| **django-crum** | 0.7+ | Usuario actual en signals |
| **SQLite** | Dev | Base de datos desarrollo |
| **PostgreSQL** | 15+ | Base de datos producción |
| **WeasyPrint** | Latest | Generación PDF |
| **openpyxl** | Latest | Exportación Excel |

### Testing
| Herramienta | Versión | Uso |
|-------------|---------|-----|
| **pytest** | 8.0+ | Test runner |
| **pytest-django** | 4.8+ | Integración Django |
| **factory-boy** | 3.3+ | Factories para tests |
| **Faker** | 40+ | Datos de prueba |

### Frontend
| Librería | Versión | Uso |
|----------|---------|-----|
| **Bootstrap** | 5.3 | UI framework |
| **AdminLTE** | 3.2 | Template admin |
| **DataTables** | 1.13 | Tablas interactivas |
| **Select2** | 4.1 | Selects buscables |
| **SweetAlert2** | 11+ | Alertas modales |
| **jQuery** | 3.7 | DOM/AJAX |
| **moment.js** | 2.29 | Fechas (es-ES) |
| **daterangepicker** | 3.1 | Rangos de fecha |

### Configuración Crítica
```python
# Zona horaria obligatoria
TIME_ZONE = 'America/Caracas'
USE_TZ = True
# zoneinfo (stdlib) — NO pytz
from zoneinfo import ZoneInfo
```

---

## 3. Módulos Funcionales

### 3.1 Punto de Venta (POS) y Facturación

**Endpoints principales:**
| URL | Vista | Descripción |
|-----|-------|-------------|
| `/facturas/nueva/` | `FacturaCreateView` | POS - creación factura AJAX |
| `/api/clientes/search/` | `ClienteSearchAJAXView` | Buscar clientes (Select2) |
| `/api/productos/search/` | `ProductoSearchAJAXView` | Buscar productos con stock |
| `/facturas/<uuid:pk>/` | `FacturaDetailView` | Detalle factura |

**Reglas de Negocio:**
- **IVA 16%** calculado automáticamente en backend
- **Moneda dual**: todos los montos en Bs y USD
- **Tasa de cambio** configurable por factura
- **Stock estricto**: validación antes de agregar línea (señales + `select_for_update`)
- **Descuento máx**: configurable por producto/categoría
- **RIF válido**: validador venezolano (V/J/E/G/P)

**Flujo AJAX Factura:**
```javascript
// 1. Buscar cliente → Select2 → /api/clientes/search/
// 2. Buscar producto → Select2 → /api/productos/search/ (filtra stock>0)
// 3. Agregar línea → POST JSON → valida stock → retorna línea + totales
// 4. Confirmar factura → POST completo → transacción atómica → PDF/ticket
```

### 3.2 Caja y Auditoría

**Endpoints:**
| URL | Vista | Permiso | Descripción |
|-----|-------|---------|-------------|
| `/caja/apertura/` | `AperturaCajaView` | Cajero | Abrir turno con fondo inicial |
| `/caja/cierre/` | `CierreCajaView` | Cajero | Cerrar turno con arqueo |
| `/caja/historial/` | `HistorialCierresView` | Cajero | Ver propios cierres |
| `/caja/historial/auditoria/` | `CajaHistorialAuditView` | Admin/Supervisor | Panel auditoría global |
| `/caja/historial/auditoria/<pk>/` | `CajaAuditoriaDetailView` | Admin/Supervisor | Detalle turno |
| `/caja/historial/export/pdf/` | `CajaHistorialExportPDFView` | Export permission | Export PDF |
| `/caja/historial/export/excel/` | `CajaHistorialExportExcelView` | Export permission | Export Excel |
| `/caja/historial/export/csv/` | `CajaHistorialExportCSVView` | Export permission | Export CSV |

**Permisos Custom (TurnoCaja):**
```python
permissions = [
    ('view_turnocaja_audit', 'Puede ver auditoría de turnos de caja'),
    ('export_turnocaja_audit', 'Puede exportar reportes de turnos de caja'),
]
```

**Métricas de Auditoría:**
- Totales sistema (efectivo Bs / tarjeta USD)
- Totales declarados por cajero
- Diferencia (sobrante/faltante/cuadrado)
- Filtros: fecha, cajero, tipo descuadre, búsqueda texto
- Exportaciones respetan filtros activos

### 3.3 Emisión de Documentos

**Tipos de Salida:**
| Formato | Vista | Uso |
|---------|-------|-----|
| **Ticket 80mm** | `FacturaTicketView` | Impresora térmica POS |
| **Factura PDF** | `FacturaPdfView` | Legal/archivo (WeasyPrint) |
| **Email** | `FacturaEmailView` | Envío automático cliente |

**Características PDF:**
- CSS inlined para WeasyPrint (sin dependencias externas)
- Layout profesional: header, cliente, tabla productos, totales Bs/USD, observaciones
- Badge de estatus (Pagada/Anulada/Crédito)
- Generado on-demand, no almacenado

---

## 4. Arquitectura Agéntica Gentle-AI v4

### Estructura de Configuración
```
.opencode/
├── agents/              # Sub-agentes especializados
│   ├── architect.md     # Arquitectura, decisiones técnicas
│   ├── developer.md     # Implementación, código
│   ├── inspector.md     # Code review, seguridad
│   └── planner.md       # Planificación, tareas
├── skills/              # Skills reutilizables
│   ├── backend_rules.md      # Django, CBVs, ORM, seguridad
│   ├── frontend_rules.md     # Bootstrap, AJAX, templates
│   ├── security_rules.md     # OWASP, permisos, CSRF
│   ├── testing_rules.md      # TDD, pytest, factories
│   └── _shared/skill-resolver.md  # Resolución de skills
├── agent-routing.md    # Routing ODD workflow
└── AGENTS.md           # Router principal del proyecto
```

### Flujo de Trabajo ODD (Organic Driven Development)

```
User Request → Authorize → Explore → Resolve Uncertainty
    → Classify → Track (odd/tasks/) → Implement Task-by-Task
    → Verify → Close
```

**Principios Clave:**
- **TDD Estricto**: Tests ANTES que implementación
- **CBVs Obligatorias**: Sin FBVs
- **Delegación Inteligente**: Sub-agentes para trabajo pesado
- **Memoria Persistente**: Engram para contexto cross-session

### Skills Disponibles
| Skill | Trigger | Ubicación |
|-------|---------|-----------|
| `backend_rules` | Modelos, vistas, ORM, CBVs | `.agents/skills/backend_rules.md` |
| `frontend_rules` | Templates, AJAX, JS, CSS | `.agents/skills/frontend_rules.md` |
| `security_rules` | Auth, permisos, OWASP | `.agents/skills/security_rules.md` |
| `testing_rules` | Tests, factories, fixtures | `.agents/skills/testing_rules.md` |

---

## 5. Hardening de Seguridad OWASP Top 10

### A01:2021 — Broken Access Control
**Mitigado:**
- `ValidarPermisosMixin` en **TODAS** las CBVs (32 vistas)
- `LoginRequiredMixin` + `permission_required` granulares
- `get_queryset()` filtra por usuario/empresa
- AJAX no autorizado → **HTTP 403 JSON** (`{"error": "Acceso denegado"}`), NO redirect

```python
# facturacion/mixins.py
class ValidarPermisosMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.permission_required and not request.user.has_perms(self.permission_required):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Acceso denegado'}, status=403)
            return HttpResponseForbidden('No tiene permiso para acceder a este módulo')
        return super().dispatch(request, *args, **kwargs)
```

### A02:2021 — Cryptographic Failures
**Mitigado:**
- `SECRET_KEY` fuera de código (`.env` via `django-environ`)
- `DEBUG=False` en producción
- HTTPS obligatorio (`SECURE_SSL_REDIRECT=True`)
- Cookies seguras (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`)
- HSTS: 1 año (`SECURE_HSTS_SECONDS=31536000`)

### A03:2021 — Injection
**Mitigado:**
- **ORM exclusivamente** — sin `extra()`, sin raw SQL
- Parámetros parametrizados en todos los queries
- Validación de entrada en forms/serializers

### A04:2021 — Insecure Design
**Mitigado:**
- `transaction.atomic()` + `select_for_update()` en operaciones críticas
- Stock validado antes de decrementar
- Transacciones atómicas en cierre de caja / creación factura

### A05:2021 — Security Misconfiguration
**Mitigado:**
- **Ningún `fields = '__all__'`** en forms/serializers
- Headers de seguridad completos (X-Frame-Options, XSS Filter, Content-Type Nosniff)
- `ALLOWED_HOSTS` restringido en producción
- `.env` en `.gitignore`, solo `.env.example` versionado

### A06:2021 — Vulnerable Components
**Mitigado:**
- Dependencias actualizadas (Django 5.2, pytest 8, etc.)
- `requirements.txt` versionado
- Sin dependencias conocidas vulnerables

### A07:2021 — Identification & Authentication Failures
**Mitigado:**
- **django-axes** instalado y configurado
- `AXES_FAILURE_LIMIT=5` → bloqueo en 5to intento fallido
- `AXES_COOLOFF_TIME=1` → 1 hora de bloqueo
- `AXES_LOCKOUT_PARAMETERS=['username', 'ip_address']`
- **HTTP 429** (Too Many Requests) en rate limit
- Template `lockout.html` personalizado
- Logging de intentos en `logs/security.log`

### A08:2021 — Software & Data Integrity Failures
**Mitigado:**
- `django-environ` para configuración inmutable
- CI/CD verifica tests antes de merge
- Migraciones versionadas

### A09:2021 — Security Logging & Monitoring Failures
**Mitigado:**
```python
LOGGING = {
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'security',
        },
    },
    'loggers': {
        'axes': {'handlers': ['security_file'], 'level': 'WARNING'},
        'django.security': {'handlers': ['security_file'], 'level': 'WARNING'},
        'django.request': {'handlers': ['security_file'], 'level': 'WARNING'},
    },
}
```
Eventos registrados: intentos fallidos, bloqueos, accesos denegados, errores 4xx/5xx

### A10:2021 — Server-Side Request Forgery
**Mitigado:**
- Sin endpoints que hagan requests externos
- Validación estricta de URLs en email/redirects

---

## 6. Guía de Ejecución y Despliegue

### 6.1 Desarrollo Local

```bash
# Clonar repositorio
git clone https://github.com/Danilo-TV/Sistema-Facturacion.git
cd Sistema-Facturacion

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con valores locales

# Migraciones y superusuario
python manage.py migrate
python manage.py createsuperuser

# Cargar permisos de cajeros (opcional)
python manage.py setup_cajeros

# Levantar servidor
python manage.py runserver
# Acceder: http://127.0.0.1:8000/
```

### 6.2 Ejecución de Tests

```bash
# Suite completa (123 tests)
pytest facturacion/tests/ -v

# Módulo específico
pytest facturacion/tests/test_caja_auditoria.py -v
pytest facturacion/tests/test_permissions.py -v
pytest facturacion/tests/test_models.py -v
pytest facturacion/tests/test_views.py -v

# Con coverage
pytest --cov=facturacion --cov-report=html
```

### 6.2 Verificaciones Pre-Despliegue

```bash
# Checks Django
python manage.py check
python manage.py check --deploy

# Static files
python manage.py collectstatic --noinput

# Migraciones
python manage.py migrate --plan
python manage.py migrate
```

### 6.3 Despliegue a Producción (VPS/Cloud)

```bash
# 1. Preparar servidor
sudo apt update && sudo apt install -y python3.11 python3.11-venv postgresql nginx certbot

# 2. Configurar PostgreSQL
sudo -u postgres psql
CREATE DATABASE facturacion_db;
CREATE USER facturacion_user WITH PASSWORD 'password_seguro';
GRANT ALL PRIVILEGES ON DATABASE facturacion_db TO facturacion_user;
\q

# 3. Clonar y configurar proyecto
git clone https://github.com/Danilo-TV/Sistema-Facturacion.git /opt/facturacion
cd /opt/facturacion
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar .env de PRODUCCIÓN
cp .env.production.example .env
# EDITAR .env con valores reales:
# - SECRET_KEY (generar nueva: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# - DEBUG=False
# - ALLOWED_HOSTS=midominio.com,www.midominio.com
# - DATABASE_URL=postgres://facturacion_user:password@localhost:5432/facturacion_db
# - EMAIL_HOST_USER / EMAIL_HOST_PASSWORD (app password SMTP)
# - SECURE_SSL_REDIRECT=True, etc.

# 5. Migraciones y static files
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# 6. Configurar Nginx + Gunicorn + systemd
# (Ver configuración ejemplo en docs/NGINX_GUNICORN.md)

# 7. SSL con Let's Encrypt
sudo certbot --nginx -d midominio.com -d www.midominio.com

# 8. Verificar
python manage.py check --deploy
```

### 6.4 Checklist Producción (`.env.production.example`)

```
[ ] SECRET_KEY generada única (50+ chars)
[ ] DEBUG=False
[ ] ALLOWED_HOSTS con dominio real
[ ] PostgreSQL configurado y accesible
[ ] DATABASE_URL apunta a PostgreSQL
[ ] Certificado SSL/TLS válido
[ ] SECURE_SSL_REDIRECT=True (tras probar HTTPS)
[ ] HSTS activado (31536000s)
[ ] Email SMTP con app password
[ ] collectstatic ejecutado
[ ] migrate ejecutado
[ ] Superusuario creado
[ ] Permisos media/static correctos
[ ] Firewall: puertos 80, 443, 22
[ ] Backups BD automáticos
[ ] Monitoreo/logs configurados
```

---

## Apéndice: Comandos Útiles

```bash
# Ver migraciones pendientes
python manage.py showmigrations

# Crear migración
python manage.py makemigrations facturacion

# Shell Django
python manage.py shell

# Limpiar sesiones expiradas
python manage.py clearsessions

# Resetear intentos fallidos django-axes
python manage.py axes_reset

# Ver logs seguridad
tail -f logs/security.log

# Backup BD (SQLite dev)
cp db.sqlite3 backups/db_$(date +%Y%m%d).sqlite3

# Backup BD (PostgreSQL prod)
pg_dump -U facturacion_user facturacion_db > backups/facturacion_$(date +%Y%m%d).sql
```

---

**Fin de la Documentación Técnica Oficial**  
*Sistema de Facturación POS — Gentle-AI v4 — MVP Completado*