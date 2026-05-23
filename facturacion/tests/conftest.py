import pytest

from facturacion.tests.factories import UsuarioFactory


@pytest.fixture
def usuario():
    """Retorna un usuario activo sin autenticar."""
    return UsuarioFactory()


@pytest.fixture
def cliente_autenticado(client, usuario):
    """Retorna un client de Django con sesión iniciada."""
    client.force_login(usuario)
    return client
