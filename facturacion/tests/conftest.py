import pytest
from django.contrib.auth.models import Permission

from facturacion.tests.factories import UsuarioFactory


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
def cliente_autenticado(client, usuario):
    """Retorna un client de Django con sesión iniciada."""
    client.force_login(usuario)
    return client
