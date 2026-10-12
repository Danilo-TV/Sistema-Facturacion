# Plan de Despliegue a Producción — Sistema de Facturación POS

**Versión:** 1.0  
**Fecha:** 2026-10-06  
**Estado:** Planificación — Sin cambios de código

---

## 1. Resumen de Infraestructura Requerida

| Componente | Especificación Mínima | Recomendado |
|------------|----------------------|-------------|
| **CPU** | 2 vCPU | 4 vCPU |
| **RAM** | 4 GB | 8 GB |
| **Disco** | 50 GB SSD | 100 GB SSD |
| **SO** | Ubuntu 22.04 LTS / 24.04 LTS | Ubuntu 24.04 LTS |
| **Python** | 3.11+ | 3.12 |
| **PostgreSQL** | 15+ | 16 |
| **Nginx** | 1.24+ | Latest stable |
| **Certbot** | Latest | Latest |

---

## 2. Arquitectura de Despliegue

```
Internet (HTTPS 443)
    │
    ▼
┌─────────────────────────────────────┐
│         Nginx (Reverse Proxy)       │
│  - SSL/TLS Termination (Let's Encrypt)│
│  - Static files serving             │
│  - Rate limiting básico             │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│      Gunicorn (WSGI Server)         │
│  - Workers: 3-4 (sync)              │
│  - Timeout: 120s                    │
│  - Bind: unix:/run/gunicorn.sock    │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│      Django Application             │
│  - DEBUG=False                      │
│  - SECRET_KEY segura                │
│  - ALLOWED_HOSTS configurado        │
└─────────────────────────────────────┘
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
PostgreSQL        Redis (opcional)    Logs/Archivos
- facturacion_db  - Cache sessions    - /var/log/facturacion/
- Usuario:        - Celery broker     - /opt/facturacion/media/
  facturacion_user                    - /opt/facturacion/static/
```

---

## 3. Checklist Pre-Despliegue (Servidor)

### 3.1 Sistema Base
- [ ] Ubuntu 22.04/24.04 LTS instalado y actualizado
- [ ] Usuario deploy creado con sudo: `adduser deploy && usermod -aG sudo deploy`
- [ ] SSH hardening: desactivar root login, solo keys, puerto no estándar
- [ ] Firewall UFW: `ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw enable`
- [ ] Fail2ban instalado para SSH y Nginx
- [ ] Zona horaria: `timedatectl set-timezone America/Caracas`

### 3.2 PostgreSQL 16
- [ ] Instalado: `apt install postgresql-16 postgresql-contrib`
- [ ] Configurado `postgresql.conf`: `listen_addresses = 'localhost'`
- [ ] Base de datos y usuario creados:
```sql
CREATE DATABASE facturacion_db;
CREATE USER facturacion_user WITH PASSWORD 'PASSWORD_SEGURO_GENERADO';
ALTER ROLE facturacion_user SET client_encoding TO 'utf8';
ALTER ROLE facturacion_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE facturacion_user SET timezone TO 'America/Caracas';
GRANT ALL PRIVILEGES ON DATABASE facturacion_db TO facturacion_user;
```
- [ ] `pg_hba.conf`: autenticación md5 para usuario local
- [ ] Backup automático configurado (pg_dump + cron)

### 3.3 Redis (Opcional — para cache/sessions/Celery)
- [ ] `apt install redis-server`
- [ ] Configurado `bind 127.0.0.1` + password en `redis.conf`
- [ ] systemd habilitado

---

## 4. Despliegue de la Aplicación

### 4.1 Estructura de Directorios
```
/opt/facturacion/
├── venv/                 # Virtual environment
├── logs/                 # Logs de aplicación (security.log, django.log)
├── media/                # Archivos subidos (MEDIA_ROOT)
├── staticfiles/          # Collectstatic (STATIC_ROOT)
├── backups/              # Backups manuales/automáticos
├── .env                  # Variables de producción (NO en git)
└── repo/                 # Código clonado desde GitHub
    ├── facturacion/
    ├── core/
    ├── templates/
    ├── manage.py
    └── requirements.txt
```

### 4.2 Pasos de Despliegue

```bash
# 1. Como usuario deploy
cd /opt/facturacion

# 2. Clonar repositorio
git clone https://github.com/Danilo-TV/Sistema-Facturacion.git repo
cd repo

# 3. Virtual environment
python3 -m venv ../venv
source ../venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# 4. Configurar .env de PRODUCCIÓN
cp .env.production.example ../.env
# EDITAR ../.env con valores reales (ver sección 5)

# 5. Migraciones y static files
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # Solo primera vez

# 6. Verificar
python manage.py check --deploy
```

---

## 5. Variables de Entorno Críticas (`.env`)

> **Copiar de `.env.production.example` y completar TODOS los valores:**

```bash
# Django Core
SECRET_KEY=django-insecure-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # 50+ chars aleatorios
DEBUG=False
ALLOWED_HOSTS=midominio.com,www.midominio.com

# Database (PostgreSQL)
DATABASE_URL=postgres://facturacion_user:PASSWORD_SEGURO@localhost:5432/facturacion_db

# Security Headers
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# django-axes
AXES_FAILURE_LIMIT=5
AXES_COOLOFF_TIME=1
AXES_LOCK_OUT_AT_FAILURE=True
AXES_RESET_ON_SUCCESS=True

# Email SMTP (usar App Password, NO password principal)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=facturacion@midominio.com
EMAIL_HOST_PASSWORD=APP_PASSWORD_GMAIL
DEFAULT_FROM_EMAIL=Sistema Facturación <noreply@midominio.com>

# CSRF Trusted Origins (requerido para Django 5.x con HTTPS)
CSRF_TRUSTED_ORIGINS=https://midominio.com,https://www.midominio.com
```

### Generar SECRET_KEY segura:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 6. Configuración Nginx

### 6.1 `/etc/nginx/sites-available/facturacion`
```nginx
upstream facturacion_app {
    server unix:/run/gunicorn.sock fail_timeout=0;
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;

server {
    listen 80;
    server_name midominio.com www.midominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name midominio.com www.midominio.com;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/midominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/midominio.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Static files
    location /static/ {
        alias /opt/facturacion/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/facturacion/media/;
        expires 30d;
    }

    # Login rate limiting
    location /login/ {
        limit_req zone=login_limit burst=3 nodelay;
        limit_req_status 429;
        proxy_pass http://facturacion_app;
        include proxy_params;
    }

    # API rate limiting
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        limit_req_status 429;
        proxy_pass http://facturacion_app;
        include proxy_params;
    }

    # Main app
    location / {
        proxy_pass http://facturacion_app;
        include proxy_params;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Logs
    access_log /var/log/nginx/facturacion_access.log;
    error_log /var/log/nginx/facturacion_error.log warn;
}
```

### 6.2 `/etc/nginx/proxy_params`
```nginx
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_redirect off;
proxy_buffering off;
```

### 6.3 Habilitar sitio
```bash
ln -s /etc/nginx/sites-available/facturacion /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## 7. Configuración Gunicorn (systemd)

### 7.1 `/etc/systemd/system/gunicorn.service`
```ini
[Unit]
Description=Gunicorn daemon for Facturacion POS
After=network.target postgresql.service

[Service]
User=deploy
Group=www-data
WorkingDirectory=/opt/facturacion/repo
Environment="PATH=/opt/facturacion/venv/bin"
EnvironmentFile=/opt/facturacion/.env
ExecStart=/opt/facturacion/venv/bin/gunicorn \
    --workers 3 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 120 \
    --keep-alive 5 \
    --bind unix:/run/gunicorn.sock \
    --access-logfile /opt/facturacion/logs/gunicorn_access.log \
    --error-logfile /opt/facturacion/logs/gunicorn_error.log \
    --log-level info \
    core.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 7.2 Socket systemd `/etc/systemd/system/gunicorn.socket`
```ini
[Unit]
Description=Gunicorn socket for Facturacion POS

[Socket]
ListenStream=/run/gunicorn.sock
SocketUser=deploy
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
```

### 7.3 Habilitar e iniciar
```bash
mkdir -p /run/gunicorn
chown deploy:www-data /run/gunicorn
chmod 770 /run/gunicorn

systemctl daemon-reload
systemctl enable --now gunicorn.socket
systemctl enable --now gunicorn.service
systemctl status gunicorn.service
```

---

## 8. SSL con Let's Encrypt

```bash
# Instalar certbot
apt install certbot python3-certbot-nginx

# Obtener certificado (requiere DNS apuntando al servidor)
certbot --nginx -d midominio.com -d www.midominio.com \
  --email admin@midominio.com \
  --agree-tos --non-interactive --redirect

# Verificar renovación automática
certbot renew --dry-run
systemctl enable certbot.timer
```

---

## 9. Logs y Monitoreo

### 9.1 Logrotate `/etc/logrotate.d/facturacion`
```bash
/opt/facturacion/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 deploy www-data
    sharedscripts
    postrotate
        systemctl reload gunicorn > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/facturacion_*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
```

### 9.2 Monitoreo Básico (Opcional)
- **Prometheus + Grafana**: Exportar métricas Django
- **Sentry**: Error tracking (dsn en .env)
- **Uptime**: UptimeRobot / Pingdom para health check `/health/`
- **Alertas**: `logs/security.log` → fail2ban / logwatch / SIEM

---

## 10. Backups Automatizados

### 10.1 Script Backup BD `/opt/facturacion/scripts/backup_db.sh`
```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/facturacion/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="facturacion_db"
DB_USER="facturacion_user"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$BACKUP_DIR/db_${DATE}.sql.gz"

# Backup media files
tar -czf "$BACKUP_DIR/media_${DATE}.tar.gz" -C /opt/facturacion media/

# Limpiar backups antiguos
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "media_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completado: $DATE"
```

```bash
chmod +x /opt/facturacion/scripts/backup_db.sh
# Cron diario a las 02:00
echo "0 2 * * * deploy /opt/facturacion/scripts/backup_db.sh >> /opt/facturacion/logs/backup.log 2>&1" | crontab -u deploy -
```

### 10.2 Backup de Configuración
- `.env` → almacenar en gestor de secretos (1Password, Bitwarden, Vault)
- Configuración Nginx/Gunicorn → versionar en repo privado o backup

---

## 11. Verificación Post-Despliegue

### 11.1 Checks Automatizados
```bash
# 1. Django checks
cd /opt/facturacion/repo && source ../venv/bin/activate
python manage.py check --deploy

# 2. Health endpoint (crear vista simple /health/)
curl -f https://midominio.com/health/  # Debe retornar 200 OK

# 3. Login funciona
curl -X POST https://midominio.com/login/ \
  -d "username=admin&password=xxx&csrfmiddlewaretoken=xxx"

# 4. Static files sirven
curl -I https://midominio.com/static/admin/css/base.css  # 200 OK

# 4. Rate limiting login
for i in {1..6}; do curl -X POST https://midominio.com/login/ -d "username=admin&password=wrong"; done
# 5to debe dar 429

# 5. Security headers
curl -I https://midominio.com/ | grep -E "Strict-Transport|X-Frame|X-Content|X-XSS"
```

### 11.2 Tests de Humo (Smoke Tests)
```bash
# Ejecutar suite crítica en producción (solo lectura)
pytest facturacion/tests/test_permissions.py -v
pytest facturacion/tests/test_caja_auditoria.py::TestCajaAuditoriaPermisos -v
```

---

## 12. Rollback Plan

| Escenario | Acción |
|-----------|--------|
| **Deploy fallido** | `git checkout HEAD~1 && pip install -r requirements.txt && python manage.py migrate && systemctl restart gunicorn` |
| **Migración rota** | `python manage.py migrate facturacion <migration_anterior>` |
| **Configuración .env incorrecta** | Restaurar `.env` anterior + `systemctl restart gunicorn` |
| **SSL expirado** | `certbot renew --force-renewal && systemctl reload nginx` |
| **BD corrupta** | Restaurar último `pg_dump` + `systemctl restart gunicorn` |

---

## 13. Mantenimiento Continuo

| Frecuencia | Tarea |
|------------|-------|
| **Diario** | Verificar backups, revisar `logs/security.log` |
| **Semanal** | `apt update && apt upgrade -y`, `certbot renew --dry-run` |
| **Mensual** | Rotar SECRET_KEY (si política lo requiere), revisar accesos fallidos en axes |
| **Trimestral** | Test de restore de backup, actualizar dependencias `pip list --outdated` |

---

## 14. Contactos y Escalación

| Rol | Contacto | Escalación |
|-----|----------|------------|
| **DevOps** | [Nombre] | Nivel 1 |
| **DBA** | [Nombre] | Nivel 2 |
| **Seguridad** | [Nombre] | Nivel 3 |
| **Vendor Hosting** | [Proveedor] | Nivel 4 |

---

## 15. Aprobación y Firma

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| **Desarrollo** | | | |
| **DevOps** | | | |
| **Seguridad** | | | |
| **Producto** | | | |

---

**Fin del Plan de Despliegue**  
*Este documento no modifica código — solo planifica infraestructura y operaciones.*