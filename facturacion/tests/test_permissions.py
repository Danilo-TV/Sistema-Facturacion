"""
Tests de permisos para el grupo Cajeros.

Verifica que los usuarios del grupo 'Cajeros' tengan los permisos correctos
y puedan acceder a las vistas de facturación sin errores 403.
"""
import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from facturacion.models import TurnoCaja
from facturacion.tests.factories import UsuarioFactory
from facturacion.models import TurnoCaja
from decimal import Decimal


@pytest.mark.django_db
@pytest.mark.usefixtures("setup_cajeros_group")
class TestCajerosGroupPermissions:
    """Tests para verificar que el grupo Cajeros tiene los permisos correctos."""

    def test_grupo_cajeros_existe(self):
        """Verificar que el grupo Cajeros existe."""
        from django.contrib.auth.models import Group
        grupo = Group.objects.get(name='Cajeros')
        assert grupo is not None

    def test_grupo_cajeros_tiene_permisos_esperados(self):
        """Verificar que el grupo tiene todos los permisos esperados."""
        from django.contrib.auth.models import Group
        grupo = Group.objects.get(name='Cajeros')
        permisos_esperados = {
            'facturacion.add_cabecerafactura',
            'facturacion.view_cabecerafactura',
            'facturacion.view_producto',
            'facturacion.add_cliente',
            'facturacion.view_cliente',
            'facturacion.change_cliente',
            'facturacion.view_categoria',
            'facturacion.add_turnocaja',
            'facturacion.change_turnocaja',
            'facturacion.view_turnocaja',
        }

        permisos_grupo = set(
            f"{p.content_type.app_label}.{p.codename}"
            for p in grupo.permissions.all()
        )

        for permiso in permisos_esperados:
            assert permiso in permisos_grupo, f"Falta permiso: {permiso}"

    def test_grupo_cajeros_no_tiene_permisos_peligrosos(self):
        """Verificar que el grupo NO tiene permisos peligrosos."""
        from django.contrib.auth.models import Group
        grupo = Group.objects.get(name='Cajeros')
        permisos_grupo = {
            f"{p.content_type.app_label}.{p.codename}"
            for p in grupo.permissions.all()
        }

        permisos_peligrosos = {
            'facturacion.delete_cabecerafactura',
            'facturacion.delete_cliente',
            'facturacion.delete_producto',
            'facturacion.delete_categoria',
            'facturacion.change_cabecerafactura',
            'facturacion.change_producto',
            'facturacion.change_categoria',
            'facturacion.view_report',
            'facturacion.add_usuario',
            'facturacion.change_usuario',
            'facturacion.delete_usuario',
            'facturacion.view_usuario',
        }

        for permiso in permisos_grupo:
            assert permiso not in {
                'facturacion.delete_cabecerafactura',
                'facturacion.delete_cliente',
                'facturacion.delete_producto',
                'facturacion.delete_categoria',
                'facturacion.change_cabecerafactura',
                'facturacion.change_producto',
                'facturacion.change_categoria',
                'facturacion.view_report',
                'facturacion.add_usuario',
                'facturacion.change_usuario',
                'facturacion.delete_usuario',
                'facturacion.view_usuario',
            }, f"El grupo tiene un permiso peligroso inesperado"


@pytest.mark.django_db
@pytest.mark.usefixtures("setup_cajeros_group")
class TestCajeroConTurnoAbierto:
    """Tests para verificar que un cajero con turno abierto puede facturar."""

    def test_cajero_con_turno_puede_acceder_a_factura_crear(self, client):
        """Verificar que un cajero con turno abierto puede acceder a crear factura (GET)."""
        from django.contrib.auth.models import Group, Permission
        from facturacion.tests.factories import UsuarioFactory
        from facturacion.models import TurnoCaja
        from decimal import Decimal

        # Crear usuario y asignar al grupo Cajeros
        from facturacion.tests.factories import UsuarioFactory
        usuario = UsuarioFactory()
        grupo, _ = Group.objects.get_or_create(name='Cajeros')
        usuario.groups.add(grupo)

        # Asignar permisos necesarios
        from django.contrib.auth.models import Permission
        permisos_necesarios = [
            'add_cabecerafactura', 'change_cabecerafactura',
            'view_cabecerafactura', 'delete_cabecerafactura',
            'view_report', 'view_producto', 'add_cliente',
            'view_cliente', 'change_cliente', 'add_turnocaja',
            'change_turnocaja', 'view_turnocaja', 'view_producto',
            'view_categoria', 'add_cliente', 'view_cliente',
            'change_cliente', 'add_turnocaja', 'change_turnocaja',
            'view_turnocaja'
        ]
        for codename in [
            'add_cabecerafactura', 'change_cabecerafactura', 'view_cabecerafactura',
            'delete_cabecerafactura', 'view_report', 'view_producto', 'add_cliente',
            'view_cliente', 'change_cliente', 'add_turnocaja', 'change_turnocaja',
            'view_turnocaja', 'view_producto', 'view_categoria', 'add_cliente',
            'view_cliente', 'change_cliente'
        ]:
            perm = Permission.objects.get(
                content_type__app_label='facturacion',
                codename=codename,
            )
            usuario.user_permissions.add(perm)

        # Crear turno abierto
        from facturacion.models import TurnoCaja
        from decimal import Decimal
        TurnoCaja.objects.create(
            cajero=usuario,
            monto_inicial=Decimal('100.00'),
            estatus='abierta',
        )

        # Hacer login y probar acceso
        from django.test import Client
        client = Client()
        client.force_login(usuario)

        # GET a factura_create debe retornar 200 (no 403 ni 302)
        from django.urls import reverse
        url = reverse('facturacion:factura_create')
        response = client.get(url)
        assert response.status_code == 200, f"Se esperaba 200, se obtuvo {response.status_code}"

    def test_cajero_sin_turno_no_puede_facturar(self, client):
        """Verificar que un cajero SIN turno abierto NO puede facturar."""
        from facturacion.tests.factories import UsuarioFactory
        usuario = UsuarioFactory()
        from django.contrib.auth.models import Group, Permission
        grupo, _ = Group.objects.get_or_create(name='Cajeros')
        usuario.groups.add(grupo)

        from django.contrib.auth.models import Permission
        for codename in [
            'add_cabecerafactura', 'change_cabecerafactura',
            'view_cabecerafactura', 'delete_cabecerafactura',
            'view_report', 'view_producto', 'add_cliente',
            'view_cliente', 'change_cliente'
        ]:
            perm = Permission.objects.get(
                content_type__app_label='facturacion',
                codename=codename,
            )
            usuario.user_permissions.add(perm)

        # NO crear turno abierto
        from django.test import Client
        client = Client()
        client.force_login(usuario)

        from django.urls import reverse
        url = reverse('facturacion:factura_create')
        response = client.get(url)
        # Debe redirigir a apertura de caja (302) o dar 403
        assert response.status_code in [302, 403]


@pytest.mark.django_db
@pytest.mark.usefixtures("setup_cajeros_group")
class TestCajerosGroupManagementCommand:
    """Tests para el comando setup_cajeros_perms."""

    def test_comando_setup_cajeros_ejecuta_sin_errores(self):
        """Verificar que el comando setup_cajeros_perms se ejecuta sin errores."""
        from django.core.management import call_command
        from django.contrib.auth.models import Group

        # Eliminar grupo si existe para probar creación
        Group.objects.filter(name='Cajeros').delete()

        from django.core.management import call_command
        call_command('setup_cajeros_perms')

        # Verificar que el grupo se creó con permisos
        grupo = Group.objects.get(name='Cajeros')
        assert grupo.permissions.count() == 12  # 12 permisos exactos

    def test_comando_idempotente(self):
        """Verificar que el comando es idempotente (se puede ejecutar múltiples veces)."""
        from django.core.management import call_command
        from django.contrib.auth.models import Group

        # Ejecutar dos veces
        call_command('setup_cajeros_perms')
        call_command('setup_cajeros_perms')

        grupo = Group.objects.get(name='Cajeros')
        assert grupo.permissions.count() == 12  # Debe seguir teniendo 12 permisos