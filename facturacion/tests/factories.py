from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from facturacion.models import (
    CabeceraFactura,
    Categoria,
    Cliente,
    DetalleVenta,
    Producto,
    Usuario,
)


# ======================================================================
# FACTORIES — datos de prueba para todos los modelos
# ======================================================================


class UsuarioFactory(DjangoModelFactory):
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


class ClienteFactory(DjangoModelFactory):
    class Meta:
        model = Cliente

    tipo_documento = Cliente.TipoDocumento.RIF
    numero_documento = factory.Sequence(lambda n: f'J{n:08d}')
    nombre_razon_social = factory.Faker('company')
    direccion = factory.Faker('address')
    telefono = factory.Faker('phone_number')
    email = factory.Faker('email')
    is_active = True


class CategoriaFactory(DjangoModelFactory):
    class Meta:
        model = Categoria

    nombre = factory.Sequence(lambda n: f'Categoría {n}')
    descripcion = factory.Faker('sentence')
    is_active = True


class ProductoFactory(DjangoModelFactory):
    class Meta:
        model = Producto

    codigo = factory.Sequence(lambda n: f'PROD-{n:04d}')
    nombre = factory.Faker('word')
    categoria = factory.SubFactory(CategoriaFactory)
    precio_bs = Decimal('100.00')
    precio_usd = Decimal('10.00')
    costo_bs = Decimal('60.00')
    stock_actual = 50
    stock_minimo = 10
    permite_stock_negativo = False
    is_active = True


class CabeceraFacturaFactory(DjangoModelFactory):
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
    descuento_bs = Decimal('0')
    descuento_usd = Decimal('0')
    total_bs = Decimal('0')
    total_usd = Decimal('0')


class DetalleVentaFactory(DjangoModelFactory):
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
