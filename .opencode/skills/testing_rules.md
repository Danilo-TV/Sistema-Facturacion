# Testing Rules — Sistema de Facturación

> Reglas obligatorias para pruebas unitarias, de integración y de seguridad.

---

## 1. Estructura de Tests

- Tests en `facturacion/tests/` como paquete (no el archivo `tests.py` por defecto).
- Separar por dominio: `test_models.py`, `test_views.py`, `test_ajax.py`, `test_security.py`.
- Usar **pytest** + `pytest-django` como test runner (no el unittest de Django).
- Usar **Factory Boy** para datos de prueba (factories en `facturacion/tests/factories.py`).
- Cada test debe ser independiente (no compartir estado entre tests).

### Estructura recomendada

```
facturacion/tests/
    __init__.py
    factories.py          # Factories para todos los modelos
    conftest.py           # Fixtures globales (pytest)
    test_models.py        # Tests de modelos y validaciones
    test_views.py         # Tests de vistas CBVs
    test_ajax.py          # Tests de endpoints JSON
    test_security.py      # Tests de autenticación y permisos
```

---

## 2. Factory Boy — Data de Prueba

Crear factories para TODOS los modelos en `factories.py`:

```python
import factory
from decimal import Decimal
from facturacion.models import Usuario, Cliente, Categoria, Producto, CabeceraFactura, DetalleVenta


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario
        django_get_or_create = ['username']

    username = factory.Sequence(lambda n: f'usuario{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@test.com')
    password = factory.PostGenerationMethodCall('set_password', 'test123')
    rol = Usuario.Rol.VENDEDOR
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class ClienteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cliente

    tipo_documento = Cliente.TipoDocumento.RIF
    numero_documento = factory.Sequence(lambda n: f'J{n:08d}')
    nombre_razon_social = factory.Faker('company')
    telefono = factory.Faker('phone_number')
    is_active = True


class CategoriaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Categoria

    nombre = factory.Sequence(lambda n: f'Categoría {n}')
    is_active = True


class ProductoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Producto

    codigo = factory.Sequence(lambda n: f'PROD-{n:04d}')
    nombre = factory.Faker('word')
    categoria = factory.SubFactory(CategoriaFactory)
    precio_bs = Decimal('100.00')
    precio_usd = Decimal('10.00')
    stock_actual = 50
    stock_minimo = 10
    permite_stock_negativo = False
    is_active = True


class CabeceraFacturaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CabeceraFactura

    numero_factura = factory.Sequence(lambda n: f'FAC-20260521-{n:04d}')
    cliente = factory.SubFactory(ClienteFactory)
    usuario = factory.SubFactory(UsuarioFactory)
    tipo_documento = CabeceraFactura.TipoDocumento.FACTURA
    estatus = CabeceraFactura.Estatus.PAGADA
    tasa_cambio = Decimal('50.0000')
    moneda_principal = CabeceraFactura.Moneda.BS
    subtotal_bs = Decimal('0')
    subtotal_usd = Decimal('0')
    monto_iva_bs = Decimal('0')
    monto_iva_usd = Decimal('0')
    total_bs = Decimal('0')
    total_usd = Decimal('0')


class DetalleVentaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DetalleVenta

    cabecera = factory.SubFactory(CabeceraFacturaFactory)
    producto = factory.SubFactory(ProductoFactory)
    cantidad = 1
    precio_unitario_bs = Decimal('100.00')
    precio_unitario_usd = Decimal('10.00')
    subtotal_bs = Decimal('100.00')
    subtotal_usd = Decimal('10.00')
    monto_iva_bs = Decimal('16.00')
    monto_iva_usd = Decimal('1.60')
    total_bs = Decimal('116.00')
    total_usd = Decimal('11.60')
```

---

## 3. Tests de Lógica de Negocio — OBLIGATORIO

### 3.1. Cálculo de IVA 16%

```python
@pytest.mark.django_db
def test_detalle_venta_calcula_iva():
    """DetalleVenta.save() debe calcular IVA = subtotal * 0.16 con quantize."""
    cabecera = CabeceraFacturaFactory()
    producto = ProductoFactory(precio_bs=Decimal('250.00'), precio_usd=Decimal('25.00'))
    detalle = DetalleVentaFactory(
        cabecera=cabecera,
        producto=producto,
        cantidad=3,
        precio_unitario_bs=producto.precio_bs,
        precio_unitario_usd=producto.precio_usd,
    )

    expected_sub_bs = Decimal('750.00')       # 3 * 250
    expected_iva_bs = Decimal('120.00')        # 750 * 0.16
    expected_total_bs = Decimal('870.00')      # 750 + 120

    detalle.refresh_from_db()
    assert detalle.subtotal_bs == expected_sub_bs
    assert detalle.monto_iva_bs == expected_iva_bs
    assert detalle.total_bs == expected_total_bs
```

Cubrir:
- IVA con valores enteros.
- IVA con decimales (ej: 3 × 99,99).
- IVA con `tasa_cambio` para USD.
- Redondeo con `quantize(Decimal('0.01'))`, NO `round()`.

### 3.2. Moneda Dual

```python
@pytest.mark.django_db
def test_moneda_dual_en_totales():
    """Los totales USD deben ser total_bs / tasa_cambio."""
    cabecera = CabeceraFacturaFactory(
        tasa_cambio=Decimal('50.0000'),
        subtotal_bs=Decimal('1000.00'),
        subtotal_usd=Decimal('20.00'),
        monto_iva_bs=Decimal('160.00'),
        monto_iva_usd=Decimal('3.20'),
        total_bs=Decimal('1160.00'),
        total_usd=Decimal('23.20'),
    )

    assert cabecera.total_usd == cabecera.total_bs / cabecera.tasa_cambio
    assert cabecera.monto_iva_usd == cabecera.monto_iva_bs / cabecera.tasa_cambio
```

### 3.3. Stock Estricto

```python
@pytest.mark.django_db
def test_producto_stock_negativo_rechazado():
    """Producto.clean() debe rechazar stock_actual < 0 si permite_stock_negativo=False."""
    producto = ProductoFactory(stock_actual=-5, permite_stock_negativo=False)
    with pytest.raises(ValidationError):
        producto.full_clean()


@pytest.mark.django_db
def test_producto_stock_negativo_permitido():
    """Producto.clean() debe permitir stock_actual < 0 si permite_stock_negativo=True."""
    producto = ProductoFactory(stock_actual=-5, permite_stock_negativo=True)
    producto.full_clean()  # No debe lanzar excepción
```

Cubrir:
- Rechazar cuando `permite_stock_negativo=False` y stock < 0.
- Permitir cuando `permite_stock_negativo=True`.
- Descuento de stock al crear factura pagada.
- NO descontar stock en factura borrador.

### 3.4. Descuento Máximo 20%

```python
@pytest.mark.django_db
def test_descuento_excede_20_porciento():
    """CabeceraFactura.clean() debe rechazar descuento > 20% del subtotal."""
    cabecera = CabeceraFacturaFactory(
        subtotal_bs=Decimal('1000.00'),
        descuento_bs=Decimal('300.00'),  # 30% > 20%
    )
    with pytest.raises(ValidationError):
        cabecera.full_clean()
```

### 3.5. Validación RIF

```python
@pytest.mark.django_db
def test_cliente_rif_debe_iniciar_con_letra():
    """Cliente.clean() debe rechazar RIF sin letra inicial."""
    cliente = ClienteFactory(
        tipo_documento=Cliente.TipoDocumento.RIF,
        numero_documento='12345678',
    )
    with pytest.raises(ValidationError):
        cliente.full_clean()


@pytest.mark.django_db
def test_cliente_rif_valido():
    """Cliente.clean() debe aceptar RIF con letra inicial válida."""
    cliente = ClienteFactory(
        tipo_documento=Cliente.TipoDocumento.RIF,
        numero_documento='J-12345678',
    )
    cliente.full_clean()  # No debe lanzar excepción
```

---

## 4. Tests de Seguridad — OBLIGATORIO

### 4.1. LoginRequiredMixin

```python
@pytest.mark.django_db
def test_vista_redirige_sin_login(client):
    """Sin autenticación, toda vista debe redirigir a login."""
    urls_protegidas = [
        reverse('facturacion:dashboard'),
        reverse('facturacion:producto_list'),
        reverse('facturacion:factura_create'),
        reverse('facturacion:factura_list'),
        reverse('facturacion:cliente_list'),
        reverse('facturacion:cliente_search'),
        reverse('facturacion:producto_search'),
    ]
    for url in urls_protegidas:
        response = client.get(url)
        assert response.status_code == 302, f'{url} no redirige a login'
        assert '/login/' in response.url, f'{url} no redirige a /login/'


@pytest.mark.django_db
def test_vista_acceso_con_login(client):
    """Con autenticación, las vistas deben responder 200."""
    usuario = UsuarioFactory()
    client.force_login(usuario)
    response = client.get(reverse('facturacion:dashboard'))
    assert response.status_code == 200
```

### 4.2. Seguridad en Endpoints AJAX

```python
@pytest.mark.django_db
def test_ajax_sin_login(client):
    """Endpoints AJAX deben requerir autenticación."""
    response = client.get(reverse('facturacion:cliente_search') + '?q=test')
    assert response.status_code == 302
    assert '/login/' in response.url


@pytest.mark.django_db
def test_ajax_stock_insuficiente(client):
    """El servidor debe rechazar líneas con stock insuficiente."""
    usuario = UsuarioFactory()
    cliente_obj = ClienteFactory()
    producto = ProductoFactory(stock_actual=2)

    client.force_login(usuario)
    url = reverse('facturacion:factura_create')

    payload = {
        'cliente': str(cliente_obj.pk),
        'tasa_cambio': '50.0000',
        'moneda_principal': 'bs',
        'tipo_documento': 'factura',
        'detalles': [{
            'producto_id': str(producto.pk),
            'cantidad': 10,  # stock = 2, pide 10
            'precio_unitario_bs': '100.00',
            'precio_unitario_usd': '2.00',
            'descuento_bs': '0',
            'subtotal_bs': '1000.00',
            'subtotal_usd': '20.00',
            'monto_iva_bs': '160.00',
            'monto_iva_usd': '3.20',
            'total_bs': '1160.00',
            'total_usd': '23.20',
        }]
    }

    response = client.post(url, data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    assert 'Stock insuficiente' in response.json()['error']
```

### 4.3. CSRF en AJAX

- Verificar que los endpoints POST requieren CSRF token.
- Los tests deben incluir `X-CSRFToken` en el header.

---

## 5. Tests de Vistas — OBLIGATORIO

### 5.1. Vistas CBV

```python
@pytest.mark.django_db
def test_producto_list_contiene_productos(client):
    usuario = UsuarioFactory()
    ProductoFactory.create_batch(5)
    client.force_login(usuario)
    response = client.get(reverse('facturacion:producto_list'))
    assert response.status_code == 200
    assert 'productos' in response.context
    assert len(response.context['productos']) == 5
```

Cubrir para cada vista:
- Respuesta 200 con login.
- Contexto contiene los objetos esperados.
- Template correcto.

### 5.2. Creación de Factura (POST JSON)

```python
@pytest.mark.django_db
def test_crear_factura_completa(client):
    usuario = UsuarioFactory()
    cliente_obj = ClienteFactory()
    producto = ProductoFactory(
        precio_bs=Decimal('100.00'),
        precio_usd=Decimal('2.00'),
        stock_actual=50,
    )

    client.force_login(usuario)
    url = reverse('facturacion:factura_create')
    payload = {
        'cliente': str(cliente_obj.pk),
        'tasa_cambio': '50.0000',
        'moneda_principal': 'bs',
        'tipo_documento': 'factura',
        'detalles': [{
            'producto_id': str(producto.pk),
            'cantidad': 3,
            'precio_unitario_bs': '100.00',
            'precio_unitario_usd': '2.00',
            'descuento_bs': '0',
            'subtotal_bs': '300.00',
            'subtotal_usd': '6.00',
            'monto_iva_bs': '48.00',
            'monto_iva_usd': '0.96',
            'total_bs': '348.00',
            'total_usd': '6.96',
        }]
    }

    response = client.post(url, data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'redirect_url' in data

    # Verificar que se descontó el stock
    producto.refresh_from_db()
    assert producto.stock_actual == 47  # 50 - 3
```

---

## 6. Tests de Modelos — OBLIGATORIO

Cubrir para cada modelo:

```python
@pytest.mark.django_db
def test_producto_str():
    producto = ProductoFactory(codigo='TEST-001', nombre='Laptop')
    assert str(producto) == 'TEST-001 — Laptop'


@pytest.mark.django_db
def test_usuario_str():
    usuario = UsuarioFactory(username='jperez', first_name='Juan', last_name='Pérez', rol=Usuario.Rol.VENDEDOR)
    assert 'Juan Pérez' in str(usuario)
    assert 'Vendedor' in str(usuario)
```

---

## 7. Configuración de pytest

```ini
# pytest.ini (raíz del proyecto)
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = tests.py test_*.py *_tests.py
testpaths = facturacion/tests
```

```python
# conftest.py
import pytest
from facturacion.tests.factories import UsuarioFactory


@pytest.fixture
def usuario():
    return UsuarioFactory()


@pytest.fixture
def cliente_autenticado(client, usuario):
    client.force_login(usuario)
    return client
```

---

## 8. Checklist de Testing

Antes de marcar una tarea como completa, verificar:

- [ ] ¿Los modelos tienen test de creación + validación + `__str__`?
- [ ] ¿El IVA 16% tiene test con valores enteros y decimales?
- [ ] ¿La moneda dual (Bs/USD) está testeada?
- [ ] ¿El stock estricto tiene test positivo y negativo?
- [ ] ¿El descuento máximo 20% está testeado?
- [ ] ¿La validación RIF está testeada?
- [ ] ¿Toda vista protegida redirige a login?
- [ ] ¿Los endpoints AJAX rechazan stock insuficiente?
- [ ] ¿La creación de factura descuenta stock correctamente?
- [ ] ¿Hay factories para todos los modelos?
