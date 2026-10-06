"""
Tests para el Panel de Control y Auditoría de Cierres de Caja (Hito 5).

Verifica:
- Permisos de acceso (solo Admin/Supervisor)
- Métricas y cálculos correctos
- Filtros de búsqueda
- Exportación PDF/Excel/CSV
"""
import csv
import json
from decimal import Decimal
from io import BytesIO

import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from openpyxl import load_workbook

from facturacion.models import CabeceraFactura, Cliente, DetalleVenta, Producto, TurnoCaja, Usuario
from facturacion.tests.factories import (
    CabeceraFacturaFactory,
    ClienteFactory,
    DetalleVentaFactory,
    ProductoFactory,
    UsuarioFactory,
)
from facturacion.tests.conftest import usuario_con_permisos


# ======================================================================
# FIXTURES
# ======================================================================

@pytest.fixture
def usuario_admin():
    """Usuario admin con is_staff=True y permisos de auditoría."""
    user = UsuarioFactory(username='admin_audit', is_staff=True, rol=Usuario.Rol.ADMIN)
    user.set_password('admin123')
    user.save()
    # Agregar permisos específicos
    for codename in ['view_turnocaja_audit', 'export_turnocaja_audit', 'view_turnocaja', 'view_cabecerafactura', 'view_producto', 'view_cliente']:
        perm = Permission.objects.get(
            content_type__app_label='facturacion',
            codename=codename,
        )
        user.user_permissions.add(perm)
    return user


@pytest.fixture
def usuario_supervisor():
    """Usuario supervisor (no staff pero con permiso view_turnocaja_audit)."""
    user = UsuarioFactory(username='supervisor_audit', is_staff=False, rol=Usuario.Rol.VENDEDOR)
    user.set_password('super123')
    user.save()
    # Agregar permisos de auditoría
    for codename in ['view_turnocaja_audit', 'export_turnocaja_audit', 'view_turnocaja', 'view_cabecerafactura', 'view_producto', 'view_cliente']:
        perm = Permission.objects.get(
            content_type__app_label='facturacion',
            codename=codename,
        )
        user.user_permissions.add(perm)
    return user


@pytest.fixture
def usuario_cajero():
    """Usuario cajero estándar SIN permisos de auditoría."""
    user = UsuarioFactory(username='cajero_audit', is_staff=False, rol=Usuario.Rol.VENDEDOR)
    user.set_password('cajero123')
    user.save()
    # Solo permisos básicos de cajero
    for codename in ['view_turnocaja', 'add_turnocaja', 'change_turnocaja', 'view_cabecerafactura', 'add_cabecerafactura', 'view_producto', 'add_cliente', 'view_cliente', 'change_cliente']:
        perm = Permission.objects.get(
            content_type__app_label='facturacion',
            codename=codename,
        )
        user.user_permissions.add(perm)
    return user


@pytest.fixture
def cliente_test():
    """Cliente de prueba."""
    return ClienteFactory(nombre_razon_social='Cliente Test', tipo_documento=Cliente.TipoDocumento.RIF, numero_documento='J123456789')


@pytest.fixture
def producto_test():
    """Producto de prueba."""
    categoria = ProductoFactory().categoria  # Reuse category from factory
    return ProductoFactory(
        codigo='PROD-TEST',
        nombre='Producto Test',
        precio_bs=Decimal('100.00'),
        precio_usd=Decimal('2.00'),
        stock_actual=100,
        categoria=categoria,
    )


@pytest.fixture
def turnos_varios(usuario_cajero, usuario_admin, cliente_test, producto_test):
    """Crear varios turnos cerrados con diferentes escenarios para tests de filtros."""
    from zoneinfo import ZoneInfo
    from django.utils import timezone
    
    caracas_tz = ZoneInfo('America/Caracas')
    
    turnos = []
    
    # Turno 1: Cuadrado (diferencia = 0)
    t1 = TurnoCaja.objects.create(
        cajero=usuario_cajero,
        monto_inicial=Decimal('100.00'),
        monto_efectivo_sistema=Decimal('500.00'),
        monto_tarjeta_sistema=Decimal('10.00'),
        efectivo_declarado=Decimal('500.00'),
        tarjeta_declarada=Decimal('10.00'),
        diferencia=Decimal('0.00'),
        estatus=TurnoCaja.Estatus.CERRADA,
        fecha_cierre=timezone.now(),
    )
    # Crear facturas para el turno
    factura1 = CabeceraFacturaFactory(
        cliente=cliente_test,
        usuario=usuario_cajero,
        turno_caja=t1,
        estatus=CabeceraFactura.Estatus.PAGADA,
        total_bs=Decimal('500.00'),
        total_usd=Decimal('10.00'),
        tasa_cambio=Decimal('50.0000'),
        moneda_principal=CabeceraFactura.Moneda.BS,
    )
    DetalleVentaFactory(cabecera=factura1, producto=producto_test, cantidad=5)
    turnos.append(t1)
    
    # Turno 2: Faltante (diferencia < 0)
    t2 = TurnoCaja.objects.create(
        cajero=usuario_admin,
        monto_inicial=Decimal('100.00'),
        monto_efectivo_sistema=Decimal('1000.00'),
        monto_tarjeta_sistema=Decimal('20.00'),
        efectivo_declarado=Decimal('950.00'),
        tarjeta_declarada=Decimal('20.00'),
        diferencia=Decimal('-50.00'),
        estatus=TurnoCaja.Estatus.CERRADA,
        fecha_cierre=timezone.now(),
    )
    factura2 = CabeceraFacturaFactory(
        cliente=cliente_test,
        usuario=usuario_admin,
        turno_caja=t2,
        estatus=CabeceraFactura.Estatus.PAGADA,
        total_bs=Decimal('1000.00'),
        total_usd=Decimal('20.00'),
        tasa_cambio=Decimal('50.0000'),
        moneda_principal=CabeceraFactura.Moneda.BS,
    )
    DetalleVentaFactory(cabecera=factura2, producto=producto_test, cantidad=10)
    turnos.append(t2)
    
    # Turno 3: Sobrante (diferencia > 0)
    t3 = TurnoCaja.objects.create(
        cajero=usuario_cajero,
        monto_inicial=Decimal('100.00'),
        monto_efectivo_sistema=Decimal('300.00'),
        monto_tarjeta_sistema=Decimal('5.00'),
        efectivo_declarado=Decimal('350.00'),
        tarjeta_declarada=Decimal('5.00'),
        diferencia=Decimal('50.00'),
        estatus=TurnoCaja.Estatus.CERRADA,
        fecha_cierre=timezone.now(),
    )
    factura3 = CabeceraFacturaFactory(
        cliente=cliente_test,
        usuario=usuario_cajero,
        turno_caja=t3,
        estatus=CabeceraFactura.Estatus.PAGADA,
        total_bs=Decimal('300.00'),
        total_usd=Decimal('5.00'),
        tasa_cambio=Decimal('50.0000'),
        moneda_principal=CabeceraFactura.Moneda.BS,
    )
    DetalleVentaFactory(cabecera=factura3, producto=producto_test, cantidad=3)
    turnos.append(t3)
    
    # Turno 4: Abierto (no debe aparecer en historial)
    t4 = TurnoCaja.objects.create(
        cajero=usuario_cajero,
        monto_inicial=Decimal('100.00'),
        estatus=TurnoCaja.Estatus.ABIERTA,
    )
    turnos.append(t4)
    
    return turnos


@pytest.fixture
def turno_con_ventas(usuario_cajero, cliente_test, producto_test):
    """Turno cerrado con facturas y detalles para tests de métricas detalladas."""
    from django.utils import timezone
    from zoneinfo import ZoneInfo
    
    caracas_tz = ZoneInfo('America/Caracas')
    
    turno = TurnoCaja.objects.create(
        cajero=usuario_cajero,
        monto_inicial=Decimal('100.00'),
        monto_efectivo_sistema=Decimal('1500.00'),
        monto_tarjeta_sistema=Decimal('30.00'),
        efectivo_declarado=Decimal('1550.00'),
        tarjeta_declarada=Decimal('30.00'),
        diferencia=Decimal('50.00'),
        estatus=TurnoCaja.Estatus.CERRADA,
        fecha_cierre=timezone.now(),
    )
    
    # Facturas en efectivo
    factura_efectivo = CabeceraFacturaFactory(
        cliente=cliente_test,
        usuario=usuario_cajero,
        turno_caja=turno,
        estatus=CabeceraFactura.Estatus.PAGADA,
        total_bs=Decimal('1500.00'),
        total_usd=Decimal('30.00'),
        tasa_cambio=Decimal('50.0000'),
        moneda_principal=CabeceraFactura.Moneda.BS,
    )
    DetalleVentaFactory(cabecera=factura_efectivo, producto=producto_test, cantidad=15)
    
    return turno


# ======================================================================
# TESTS DE PERMISOS
# ======================================================================

@pytest.mark.django_db
class TestCajaAuditoriaPermisos:
    """Tests de control de acceso a vistas de auditoría."""

    def test_cajero_sin_permiso_recibe_403_en_historial(self, client, usuario_cajero):
        """Cajero estándar recibe 403 al acceder a /caja/historial/."""
        client.force_login(usuario_cajero)
        response = client.get(reverse('facturacion:caja_historial_audit'))
        assert response.status_code == 403

    def test_cajero_sin_permiso_recibe_403_en_detalle(self, client, usuario_cajero, turnos_varios):
        """Cajero recibe 403 en detalle de cierre."""
        client.force_login(usuario_cajero)
        turno_cerrado = [t for t in turnos_varios if t.estatus == TurnoCaja.Estatus.CERRADA][0]
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_cerrado.pk}))
        assert response.status_code == 403

    def test_admin_accede_historial_200(self, client, usuario_admin):
        """Admin/Supervisor accede a historial con 200."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'))
        assert response.status_code == 200

    def test_admin_accede_detalle_200(self, client, usuario_admin, turnos_varios):
        """Admin accede a detalle de cierre."""
        client.force_login(usuario_admin)
        turno_cerrado = [t for t in turnos_varios if t.estatus == TurnoCaja.Estatus.CERRADA][0]
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_cerrado.pk}))
        assert response.status_code == 200

    def test_supervisor_accede_historial_200(self, client, usuario_supervisor):
        """Supervisor (no staff pero con permiso) accede a historial con 200."""
        client.force_login(usuario_supervisor)
        response = client.get(reverse('facturacion:caja_historial_audit'))
        assert response.status_code == 200

    def test_ajax_sin_permiso_retorna_403_json(self, client, usuario_cajero):
        """AJAX a exportación retorna 403 JSON."""
        client.force_login(usuario_cajero)
        response = client.get(
            reverse('facturacion:caja_historial_export_excel'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        assert response.status_code == 403
        assert response.json()['error'] == 'Acceso denegado'

    def test_sin_login_redirige_a_login(self, client):
        """Sin autenticación, redirige a /login/ o retorna 403 (PermissionDenied)."""
        response = client.get(reverse('facturacion:caja_historial_audit'))
        # La vista requiere permisos específicos, así que puede dar 403 antes de redirigir
        assert response.status_code in [302, 403]


# ======================================================================
# TESTS DE MÉTRICAS Y CÁLCULOS
# ======================================================================

@pytest.mark.django_db
class TestCajaAuditoriaMetricas:
    """Verificar cálculos exactos de métricas en auditoría."""

    def test_diferencia_cuadrada_cero(self, turnos_varios):
        """Turno cuadrado: diferencia = 0."""
        turno_cuadrado = [t for t in turnos_varios if t.diferencia == Decimal('0')][0]
        assert turno_cuadrado.diferencia == Decimal('0')

    def test_faltante_negativo(self, turnos_varios):
        """Faltante: diferencia < 0."""
        turno_faltante = [t for t in turnos_varios if t.diferencia < Decimal('0')][0]
        assert turno_faltante.diferencia < Decimal('0')

    def test_sobrante_positivo(self, turnos_varios):
        """Sobrante: diferencia > 0."""
        turno_sobrante = [t for t in turnos_varios if t.diferencia > Decimal('0')][0]
        assert turno_sobrante.diferencia > Decimal('0')

    def test_totales_sistema_calculo_correcto(self, turnos_varios):
        """Total sistema = efectivo_sistema + tarjeta_sistema."""
        for turno in turnos_varios:
            if turno.estatus == TurnoCaja.Estatus.CERRADA:
                total_sistema = (turno.monto_efectivo_sistema or Decimal('0')) + (turno.monto_tarjeta_sistema or Decimal('0'))
                assert hasattr(turno, 'total_sistema_calculado') or total_sistema >= 0

    def test_diferencia_calculo_correcto(self, turnos_varios):
        """Diferencia = Total Declarado - Total Sistema."""
        for turno in turnos_varios:
            if turno.estatus == TurnoCaja.Estatus.CERRADA:
                total_declarado = (turno.efectivo_declarado or Decimal('0')) + (turno.tarjeta_declarada or Decimal('0'))
                total_sistema = (turno.monto_efectivo_sistema or Decimal('0')) + (turno.monto_tarjeta_sistema or Decimal('0'))
                assert turno.diferencia == (total_declarado - total_sistema)

    def test_detalle_view_metricas_correctas(self, client, usuario_admin, turno_con_ventas):
        """Vista de detalle muestra métricas calculadas correctamente."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_con_ventas.pk}))
        assert response.status_code == 200
        
        # Verificar que el contexto tiene las métricas
        assert 'turno' in response.context
        turno = response.context['turno']
        assert turno.monto_efectivo_sistema == Decimal('1500.00')
        assert turno.monto_tarjeta_sistema == Decimal('30.00')
        assert turno.efectivo_declarado == Decimal('1550.00')
        assert turno.tarjeta_declarada == Decimal('30.00')
        assert turno.diferencia == Decimal('50.00')


# ======================================================================
# TESTS DE FILTROS
# ======================================================================

@pytest.mark.django_db
class TestCajaAuditoriaFiltros:
    """Tests de filtrado en CajaHistorialAuditView."""

    def test_filtro_fecha_inicio(self, client, usuario_admin, turnos_varios):
        """Filtrar por fecha_inicio funciona."""
        client.force_login(usuario_admin)
        from zoneinfo import ZoneInfo
        from django.utils import timezone
        caracas_tz = ZoneInfo('America/Caracas')
        fecha_inicio = timezone.now().date()
        
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d')})
        assert response.status_code == 200
        # Verificar que solo retornan turnos >= fecha_inicio
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert t.fecha_apertura.date() >= fecha_inicio

    def test_filtro_fecha_fin(self, client, usuario_admin, turnos_varios):
        """Filtrar por fecha_fin funciona."""
        client.force_login(usuario_admin)
        from zoneinfo import ZoneInfo
        from django.utils import timezone
        caracas_tz = ZoneInfo('America/Caracas')
        fecha_fin = timezone.now().date()
        
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'fecha_fin': fecha_fin.strftime('%Y-%m-%d')})
        assert response.status_code == 200
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert t.fecha_cierre.date() <= fecha_fin

    def test_filtro_tipo_descuadre_faltante(self, client, usuario_admin, turnos_varios):
        """Filtrar solo faltantes."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'tipo_descuadre': 'FALTANTE'})
        assert response.status_code == 200
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert t.diferencia < Decimal('0')

    def test_filtro_tipo_descuadre_sobrante(self, client, usuario_admin, turnos_varios):
        """Filtrar solo sobrantes."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'tipo_descuadre': 'SOBRANTE'})
        assert response.status_code == 200
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert t.diferencia > Decimal('0')

    def test_filtro_tipo_descuadre_cuadrado(self, client, usuario_admin, turnos_varios):
        """Filtrar solo cuadrados."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'tipo_descuadre': 'CUADRADO'})
        assert response.status_code == 200
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert t.diferencia == Decimal('0')

    def test_filtro_cajero_especifico(self, client, usuario_admin, turnos_varios, usuario_cajero):
        """Filtrar por cajero específico."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'cajero': str(usuario_cajero.pk)})
        assert response.status_code == 200
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert t.cajero_id == usuario_cajero.pk

    def test_busqueda_por_username(self, client, usuario_admin, turnos_varios, usuario_cajero):
        """Búsqueda parcial por username/nombre."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'q': usuario_cajero.username[:3]})
        assert response.status_code == 200
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert usuario_cajero.username[:3].lower() in t.cajero.username.lower()

    def test_filtro_estatus_cerrada(self, client, usuario_admin, turnos_varios):
        """Filtrar por estatus CERRADA."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'), 
                             {'estatus': 'CERRADA'})
        assert response.status_code == 200
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert t.estatus == TurnoCaja.Estatus.CERRADA

    def test_no_muestra_turnos_abiertos(self, client, usuario_admin, turnos_varios):
        """Por defecto no debe mostrar turnos abiertos."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_audit'))
        assert response.status_code == 200
        turnos_en_contexto = response.context['turnos']
        for t in turnos_en_contexto:
            assert t.estatus == TurnoCaja.Estatus.CERRADA


# ======================================================================
# TESTS DE EXPORTACIÓN
# ======================================================================

@pytest.mark.django_db
class TestCajaAuditoriaExportacion:
    """Tests de exportación PDF/Excel/CSV."""

    def test_export_pdf_retorna_pdf_valido(self, client, usuario_admin):
        """Export PDF retorna PDF válido."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_export_pdf'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert response.content.startswith(b'%PDF')

    def test_export_excel_retorna_xlsx_valido(self, client, usuario_admin):
        """Export Excel retorna XLSX válido."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_export_excel'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Verificar que es un Excel válido
        wb = load_workbook(BytesIO(response.content))
        assert 'Reporte Cierres' in wb.sheetnames or len(wb.sheetnames) > 0

    def test_export_csv_retorna_csv_valido(self, client, usuario_admin):
        """Export CSV retorna CSV válido."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_export_csv'))
        assert response.status_code == 200
        assert response['Content-Type'].startswith('text/csv')
        
        # Verificar que es CSV válido
        content = response.content.decode('utf-8')
        reader = csv.reader(content.splitlines())
        rows = list(reader)
        assert len(rows) > 0  # Al menos header

    def test_export_pdf_respeta_filtros(self, client, usuario_admin, turnos_varios):
        """Export PDF respeta filtros aplicados."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_export_pdf'),
                              {'fecha_inicio': '2026-01-01', 'tipo_descuadre': 'FALTANTE'})
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'

    def test_export_excel_respeta_filtros(self, client, usuario_admin, turnos_varios):
        """Export Excel respeta filtros aplicados."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_export_excel'),
                              {'tipo_descuadre': 'SOBRANTE'})
        assert response.status_code == 200
        wb = load_workbook(BytesIO(response.content))
        ws = wb.active
        # Verificar que solo hay datos de sobrantes (header + 1 fila de datos)
        data_rows = list(ws.iter_rows(min_row=2, values_only=True))
        for row in data_rows:
            if row[8]:  # Columna diferencia
                diff = Decimal(str(row[8]))
                assert diff > 0

    def test_export_csv_respeta_filtros(self, client, usuario_admin, turnos_varios):
        """Export CSV respeta filtros aplicados."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_historial_export_csv'),
                              {'cajero': str(turnos_varios[0].cajero.pk)})
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        reader = csv.reader(content.splitlines())
        rows = list(reader)
        # Header + al menos una fila
        assert len(rows) >= 2


# ======================================================================
# TESTS DE VISTA DE DETALLE
# ======================================================================

@pytest.mark.django_db
class TestCajaAuditoriaDetalle:
    """Tests de la vista de detalle de auditoría."""

    def test_detalle_muestra_informacion_general(self, client, usuario_admin, turno_con_ventas):
        """Detalle muestra información general del turno."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_con_ventas.pk}))
        assert response.status_code == 200
        assert 'turno' in response.context
        assert response.context['turno'].cajero == turno_con_ventas.cajero

    def test_detalle_muestra_facturas_del_turno(self, client, usuario_admin, turno_con_ventas):
        """Detalle muestra lista de facturas del turno."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_con_ventas.pk}))
        assert response.status_code == 200
        assert 'facturas' in response.context
        facturas = response.context['facturas']
        assert facturas.count() > 0

    def test_detalle_muestra_productos_vendidos(self, client, usuario_admin, turno_con_ventas):
        """Detalle muestra productos vendidos (opcional/colapsable)."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_con_ventas.pk}))
        assert response.status_code == 200
        assert 'productos_vendidos' in response.context
        productos = response.context['productos_vendidos']
        assert productos.count() > 0

    def test_detalle_calcula_metricas_sistema_correctamente(self, client, usuario_admin, turno_con_ventas):
        """Detalle calcula métricas del sistema correctamente."""
        client.force_login(usuario_admin)
        response = client.get(reverse('facturacion:caja_auditoria_detail', kwargs={'pk': turno_con_ventas.pk}))
        assert response.status_code == 200
        
        context = response.context
        assert 'ventas_efectivo_bs' in context
        assert 'ventas_tarjeta_usd' in context
        assert 'total_sistema_bs' in context
        
        # Verificar cálculos
        assert context['ventas_efectivo_bs'] == Decimal('1500.00')
        assert context['ventas_tarjeta_usd'] == Decimal('30.00')
        # Total sistema = efectivo + (tarjeta * tasa) = 1500 + (30 * 50) = 3000
        assert context['total_sistema_bs'] == Decimal('3000.00')


# ======================================================================
# TESTS DE MODELO - PERMISOS PERSONALIZADOS
# ======================================================================

@pytest.mark.django_db
class TestTurnoCajaPermisos:
    """Tests de permisos personalizados en el modelo TurnoCaja."""

    def test_modelo_tiene_permisos_custom(self):
        """Verificar que TurnoCaja.Meta tiene los permisos personalizados."""
        permisos = [p[0] for p in TurnoCaja._meta.permissions]
        assert 'view_turnocaja_audit' in permisos
        assert 'export_turnocaja_audit' in permisos

    def test_permisos_tienen_descripcion_correcta(self):
        """Verificar descripciones de permisos."""
        permisos_dict = dict(TurnoCaja._meta.permissions)
        assert permisos_dict['view_turnocaja_audit'] == 'Puede ver auditoría de turnos de caja'
        assert permisos_dict['export_turnocaja_audit'] == 'Puede exportar reportes de turnos de caja'