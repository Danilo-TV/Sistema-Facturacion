import json
from decimal import Decimal

import pytest
from django.urls import reverse

from facturacion.models import CabeceraFactura, DetalleVenta, Producto
from facturacion.tests.factories import (
    ClienteFactory,
    ProductoFactory,
    UsuarioFactory,
)


# ======================================================================
# SEGURIDAD — LoginRequiredMixin
# ======================================================================


class TestLoginRequired:
    """Toda vista debe redirigir a /login/ si el usuario no está autenticado."""

    # Todas las URLs protegidas del sistema
    URLS_PROTEGIDAS = [
        'facturacion:dashboard',
        'facturacion:producto_list',
        'facturacion:producto_create',
        'facturacion:cliente_list',
        'facturacion:cliente_create',
        'facturacion:categoria_list',
        'facturacion:categoria_create',
        'facturacion:factura_list',
        'facturacion:factura_create',
        'facturacion:cliente_search',
        'facturacion:producto_search',
    ]

    @pytest.mark.django_db
    @pytest.mark.parametrize('url_name', URLS_PROTEGIDAS)
    def test_vista_protegida_redirige_sin_login(self, client, url_name):
        """Sin autenticación, {url_name} debe redirigir a /login/."""
        response = client.get(reverse(url_name))
        assert response.status_code == 302, f'{url_name} no redirigió (status={response.status_code})'
        assert '/login/' in response.url, f'{url_name} no redirige a /login/'

    @pytest.mark.django_db
    @pytest.mark.parametrize('url_name', [
        'facturacion:producto_list',
        'facturacion:cliente_list',
        'facturacion:categoria_list',
        'facturacion:factura_list',
        'facturacion:dashboard',
    ])
    def test_vista_retorna_200_con_login(self, client, url_name):
        """Con autenticación, {url_name} debe responder 200 OK."""
        usuario = UsuarioFactory()
        client.force_login(usuario)
        response = client.get(reverse(url_name))
        assert response.status_code == 200, f'{url_name} falló con 200'

    @pytest.mark.django_db
    def test_factura_create_get_retorna_200(self, client):
        """FacturaCreateView GET debe responder 200 con login."""
        usuario = UsuarioFactory()
        client.force_login(usuario)
        response = client.get(reverse('facturacion:factura_create'))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_factura_detail_retorna_200(self, client):
        """FacturaDetailView debe responder 200 con login."""
        from facturacion.tests.factories import CabeceraFacturaFactory
        usuario = UsuarioFactory()
        factura = CabeceraFacturaFactory()
        client.force_login(usuario)
        response = client.get(reverse('facturacion:factura_detail', kwargs={'pk': factura.pk}))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_producto_edit_retorna_200(self, client):
        """ProductoUpdateView debe responder 200 con login."""
        from facturacion.tests.factories import ProductoFactory
        usuario = UsuarioFactory()
        producto = ProductoFactory()
        client.force_login(usuario)
        response = client.get(reverse('facturacion:producto_edit', kwargs={'pk': producto.pk}))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_producto_delete_retorna_200(self, client):
        """ProductoDeleteView GET debe responder 200 con login."""
        from facturacion.tests.factories import ProductoFactory
        usuario = UsuarioFactory()
        producto = ProductoFactory()
        client.force_login(usuario)
        response = client.get(reverse('facturacion:producto_delete', kwargs={'pk': producto.pk}))
        assert response.status_code == 200


# ======================================================================
# SEGURIDAD — Endpoints AJAX
# ======================================================================


class TestAJAXSeguridad:
    """Los endpoints AJAX también deben requerir autenticación."""

    @pytest.mark.django_db
    def test_cliente_search_sin_login(self, client):
        """Endpoint de búsqueda de clientes debe redirigir sin auth."""
        response = client.get(reverse('facturacion:cliente_search') + '?q=test')
        assert response.status_code == 302
        assert '/login/' in response.url

    @pytest.mark.django_db
    def test_producto_search_sin_login(self, client):
        """Endpoint de búsqueda de productos debe redirigir sin auth."""
        response = client.get(reverse('facturacion:producto_search') + '?q=test')
        assert response.status_code == 302
        assert '/login/' in response.url

    @pytest.mark.django_db
    def test_cliente_search_retorna_json(self, client):
        """Endpoint de búsqueda debe retornar JSON con items."""
        usuario = UsuarioFactory()
        ClienteFactory(nombre_razon_social='Tech Solutions')
        client.force_login(usuario)
        response = client.get(reverse('facturacion:cliente_search') + '?q=Tech')
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert len(data['items']) > 0

    @pytest.mark.django_db
    def test_producto_search_retorna_json_con_precios(self, client):
        """Endpoint de búsqueda debe incluir precio y stock en la respuesta."""
        usuario = UsuarioFactory()
        ProductoFactory(codigo='LAP-001', nombre='Laptop', precio_bs=Decimal('500.00'))
        client.force_login(usuario)
        response = client.get(reverse('facturacion:producto_search') + '?q=LAP')
        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) > 0
        assert 'precio_bs' in data['items'][0]
        assert 'stock_actual' in data['items'][0]

    @pytest.mark.django_db
    def test_cliente_search_requiere_minimo_2_caracteres(self, client):
        """Búsqueda con menos de 2 caracteres debe retornar vacío."""
        usuario = UsuarioFactory()
        ClienteFactory()
        client.force_login(usuario)
        response = client.get(reverse('facturacion:cliente_search') + '?q=a')
        data = response.json()
        assert data['items'] == []


# ======================================================================
# STOCK — Validación en POST de FacturaCreateView
# ======================================================================


class TestStockEnCreacionFactura:
    """El servidor debe validar stock al crear la factura."""

    @pytest.mark.django_db
    def test_rechaza_stock_insuficiente(self, client):
        """Si la cantidad solicitada excede el stock, debe responder 400."""
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
                'cantidad': 10,
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

    @pytest.mark.django_db
    def test_rechaza_cantidad_invalida(self, client):
        """Cantidad cero o negativa debe ser rechazada."""
        usuario = UsuarioFactory()
        cliente_obj = ClienteFactory()
        producto = ProductoFactory(stock_actual=10)

        client.force_login(usuario)
        url = reverse('facturacion:factura_create')

        for cant in [0, -1, -5]:
            payload = {
                'cliente': str(cliente_obj.pk),
                'tasa_cambio': '50.0000',
                'moneda_principal': 'bs',
                'tipo_documento': 'factura',
                'detalles': [{
                    'producto_id': str(producto.pk),
                    'cantidad': cant,
                    'precio_unitario_bs': '100.00',
                    'precio_unitario_usd': '2.00',
                    'descuento_bs': '0',
                    'subtotal_bs': '100.00',
                    'subtotal_usd': '2.00',
                    'monto_iva_bs': '16.00',
                    'monto_iva_usd': '0.32',
                    'total_bs': '116.00',
                    'total_usd': '2.32',
                }]
            }
            response = client.post(url, data=json.dumps(payload), content_type='application/json')
            assert response.status_code == 400
            assert 'cantidad debe ser mayor a cero' in response.json()['error'].lower()

    @pytest.mark.django_db
    def test_permite_venta_con_stock_suficiente(self, client):
        """Si hay stock suficiente, la petición debe procesarse (sin error de stock)."""
        usuario = UsuarioFactory()
        cliente_obj = ClienteFactory()
        producto = ProductoFactory(stock_actual=50)

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

    @pytest.mark.django_db
    def test_stock_se_descarta_al_crear_factura(self, client):
        """Al crear factura pagada, el stock del producto debe disminuir."""
        usuario = UsuarioFactory()
        cliente_obj = ClienteFactory()
        producto = ProductoFactory(stock_actual=50)

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

        producto.refresh_from_db()
        assert producto.stock_actual == 47  # 50 - 3


# ======================================================================
# CREACIÓN COMPLETA DE FACTURA
# ======================================================================


class TestCreacionFacturaCompleta:
    """Flujo completo de creación de factura vía POST JSON."""

    @pytest.mark.django_db
    def test_crear_factura_con_un_producto(self, client):
        """Factura con 1 producto: verificar creación y montos."""
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
        assert 'numero_factura' in data

        # Verificar que la factura existe en DB
        factura = CabeceraFactura.objects.get(numero_factura=data['numero_factura'])
        assert factura.cliente == cliente_obj
        assert factura.usuario == usuario
        assert factura.total_bs == Decimal('348.00')
        assert factura.total_usd == Decimal('6.96')
        assert factura.estatus == CabeceraFactura.Estatus.PAGADA

        # Verificar que el detalle existe
        assert factura.detalles.count() == 1
        detalle = factura.detalles.first()
        assert detalle.producto == producto
        assert detalle.cantidad == 3
        assert detalle.total_bs == Decimal('348.00')

    @pytest.mark.django_db
    def test_crear_factura_con_varios_productos(self, client):
        """Factura con 2 productos: verificar montos consolidados."""
        usuario = UsuarioFactory()
        cliente_obj = ClienteFactory()
        p1 = ProductoFactory(precio_bs=Decimal('100.00'), precio_usd=Decimal('2.00'), stock_actual=10)
        p2 = ProductoFactory(precio_bs=Decimal('50.00'), precio_usd=Decimal('1.00'), stock_actual=20)

        client.force_login(usuario)
        url = reverse('facturacion:factura_create')

        payload = {
            'cliente': str(cliente_obj.pk),
            'tasa_cambio': '50.0000',
            'moneda_principal': 'bs',
            'tipo_documento': 'factura',
            'detalles': [
                {
                    'producto_id': str(p1.pk),
                    'cantidad': 2,
                    'precio_unitario_bs': '100.00',
                    'precio_unitario_usd': '2.00',
                    'descuento_bs': '0',
                    'subtotal_bs': '200.00',
                    'subtotal_usd': '4.00',
                    'monto_iva_bs': '32.00',
                    'monto_iva_usd': '0.64',
                    'total_bs': '232.00',
                    'total_usd': '4.64',
                },
                {
                    'producto_id': str(p2.pk),
                    'cantidad': 5,
                    'precio_unitario_bs': '50.00',
                    'precio_unitario_usd': '1.00',
                    'descuento_bs': '0',
                    'subtotal_bs': '250.00',
                    'subtotal_usd': '5.00',
                    'monto_iva_bs': '40.00',
                    'monto_iva_usd': '0.80',
                    'total_bs': '290.00',
                    'total_usd': '5.80',
                },
            ]
        }

        response = client.post(url, data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        factura = CabeceraFactura.objects.get(numero_factura=data['numero_factura'])
        assert factura.detalles.count() == 2
        assert factura.subtotal_bs == Decimal('450.00')    # 200 + 250
        assert factura.monto_iva_bs == Decimal('72.00')     # 32 + 40
        assert factura.total_bs == Decimal('522.00')        # 232 + 290

        # Stock descontado
        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.stock_actual == 8   # 10 - 2
        assert p2.stock_actual == 15  # 20 - 5

    @pytest.mark.django_db
    def test_rechaza_factura_sin_cliente(self, client):
        """POST sin cliente debe responder 400."""
        usuario = UsuarioFactory()
        client.force_login(usuario)
        url = reverse('facturacion:factura_create')

        payload = {
            'tasa_cambio': '50.0000',
            'moneda_principal': 'bs',
            'tipo_documento': 'factura',
            'detalles': [],
        }

        response = client.post(url, data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 400
        assert 'cliente' in response.json()['error'].lower() or 'seleccionar' in response.json()['error'].lower()

    @pytest.mark.django_db
    def test_rechaza_factura_sin_productos(self, client):
        """POST sin detalles debe responder 400."""
        usuario = UsuarioFactory()
        cliente_obj = ClienteFactory()
        client.force_login(usuario)
        url = reverse('facturacion:factura_create')

        payload = {
            'cliente': str(cliente_obj.pk),
            'tasa_cambio': '50.0000',
            'moneda_principal': 'bs',
            'tipo_documento': 'factura',
            'detalles': [],
        }

        response = client.post(url, data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 400
        assert 'producto' in response.json()['error'].lower() or 'agregar' in response.json()['error'].lower()

    @pytest.mark.django_db
    def test_rechaza_json_invalido(self, client):
        """POST con JSON mal formado debe responder 400."""
        usuario = UsuarioFactory()
        client.force_login(usuario)
        url = reverse('facturacion:factura_create')

        response = client.post(url, data='esto-no-es-json', content_type='application/json')
        assert response.status_code == 400
        assert 'JSON' in response.json()['error']


# ======================================================================
# VALIDACIONES DEL SERVIDOR — Rechazar descuento excesivo
# ======================================================================


class TestDescuentoEnCreacionFactura:
    """El servidor debe validar descuento ≤ 20% al crear la factura."""

    @pytest.mark.django_db
    def test_rechaza_descuento_excesivo(self, client):
        """Descuento > 20% del subtotal debe ser rechazado."""
        usuario = UsuarioFactory()
        cliente_obj = ClienteFactory()
        producto = ProductoFactory(precio_bs=Decimal('100.00'), stock_actual=10)

        client.force_login(usuario)
        url = reverse('facturacion:factura_create')

        payload = {
            'cliente': str(cliente_obj.pk),
            'tasa_cambio': '50.0000',
            'moneda_principal': 'bs',
            'tipo_documento': 'factura',
            'detalles': [{
                'producto_id': str(producto.pk),
                'cantidad': 5,
                'precio_unitario_bs': '100.00',
                'precio_unitario_usd': '2.00',
                'descuento_bs': '150.00',       # subtotal = 500, 150 = 30% > 20%
                'subtotal_bs': '500.00',
                'subtotal_usd': '10.00',
                'monto_iva_bs': '56.00',        # (500 - 150) * 0.16 = 56
                'monto_iva_usd': '1.12',
                'total_bs': '406.00',
                'total_usd': '8.12',
            }]
        }

        response = client.post(url, data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 400
        assert 'descuento' in response.json()['error'].lower()
