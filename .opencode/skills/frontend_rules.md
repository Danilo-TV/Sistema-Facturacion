# Skill: Frontend Rules (UI &amp; AJAX) 

## Plantillas y Estilos 
- Usar maquetación responsive basada en Bootstrap 5 / AdminLTE 3. 
- DataTables para tabulación de datos y Select2 para búsquedas asíncronas de productos/clientes. 

## Integridad AJAX y Seguridad XSS 
- **Tokens CSRF**: Toda llamada `fetch()` o `$.ajax()` con método POST/PUT/DELETE debe incluir en las cabeceras: `'X-CSRFToken': getCookie('csrftoken')`.
- **Prohibición XSS**: NUNCA usar `|safe` o `mark_safe()` sobre contenido ingresado por usuarios.
- **Manejo de Errores**: Manejar respuestas HTTP 400 y 403 mostrando notificaciones con SweetAlert2.