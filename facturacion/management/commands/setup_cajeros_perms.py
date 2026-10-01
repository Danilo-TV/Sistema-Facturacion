"""
Comando para configurar los permisos del grupo 'Cajeros'.

Uso:
    python manage.py setup_cajeros_perms

Este comando es idempotente (seguro de ejecutar múltiples veces).
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from facturacion.models import (
    CabeceraFactura,
    Categoria,
    Cliente,
    DetalleVenta,
    Producto,
    TurnoCaja,
)


class Command(BaseCommand):
    help = 'Configura los permisos exactos para el grupo "Cajeros".'

    # Permisos EXACTOS que debe tener el grupo Cajeros
    PERMISOS_CAJEROS = [
        'add_cabecerafactura',
        'view_cabecerafactura',
        'add_detalleventa',
        'view_detalleventa',
        'add_cliente',
        'view_cliente',
        'change_cliente',
        'view_producto',
        'view_categoria',
        'add_turnocaja',
        'change_turnocaja',
        'view_turnocaja',
    ]

    def handle(self, *args, **options):
        # 1. Obtener o crear el grupo 'Cajeros'
        group, created = Group.objects.get_or_create(name='Cajeros')

        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Cajeros" creado'))
        else:
            self.stdout.write('Grupo "Cajeros" ya existe')

        # 2. Obtener los objetos Permission para cada permiso requerido
        permisos_a_asignar = []
        modelos_permisos = {
            'cabecerafactura': CabeceraFactura,
            'detalleventa': DetalleVenta,
            'cliente': Cliente,
            'producto': Producto,
            'categoria': Categoria,
            'turnocaja': TurnoCaja,
        }

        for perm_codename in self.PERMISOS_CAJEROS:
            # Extraer modelo del codename (formato: action_modelo)
            parts = perm_codename.split('_', 1)
            if len(parts) != 2:
                self.stdout.write(self.style.WARNING(f'  ⚠ Formato de permiso inesperado: {perm_codename}'))
                continue

            action, modelo_nombre = parts
            modelo = modelos_permisos.get(modelo_nombre)

            if not modelo:
                self.stdout.write(self.style.WARNING(f'  ⚠ Modelo no encontrado para: {perm_codename}'))
                continue

            content_type = ContentType.objects.get_for_model(modelo)

            try:
                permiso = Permission.objects.get(
                    content_type=content_type,
                    codename=perm_codename,
                )
                permisos_a_asignar.append(permiso)
                self.stdout.write(f'  ✓ Permiso encontrado: {perm_codename}')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ✗ Permiso NO existe: {perm_codename}'))

        # 3. Asignar EXACTAMENTE estos permisos (reemplaza los existentes)
        group.permissions.set(permisos_a_asignar)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Grupo "Cajeros" configurado con {len(permisos_a_asignar)} permisos exactos.'
            )
        )

        # 4. Mostrar permisos asignados para verificación
        self.stdout.write('\nPermisos actuales del grupo:')
        for perm in group.permissions.all().order_by('content_type__model', 'codename'):
            self.stdout.write(f'  - {perm.content_type.app_label}.{perm.codename}')

        # 5. Advertir si hay permisos "peligrosos" que NO deberían estar
        permisos_peligrosos = [
            'delete_',
            'change_cabecerafactura',
            'change_detalleventa',
            'change_producto',
            'change_categoria',
            'view_report',
            'add_usuario',
            'change_usuario',
            'delete_usuario',
            'view_usuario',
        ]

        self.stdout.write('\nVerificación de permisos NO asignados (deberían estar ausentes):')
        for perm in group.permissions.all():
            for peligroso in permisos_peligrosos:
                if peligroso in perm.codename:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ ATENCIÓN: Permiso potencialmente no deseado: {perm.codename}'
                        )
                    )

        self.stdout.write(self.style.SUCCESS('\n✅ Comando completado exitosamente.'))