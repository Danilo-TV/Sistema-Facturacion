"""
Comando personalizado para poblar la base de datos con datos de prueba.

Uso:
    python manage.py seed_data

Elimina los datos existentes y crea:
    - 5 clientes con documentos venezolanos
    - 4 categorías de supermercado
    - 7 productos específicos (stock alto)
    - 2 facturas con IVA 16% y moneda dual
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from facturacion.models import (
    CabeceraFactura,
    Categoria,
    Cliente,
    DetalleVenta,
    Producto,
    Usuario,
)

IVA = Decimal('0.16')


def _calcular_linea(cantidad, precio_bs, precio_usd):
    """Calcula subtotal, IVA y total para una línea de detalle."""
    subtotal_bs = (cantidad * precio_bs).quantize(Decimal('0.01'))
    subtotal_usd = (cantidad * precio_usd).quantize(Decimal('0.01'))
    iva_bs = (subtotal_bs * IVA).quantize(Decimal('0.01'))
    iva_usd = (subtotal_usd * IVA).quantize(Decimal('0.01'))
    total_bs = (subtotal_bs + iva_bs).quantize(Decimal('0.01'))
    total_usd = (subtotal_usd + iva_usd).quantize(Decimal('0.01'))
    return subtotal_bs, subtotal_usd, iva_bs, iva_usd, total_bs, total_usd


class Command(BaseCommand):
    help = 'Puebla la base de datos con datos de prueba (clientes, categorías, productos y facturas).'

    def handle(self, *args, **options):
        # ------------------------------------------------------------------
        # 1. Limpiar datos existentes (orden inverso por FK)
        # ------------------------------------------------------------------
        self.stdout.write('Limpiando datos existentes...')
        DetalleVenta.objects.all().delete()
        CabeceraFactura.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()
        Cliente.objects.all().delete()
        # No eliminamos Usuario — podría haber superusuarios creados manualmente

        # ------------------------------------------------------------------
        # 2. Crear Clientes (5)
        # ------------------------------------------------------------------
        self.stdout.write('Creando clientes...')

        cliente1 = Cliente.objects.create(
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='J-12345678-0',
            nombre_razon_social='Tech Solutions C.A.',
            direccion='Av. Principal, Edif. Tecnológico, Piso 3, Caracas',
            telefono='+58 212-555-0101',
            email='ventas@techsolutions.com.ve',
        )
        cliente2 = Cliente.objects.create(
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='J-23456789-1',
            nombre_razon_social='Distribuidora Los Andes C.A.',
            direccion='Calle 5, Qta. Los Andes, Mérida',
            telefono='+58 274-555-0202',
            email='info@distlosandes.com.ve',
        )
        cliente3 = Cliente.objects.create(
            tipo_documento=Cliente.TipoDocumento.CEDULA,
            numero_documento='V-12345678',
            nombre_razon_social='María Gabriela Rodríguez',
            direccion='Urb. Las Flores, Calle 3, Casa 15, Valencia',
            telefono='+58 241-555-0303',
            email='mrodriguez@gmail.com',
        )
        cliente4 = Cliente.objects.create(
            tipo_documento=Cliente.TipoDocumento.RIF,
            numero_documento='J-34567890-2',
            nombre_razon_social='Comercializadora del Sur S.R.L.',
            direccion='Av. Bolívar, Centro Comercial Sur, Local 8, San Cristóbal',
            telefono='+58 276-555-0404',
            email='comercsrl@yahoo.com',
        )
        cliente5 = Cliente.objects.create(
            tipo_documento=Cliente.TipoDocumento.CEDULA,
            numero_documento='V-87654321',
            nombre_razon_social='Carlos Andrés Méndez',
            direccion='Calle 9, Edif. Luxor, Apto 4B, Maracaibo',
            telefono='+58 261-555-0505',
            email='camendez@hotmail.com',
        )

        # ------------------------------------------------------------------
        # 3. Crear Categorías (4)
        # ------------------------------------------------------------------
        self.stdout.write('Creando categorías...')

        cat_bebidas = Categoria.objects.create(
            nombre='Bebidas',
            descripcion='Bebidas gaseosas, jugos y refrescos.',
        )
        cat_carnes = Categoria.objects.create(
            nombre='Carnes',
            descripcion='Carnes de res, cerdo, pollo y embutidos.',
        )
        cat_lacteos = Categoria.objects.create(
            nombre='Lácteos',
            descripcion='Productos lácteos, yogures y derivados.',
        )
        cat_viveres = Categoria.objects.create(
            nombre='Víveres',
            descripcion='Alimentos preparados, enlatados y víveres en general.',
        )

        # ------------------------------------------------------------------
        # 4. Crear Productos (7)
        # ------------------------------------------------------------------
        self.stdout.write('Creando productos...')

        p_beb_coca = Producto.objects.create(
            codigo='BEB-001',
            nombre='Coca-Cola',
            descripcion='Gaseosa Coca-Cola 2 litros.',
            categoria=cat_bebidas,
            precio_bs=Decimal('60.00'),
            precio_usd=Decimal('1.20'),
            costo_bs=Decimal('42.00'),
            stock_actual=100,
            stock_minimo=20,
        )
        p_car_pollo = Producto.objects.create(
            codigo='CAR-001',
            nombre='Pollo',
            descripcion='Pollo entero fresco por kilo.',
            categoria=cat_carnes,
            precio_bs=Decimal('175.00'),
            precio_usd=Decimal('3.50'),
            costo_bs=Decimal('122.50'),
            stock_actual=80,
            stock_minimo=15,
        )
        p_car_chule = Producto.objects.create(
            codigo='CAR-002',
            nombre='Chuleta',
            descripcion='Chuleta de cerdo ahumada por kilo.',
            categoria=cat_carnes,
            precio_bs=Decimal('225.00'),
            precio_usd=Decimal('4.50'),
            costo_bs=Decimal('157.50'),
            stock_actual=60,
            stock_minimo=10,
        )
        p_lac_yogurt = Producto.objects.create(
            codigo='LAC-001',
            nombre='Yogurt',
            descripcion='Yogurt natural batido 1 litro.',
            categoria=cat_lacteos,
            precio_bs=Decimal('90.00'),
            precio_usd=Decimal('1.80'),
            costo_bs=Decimal('63.00'),
            stock_actual=70,
            stock_minimo=15,
        )
        p_car_morta = Producto.objects.create(
            codigo='CAR-003',
            nombre='Mortadela',
            descripcion='Mortadela tipo Bologna 500 gramos.',
            categoria=cat_carnes,
            precio_bs=Decimal('100.00'),
            precio_usd=Decimal('2.00'),
            costo_bs=Decimal('70.00'),
            stock_actual=90,
            stock_minimo=20,
        )
        p_viv_arroz = Producto.objects.create(
            codigo='VIV-001',
            nombre='Arroz con menestra',
            descripcion='Bandeja de arroz con menestra (porción individual).',
            categoria=cat_viveres,
            precio_bs=Decimal('125.00'),
            precio_usd=Decimal('2.50'),
            costo_bs=Decimal('87.50'),
            stock_actual=50,
            stock_minimo=10,
        )
        p_viv_papas = Producto.objects.create(
            codigo='VIV-002',
            nombre='Papas fritas',
            descripcion='Papas fritas en bolsa 200 gramos.',
            categoria=cat_viveres,
            precio_bs=Decimal('75.00'),
            precio_usd=Decimal('1.50'),
            costo_bs=Decimal('52.50'),
            stock_actual=100,
            stock_minimo=25,
        )

        # ------------------------------------------------------------------
        # 5. Obtener un usuario para asociar las facturas
        # ------------------------------------------------------------------
        usuario_admin = Usuario.objects.filter(is_superuser=True).first()
        if not usuario_admin:
            usuario_admin = Usuario.objects.filter(is_active=True).first()
        if not usuario_admin:
            self.stdout.write(self.style.WARNING(
                'No hay usuarios en la base de datos. Las facturas se crearán '
                'sin usuario asociado (violará NOT NULL). '
                'Cree un superusuario con: python manage.py createsuperuser'
            ))
            return

        # ------------------------------------------------------------------
        # 6. Crear Factura 1 — Tech Solutions C.A. (compra corporativa)
        # ------------------------------------------------------------------
        self.stdout.write('Creando facturas de ejemplo...')

        tasa_cambio_1 = Decimal('50.0000')
        factura1 = CabeceraFactura.objects.create(
            numero_factura='FAC-20260521-0001',
            cliente=cliente1,
            usuario=usuario_admin,
            tipo_documento=CabeceraFactura.TipoDocumento.FACTURA,
            estatus=CabeceraFactura.Estatus.PAGADA,
            tasa_cambio=tasa_cambio_1,
            moneda_principal=CabeceraFactura.Moneda.BS,
            subtotal_bs=Decimal('0'),
            subtotal_usd=Decimal('0'),
            monto_iva_bs=Decimal('0'),
            monto_iva_usd=Decimal('0'),
            total_bs=Decimal('0'),
            total_usd=Decimal('0'),
            observaciones='Compra corporativa — Bebidas, carnes y abarrotes para evento.',
        )

        # Línea 1: 10 Coca-Cola
        s1_bs, s1_usd, iva1_bs, iva1_usd, t1_bs, t1_usd = _calcular_linea(
            10, p_beb_coca.precio_bs, p_beb_coca.precio_usd,
        )
        DetalleVenta.objects.create(
            cabecera=factura1,
            producto=p_beb_coca,
            cantidad=10,
            precio_unitario_bs=p_beb_coca.precio_bs,
            precio_unitario_usd=p_beb_coca.precio_usd,
            subtotal_bs=s1_bs,
            subtotal_usd=s1_usd,
            monto_iva_bs=iva1_bs,
            monto_iva_usd=iva1_usd,
            total_bs=t1_bs,
            total_usd=t1_usd,
        )
        p_beb_coca.stock_actual -= 10
        p_beb_coca.save(update_fields=['stock_actual'])

        # Línea 2: 5 Pollo
        s2_bs, s2_usd, iva2_bs, iva2_usd, t2_bs, t2_usd = _calcular_linea(
            5, p_car_pollo.precio_bs, p_car_pollo.precio_usd,
        )
        DetalleVenta.objects.create(
            cabecera=factura1,
            producto=p_car_pollo,
            cantidad=5,
            precio_unitario_bs=p_car_pollo.precio_bs,
            precio_unitario_usd=p_car_pollo.precio_usd,
            subtotal_bs=s2_bs,
            subtotal_usd=s2_usd,
            monto_iva_bs=iva2_bs,
            monto_iva_usd=iva2_usd,
            total_bs=t2_bs,
            total_usd=t2_usd,
        )
        p_car_pollo.stock_actual -= 5
        p_car_pollo.save(update_fields=['stock_actual'])

        # Línea 3: 8 Yogurt
        s3_bs, s3_usd, iva3_bs, iva3_usd, t3_bs, t3_usd = _calcular_linea(
            8, p_lac_yogurt.precio_bs, p_lac_yogurt.precio_usd,
        )
        DetalleVenta.objects.create(
            cabecera=factura1,
            producto=p_lac_yogurt,
            cantidad=8,
            precio_unitario_bs=p_lac_yogurt.precio_bs,
            precio_unitario_usd=p_lac_yogurt.precio_usd,
            subtotal_bs=s3_bs,
            subtotal_usd=s3_usd,
            monto_iva_bs=iva3_bs,
            monto_iva_usd=iva3_usd,
            total_bs=t3_bs,
            total_usd=t3_usd,
        )
        p_lac_yogurt.stock_actual -= 8
        p_lac_yogurt.save(update_fields=['stock_actual'])

        # Línea 4: 12 Papas fritas
        s4_bs, s4_usd, iva4_bs, iva4_usd, t4_bs, t4_usd = _calcular_linea(
            12, p_viv_papas.precio_bs, p_viv_papas.precio_usd,
        )
        DetalleVenta.objects.create(
            cabecera=factura1,
            producto=p_viv_papas,
            cantidad=12,
            precio_unitario_bs=p_viv_papas.precio_bs,
            precio_unitario_usd=p_viv_papas.precio_usd,
            subtotal_bs=s4_bs,
            subtotal_usd=s4_usd,
            monto_iva_bs=iva4_bs,
            monto_iva_usd=iva4_usd,
            total_bs=t4_bs,
            total_usd=t4_usd,
        )
        p_viv_papas.stock_actual -= 12
        p_viv_papas.save(update_fields=['stock_actual'])

        # Actualizar totales de la factura 1
        total_sub_bs = s1_bs + s2_bs + s3_bs + s4_bs
        total_sub_usd = s1_usd + s2_usd + s3_usd + s4_usd
        total_iva_bs = iva1_bs + iva2_bs + iva3_bs + iva4_bs
        total_iva_usd = iva1_usd + iva2_usd + iva3_usd + iva4_usd
        total_bs = t1_bs + t2_bs + t3_bs + t4_bs
        total_usd = t1_usd + t2_usd + t3_usd + t4_usd

        factura1.subtotal_bs = total_sub_bs
        factura1.subtotal_usd = total_sub_usd
        factura1.monto_iva_bs = total_iva_bs
        factura1.monto_iva_usd = total_iva_usd
        factura1.total_bs = total_bs
        factura1.total_usd = total_usd
        factura1.save(update_fields=[
            'subtotal_bs', 'subtotal_usd', 'monto_iva_bs', 'monto_iva_usd',
            'total_bs', 'total_usd',
        ])

        self.stdout.write(f'  ✓ Factura {factura1.numero_factura}: '
                          f'{total_sub_bs} Bs + {total_iva_bs} IVA = {total_bs} Bs')

        # ------------------------------------------------------------------
        # 7. Crear Factura 2 — María Gabriela Rodríguez (consumo personal)
        # ------------------------------------------------------------------
        tasa_cambio_2 = Decimal('51.5000')
        factura2 = CabeceraFactura.objects.create(
            numero_factura='FAC-20260521-0002',
            cliente=cliente3,
            usuario=usuario_admin,
            tipo_documento=CabeceraFactura.TipoDocumento.FACTURA,
            estatus=CabeceraFactura.Estatus.PAGADA,
            tasa_cambio=tasa_cambio_2,
            moneda_principal=CabeceraFactura.Moneda.BS,
            subtotal_bs=Decimal('0'),
            subtotal_usd=Decimal('0'),
            monto_iva_bs=Decimal('0'),
            monto_iva_usd=Decimal('0'),
            total_bs=Decimal('0'),
            total_usd=Decimal('0'),
            observaciones='Compra personal — Carnes y víveres.',
        )

        # Línea 1: 6 Chuleta
        s5_bs, s5_usd, iva5_bs, iva5_usd, t5_bs, t5_usd = _calcular_linea(
            6, p_car_chule.precio_bs, p_car_chule.precio_usd,
        )
        DetalleVenta.objects.create(
            cabecera=factura2,
            producto=p_car_chule,
            cantidad=6,
            precio_unitario_bs=p_car_chule.precio_bs,
            precio_unitario_usd=p_car_chule.precio_usd,
            subtotal_bs=s5_bs,
            subtotal_usd=s5_usd,
            monto_iva_bs=iva5_bs,
            monto_iva_usd=iva5_usd,
            total_bs=t5_bs,
            total_usd=t5_usd,
        )
        p_car_chule.stock_actual -= 6
        p_car_chule.save(update_fields=['stock_actual'])

        # Línea 2: 3 Mortadela
        s6_bs, s6_usd, iva6_bs, iva6_usd, t6_bs, t6_usd = _calcular_linea(
            3, p_car_morta.precio_bs, p_car_morta.precio_usd,
        )
        DetalleVenta.objects.create(
            cabecera=factura2,
            producto=p_car_morta,
            cantidad=3,
            precio_unitario_bs=p_car_morta.precio_bs,
            precio_unitario_usd=p_car_morta.precio_usd,
            subtotal_bs=s6_bs,
            subtotal_usd=s6_usd,
            monto_iva_bs=iva6_bs,
            monto_iva_usd=iva6_usd,
            total_bs=t6_bs,
            total_usd=t6_usd,
        )
        p_car_morta.stock_actual -= 3
        p_car_morta.save(update_fields=['stock_actual'])

        # Línea 3: 4 Arroz con menestra
        s7_bs, s7_usd, iva7_bs, iva7_usd, t7_bs, t7_usd = _calcular_linea(
            4, p_viv_arroz.precio_bs, p_viv_arroz.precio_usd,
        )
        DetalleVenta.objects.create(
            cabecera=factura2,
            producto=p_viv_arroz,
            cantidad=4,
            precio_unitario_bs=p_viv_arroz.precio_bs,
            precio_unitario_usd=p_viv_arroz.precio_usd,
            subtotal_bs=s7_bs,
            subtotal_usd=s7_usd,
            monto_iva_bs=iva7_bs,
            monto_iva_usd=iva7_usd,
            total_bs=t7_bs,
            total_usd=t7_usd,
        )
        p_viv_arroz.stock_actual -= 4
        p_viv_arroz.save(update_fields=['stock_actual'])

        # Actualizar totales de la factura 2
        total_sub2_bs = s5_bs + s6_bs + s7_bs
        total_sub2_usd = s5_usd + s6_usd + s7_usd
        total_iva2_bs = iva5_bs + iva6_bs + iva7_bs
        total_iva2_usd = iva5_usd + iva6_usd + iva7_usd
        total2_bs = t5_bs + t6_bs + t7_bs
        total2_usd = t5_usd + t6_usd + t7_usd

        factura2.subtotal_bs = total_sub2_bs
        factura2.subtotal_usd = total_sub2_usd
        factura2.monto_iva_bs = total_iva2_bs
        factura2.monto_iva_usd = total_iva2_usd
        factura2.total_bs = total2_bs
        factura2.total_usd = total2_usd
        factura2.save(update_fields=[
            'subtotal_bs', 'subtotal_usd', 'monto_iva_bs', 'monto_iva_usd',
            'total_bs', 'total_usd',
        ])

        self.stdout.write(f'  ✓ Factura {factura2.numero_factura}: '
                          f'{total_sub2_bs} Bs + {total_iva2_bs} IVA = {total2_bs} Bs')

        # ------------------------------------------------------------------
        # 8. Resumen final
        # ------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS(
            '\n✅ Base de datos poblada exitosamente:\n'
            f'   • 5 clientes creados\n'
            f'   • 4 categorías de supermercado creadas\n'
            f'   • 7 productos de supermercado creados\n'
            f'   • 2 facturas con IVA 16%% y moneda dual\n'
            f'   • Stock descontado de las facturas correctamente'
        ))
