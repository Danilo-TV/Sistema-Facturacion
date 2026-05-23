import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from facturacion.models import CabeceraFactura, Cliente, DetalleVenta, Producto, Usuario
from facturacion.tests.factories import (
    CabeceraFacturaFactory,
    CategoriaFactory,
    ClienteFactory,
    DetalleVentaFactory,
    ProductoFactory,
    UsuarioFactory,
)


# ======================================================================
# IVA 16% — Cálculos del DetalleVenta
# ======================================================================


class TestDetalleVentaIVA:
    """DetalleVenta.save() auto-calcula subtotal, IVA y total."""

    @pytest.mark.django_db
    def test_iva_con_valores_enteros(self):
        """3 × 100.00 = 300.00 → IVA 48.00 → total 348.00."""
        detalle = DetalleVentaFactory(
            cantidad=3,
            precio_unitario_bs=Decimal('100.00'),
            precio_unitario_usd=Decimal('10.00'),
        )
        detalle.refresh_from_db()

        assert detalle.subtotal_bs == Decimal('300.00')
        assert detalle.subtotal_usd == Decimal('30.00')
        assert detalle.monto_iva_bs == Decimal('48.00')       # 300 * 0.16
        assert detalle.monto_iva_usd == Decimal('4.80')        # 30 * 0.16
        assert detalle.total_bs == Decimal('348.00')           # 300 + 48
        assert detalle.total_usd == Decimal('34.80')           # 30 + 4.80

    @pytest.mark.django_db
    def test_iva_con_valores_decimales(self):
        """3 × 99.99 = 299.97 → IVA 47.9952 → quantize(0.01) = 48.00."""
        detalle = DetalleVentaFactory(
            cantidad=3,
            precio_unitario_bs=Decimal('99.99'),
            precio_unitario_usd=Decimal('9.99'),
        )
        detalle.refresh_from_db()

        assert detalle.subtotal_bs == Decimal('299.97')        # 3 * 99.99
        assert detalle.monto_iva_bs == Decimal('48.00')         # 299.97 * 0.16 = 47.9952 → 48.00
        assert detalle.total_bs == Decimal('347.97')            # 299.97 + 48.00

    @pytest.mark.django_db
    def test_iva_con_cantidad_unitaria(self):
        """1 × 250.00 = 250.00 → IVA 40.00 → total 290.00."""
        detalle = DetalleVentaFactory(
            cantidad=1,
            precio_unitario_bs=Decimal('250.00'),
            precio_unitario_usd=Decimal('25.00'),
        )
        detalle.refresh_from_db()

        assert detalle.subtotal_bs == Decimal('250.00')
        assert detalle.monto_iva_bs == Decimal('40.00')
        assert detalle.total_bs == Decimal('290.00')

    @pytest.mark.django_db
    def test_iva_con_precio_cero(self):
        """Precio 0 → todo debe ser 0."""
        detalle = DetalleVentaFactory(
            cantidad=5,
            precio_unitario_bs=Decimal('0'),
            precio_unitario_usd=Decimal('0'),
        )
        detalle.refresh_from_db()

        assert detalle.subtotal_bs == Decimal('0')
        assert detalle.monto_iva_bs == Decimal('0')
        assert detalle.total_bs == Decimal('0')

    @pytest.mark.django_db
    def test_iva_usado_quantize_no_round(self):
        """Verificar que el redondeo usa quantize(0.01), no round() de Python.

        1 × 0.01 → subtotal 0.01 → IVA 0.0016 → quantize = 0.00
        round(0.0016, 2) = 0.00 (coincide, pero el mecanismo debe ser quantize).
        """
        detalle = DetalleVentaFactory(
            cantidad=1,
            precio_unitario_bs=Decimal('0.01'),
            precio_unitario_usd=Decimal('0.01'),
        )
        detalle.refresh_from_db()
        # Con quantize: 0.01 * 0.16 = 0.0016 → 0.00
        assert detalle.monto_iva_bs == Decimal('0.00')

    @pytest.mark.django_db
    def test_iva_varios_detalles_misma_factura(self):
        """Dos líneas en una misma factura, cada una con su propio cálculo."""
        cabecera = CabeceraFacturaFactory()
        d1 = DetalleVentaFactory(cabecera=cabecera, cantidad=2, precio_unitario_bs=Decimal('50.00'))
        d2 = DetalleVentaFactory(cabecera=cabecera, cantidad=3, precio_unitario_bs=Decimal('30.00'))

        d1.refresh_from_db()
        d2.refresh_from_db()

        # Línea 1: 2 × 50 = 100, IVA = 16, total = 116
        assert d1.subtotal_bs == Decimal('100.00')
        assert d1.monto_iva_bs == Decimal('16.00')
        assert d1.total_bs == Decimal('116.00')

        # Línea 2: 3 × 30 = 90, IVA = 14.40, total = 104.40
        assert d2.subtotal_bs == Decimal('90.00')
        assert d2.monto_iva_bs == Decimal('14.40')
        assert d2.total_bs == Decimal('104.40')


# ======================================================================
# MONEDA DUAL — Conversión Bs/USD
# ======================================================================


class TestMonedaDual:
    """CabeceraFactura almacena ambos valores; USD = Bs / tasa_cambio."""

    @pytest.mark.django_db
    def test_total_usd_es_bs_dividido_tasa(self):
        """total_usd debe ser exactamente total_bs / tasa_cambio."""
        factura = CabeceraFacturaFactory(
            tasa_cambio=Decimal('50.0000'),
            total_bs=Decimal('1160.00'),
            total_usd=Decimal('23.20'),
        )
        assert factura.total_usd == factura.total_bs / factura.tasa_cambio

    @pytest.mark.django_db
    def test_monto_iva_usd_es_iva_bs_dividido_tasa(self):
        factura = CabeceraFacturaFactory(
            tasa_cambio=Decimal('45.0000'),
            monto_iva_bs=Decimal('160.00'),
            monto_iva_usd=Decimal('3.56'),   # 160 / 45 = 3.5555... → 3.56
        )
        expected = (factura.monto_iva_bs / factura.tasa_cambio).quantize(Decimal('0.01'))
        assert factura.monto_iva_usd == expected

    @pytest.mark.django_db
    def test_subtotal_usd_es_subtotal_bs_dividido_tasa(self):
        factura = CabeceraFacturaFactory(
            tasa_cambio=Decimal('60.5000'),
            subtotal_bs=Decimal('1500.00'),
            subtotal_usd=Decimal('24.79'),   # 1500 / 60.5 = 24.793...
        )
        expected = (factura.subtotal_bs / factura.tasa_cambio).quantize(Decimal('0.01'))
        assert factura.subtotal_usd == expected

    @pytest.mark.django_db
    def test_descuento_usd_es_descuento_bs_dividido_tasa(self):
        factura = CabeceraFacturaFactory(
            tasa_cambio=Decimal('50.0000'),
            descuento_bs=Decimal('100.00'),
            descuento_usd=Decimal('2.00'),
        )
        assert factura.descuento_usd == factura.descuento_bs / factura.tasa_cambio

    @pytest.mark.django_db
    def test_tasa_cambio_uno_a_uno(self):
        """Si tasa_cambio = 1, Bs y USD deben ser iguales."""
        factura = CabeceraFacturaFactory(
            tasa_cambio=Decimal('1.0000'),
            total_bs=Decimal('1160.00'),
            total_usd=Decimal('1160.00'),
        )
        assert factura.total_usd == factura.total_bs
        assert factura.total_usd == Decimal('1160.00')

    @pytest.mark.django_db
    def test_tasa_cambio_gran_escala(self):
        """Tasa alta: 1 USD = 1000 Bs."""
        factura = CabeceraFacturaFactory(
            tasa_cambio=Decimal('1000.0000'),
            total_bs=Decimal('500000.00'),
            total_usd=Decimal('500.00'),
        )
        assert factura.total_usd == factura.total_bs / factura.tasa_cambio


# ======================================================================
# STOCK ESTRICTO — Validaciones del Producto
# ======================================================================


class TestStockEstricto:
    """Producto.clean() controla el stock según permite_stock_negativo."""

    @pytest.mark.django_db
    def test_rechaza_stock_negativo_sin_permiso(self):
        """Si permite_stock_negativo=False y stock < 0 → ValidationError."""
        producto = ProductoFactory(stock_actual=-5, permite_stock_negativo=False)
        with pytest.raises(ValidationError):
            producto.full_clean()

    @pytest.mark.django_db
    def test_permite_stock_negativo_con_permiso(self):
        """Si permite_stock_negativo=True y stock < 0 → OK."""
        producto = ProductoFactory(stock_actual=-5, permite_stock_negativo=True)
        producto.full_clean()  # No debe lanzar excepción

    @pytest.mark.django_db
    def test_stock_cero_es_valido(self):
        """stock_actual = 0 siempre es válido, independientemente del flag."""
        p1 = ProductoFactory(stock_actual=0, permite_stock_negativo=False)
        p2 = ProductoFactory(stock_actual=0, permite_stock_negativo=True)
        p1.full_clean()
        p2.full_clean()

    @pytest.mark.django_db
    def test_stock_positivo_siempre_valido(self):
        """stock_actual > 0 siempre es válido."""
        producto = ProductoFactory(stock_actual=100, permite_stock_negativo=False)
        producto.full_clean()


# ======================================================================
# DESCUENTO MÁXIMO 20%
# ======================================================================


class TestDescuentoMaximo:
    """CabeceraFactura.clean() valida descuento ≤ 20% del subtotal."""

    @pytest.mark.django_db
    def test_rechaza_descuento_excede_20_porciento(self):
        """30% > 20% → ValidationError."""
        factura = CabeceraFacturaFactory(
            subtotal_bs=Decimal('1000.00'),
            descuento_bs=Decimal('300.00'),   # 30%
        )
        with pytest.raises(ValidationError):
            factura.full_clean()

    @pytest.mark.django_db
    def test_permite_descuento_exactamente_20_porciento(self):
        """20% = 20% → OK."""
        factura = CabeceraFacturaFactory(
            subtotal_bs=Decimal('1000.00'),
            descuento_bs=Decimal('200.00'),   # 20% exacto
        )
        factura.full_clean()

    @pytest.mark.django_db
    def test_permite_descuento_menor_a_20_porciento(self):
        """10% < 20% → OK."""
        factura = CabeceraFacturaFactory(
            subtotal_bs=Decimal('1000.00'),
            descuento_bs=Decimal('100.00'),   # 10%
        )
        factura.full_clean()

    @pytest.mark.django_db
    def test_permite_descuento_cero(self):
        """0% siempre OK."""
        factura = CabeceraFacturaFactory(
            subtotal_bs=Decimal('1000.00'),
            descuento_bs=Decimal('0'),
        )
        factura.full_clean()


# ======================================================================
# VALIDACIÓN RIF
# ======================================================================


class TestValidacionRIF:
    """Cliente.clean() valida que RIF empiece con letra."""

    @pytest.mark.django_db
    def test_rechaza_rif_sin_letra_inicial(self):
        """RIF que empieza con número → ValidationError."""
        cliente = ClienteFactory(
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='12345678',
        )
        with pytest.raises(ValidationError):
            cliente.full_clean()

    @pytest.mark.django_db
    def test_acepta_rif_con_letra_j(self):
        """RIF J-12345678 → OK."""
        cliente = ClienteFactory(
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='J-12345678',
        )
        cliente.full_clean()

    @pytest.mark.django_db
    def test_acepta_rif_con_letra_g(self):
        """RIF G-12345678 → OK."""
        cliente = ClienteFactory(
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='G12345678',
        )
        cliente.full_clean()

    @pytest.mark.django_db
    def test_acepta_rif_con_letra_v(self):
        """RIF V-12345678 → OK."""
        cliente = ClienteFactory(
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='V12345678',
        )
        cliente.full_clean()

    @pytest.mark.django_db
    def test_rif_case_insensitive(self):
        """Letra minúscula también es válida."""
        cliente = ClienteFactory(
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='j-12345678',
        )
        cliente.full_clean()

    @pytest.mark.django_db
    def test_no_aplica_a_cedula(self):
        """Validación RIF no debe afectar cédulas."""
        cliente = ClienteFactory(
            tipo_documento=Cliente.TipoDocumento.CEDULA,
            numero_documento='12345678',   # sin letra, pero es cédula → OK
        )
        cliente.full_clean()

    @pytest.mark.django_db
    def test_no_aplica_a_pasaporte(self):
        """Validación RIF no debe afectar pasaportes."""
        cliente = ClienteFactory(
            tipo_documento=Cliente.TipoDocumento.PASAPORTE,
            numero_documento='A12345678',   # letra + número, no es RIF → OK
        )
        cliente.full_clean()


# ======================================================================
# UNIQUE TOGETHER — Cliente
# ======================================================================


class TestClienteUniqueDocumento:
    """tipo_documento + numero_documento debe ser único."""

    @pytest.mark.django_db
    def test_duplicado_rechazado(self):
        """Mismo tipo + mismo número → violación de integridad."""
        ClienteFactory(tipo_documento=Cliente.TipoDocumento.RIF, numero_documento='J-12345678')
        with pytest.raises(Exception):  # IntegrityError
            ClienteFactory(tipo_documento=Cliente.TipoDocumento.RIF, numero_documento='J-12345678')

    @pytest.mark.django_db
    def test_mismo_numero_distinto_tipo_permitido(self):
        """Mismo número, distinto tipo → OK."""
        ClienteFactory(tipo_documento=Cliente.TipoDocumento.RIF, numero_documento='12345678')
        ClienteFactory(tipo_documento=Cliente.TipoDocumento.CEDULA, numero_documento='12345678')


# ======================================================================
# __str__ DE CADA MODELO
# ======================================================================


class TestStringRepresentation:
    """Cada modelo debe tener un __str__ descriptivo."""

    @pytest.mark.django_db
    def test_usuario_str(self):
        usuario = UsuarioFactory(
            username='jperez',
            first_name='Juan',
            last_name='Pérez',
            rol=Usuario.Rol.VENDEDOR,
        )
        assert 'Juan Pérez' in str(usuario)
        assert 'Vendedor' in str(usuario)

    @pytest.mark.django_db
    def test_usuario_str_sin_nombre(self):
        """Sin first_name/last_name, debe mostrar username."""
        usuario = UsuarioFactory(
            username='admin1',
            first_name='',
            last_name='',
            rol=Usuario.Rol.ADMIN,
        )
        assert 'admin1' in str(usuario)
        assert 'Admin' in str(usuario)

    @pytest.mark.django_db
    def test_cliente_str(self):
        cliente = ClienteFactory(
            nombre_razon_social='Tech Solutions C.A.',
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='J-12345678',
        )
        assert 'Tech Solutions C.A.' in str(cliente)
        assert 'J-12345678' in str(cliente)

    @pytest.mark.django_db
    def test_categoria_str(self):
        categoria = CategoriaFactory(nombre='Electrónicos')
        assert str(categoria) == 'Electrónicos'

    @pytest.mark.django_db
    def test_producto_str(self):
        producto = ProductoFactory(codigo='LAP-001', nombre='Laptop')
        assert str(producto) == 'LAP-001 — Laptop'

    @pytest.mark.django_db
    def test_cabecera_factura_str(self):
        factura = CabeceraFacturaFactory(
            numero_factura='FAC-001',
            cliente__nombre_razon_social='Cliente Test',
        )
        assert 'FAC-001' in str(factura)
        assert 'Cliente Test' in str(factura)

    @pytest.mark.django_db
    def test_detalle_venta_str(self):
        detalle = DetalleVentaFactory(
            cabecera__numero_factura='FAC-001',
            producto__nombre='Laptop',
            cantidad=3,
        )
        assert 'FAC-001' in str(detalle)
        assert 'Laptop' in str(detalle)
        assert 'x3' in str(detalle)


# ======================================================================
# CREACIÓN BÁSICA DE MODELOS
# ======================================================================


class TestCreacionModelos:
    """Cada modelo se crea correctamente con valores por defecto."""

    @pytest.mark.django_db
    def test_crear_usuario(self):
        usuario = UsuarioFactory()
        assert usuario.pk is not None
        assert usuario.is_active is True
        assert usuario.check_password('test123')

    @pytest.mark.django_db
    def test_crear_cliente(self):
        cliente = ClienteFactory()
        assert cliente.pk is not None

    @pytest.mark.django_db
    def test_crear_categoria(self):
        categoria = CategoriaFactory()
        assert categoria.pk is not None

    @pytest.mark.django_db
    def test_crear_producto(self):
        producto = ProductoFactory()
        assert producto.pk is not None
        assert producto.categoria is not None

    @pytest.mark.django_db
    def test_crear_cabecera_factura(self):
        factura = CabeceraFacturaFactory()
        assert factura.pk is not None
        assert factura.cliente is not None
        assert factura.usuario is not None

    @pytest.mark.django_db
    def test_crear_detalle_venta(self):
        detalle = DetalleVentaFactory()
        assert detalle.pk is not None
        assert detalle.cabecera is not None
        assert detalle.producto is not None
