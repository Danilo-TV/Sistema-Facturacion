import pytest
from django.contrib.auth.models import Permission

from facturacion.tests.factories import UsuarioFactory
from facturacion.models import TurnoCaja
from decimal import Decimal


def usuario_con_permisos(*codenames):
    """Crea un usuario con los permisos especificados de la app 'facturacion'."""
    user = UsuarioFactory()
    for codename in codenames:
        perm = Permission.objects.get(
            content_type__app_label='facturacion',
            codename=codename,
        )
        user.user_permissions.add(perm)
    return user


@pytest.fixture
def usuario():
    """Retorna un usuario activo sin autenticar."""
    return UsuarioFactory()


@pytest.fixture
def usuario_con_turno_abierto(usuario):
    """Crea un turno de caja abierto para el usuario y retorna el usuario."""
    TurnoCaja.objects.create(
        cajero=usuario,
        monto_inicial=Decimal('100.00'),
        estatus=TurnoCaja.Estatus.ABIERTA,
    )
    return usuario


@pytest.fixture
def cliente_autenticado(client, usuario):
    """Retorna un client de Django con sesión iniciada."""
    client.force_login(usuario)
    return client


@pytest.fixture
def cliente_autenticado_con_turno(client, usuario):
    """Retorna un client de Django con sesión iniciada y turno de caja abierto (con permisos)."""
    # Agregar permisos necesarios
    for codename in ['add_cabecerafactura', 'change_cabecerafactura', 'view_cabecerafactura', 'delete_cabecerafactura', 'view_report']:
        perm = Permission.objects.get(
            content_type__app_label='facturacion',
            codename=codename,
        )
        usuario.user_permissions.add(perm)
    
    TurnoCaja.objects.create(
        cajero=usuario,
        monto_inicial=Decimal('100.00'),
        estatus=TurnoCaja.Estatus.ABIERTA,
    )
    client.force_login(usuario)
    return client
