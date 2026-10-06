# Skill: Security Rules (OWASP Top 10)

## A01: Broken Access Control (IDOR)
- Filtrar obligatoriamente la consulta en el servidor:
  ```python
  def get_queryset(self):
      return Factura.objects.filter(empresa=self.request.user.empresa)

```

* No confiar en IDs pasados por URL o cuerpo JSON sin validar pertenencia.

## A03: Injection (SQLi)

* Prohibido concatenar parámetros en consultas SQL. Usar el ORM parametrizado.
* Validar argumentos de ordenamiento dinámico contra una lista blanca permitida.

## A05: Security Misconfiguration (Mass Assignment)

* Declarar siempre los campos explícitamente en formularios: `fields = ['cliente', 'monto']`. NUNCA usar `__all__`.

## Respuestas AJAX No Autorizadas

* Retornar respuesta JSON con estado HTTP 403 Forbidden para peticiones AJAX sin permiso, no redirecciones a HTML de login.

```

#### D) `.agents/skills/testing_rules.md`
```markdown
# Skill: Testing Rules (Pytest &; TDD)

## Estructura de Pruebas
- Toda prueba debe alojarse en `facturacion/tests/` con el prefijo `test_*.py`.
- Usar `factory_boy` para la generación de accesorios (fixtures) de modelos (Usuarios, Clientes, Facturas).

## Cobertura Mínima Obligatoria
1. **Pruebas de Permisos**: Verificar que usuarios sin rol reciban HTTP 403 Forbidden.
2. **Pruebas de Concurrencia/Stock**: Validar que no se permita vender productos sin inventario disponible.
3. **Pruebas de Transacción**: Verificar el cálculo automático de IVA 16% y equivalencia dual Bs/USD.
4. **Pruebas de Emailing**: Validar el envío de correos utilizando `django.core.mail.outbox`.