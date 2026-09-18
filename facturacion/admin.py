from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import (
    CabeceraFactura,
    Categoria,
    Cliente,
    DetalleVenta,
    Producto,
    Usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'rol', 'first_name', 'last_name', 'is_active']
    list_filter = ['rol', 'is_active', 'is_staff', 'is_superuser', 'groups']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    filter_horizontal = ['groups', 'user_permissions']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email', 'rol')}),
        (
            'Permisos',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'email', 'first_name', 'last_name', 'rol', 'password1', 'password2'),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        # Hash password if provided
        if 'password' in form.changed_data and obj.password:
            obj.set_password(obj.password)

        # Clear existing groups
        obj.groups.clear()

        # Assign group based on rol
        if obj.rol == Usuario.Rol.ADMIN:
            group, _ = Group.objects.get_or_create(name='Administrador')
            obj.groups.add(group)
            obj.is_staff = True
            obj.is_superuser = True
        elif obj.rol == Usuario.Rol.VENDEDOR:
            group, _ = Group.objects.get_or_create(name='Cajeros')
            obj.groups.add(group)
            obj.is_staff = False
            obj.is_superuser = False

        super().save_model(request, obj, form, change)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre_razon_social', 'tipo_documento', 'numero_documento', 'is_active']
    list_filter = ['tipo_documento', 'is_active']
    search_fields = ['nombre_razon_social', 'numero_documento']
    ordering = ['nombre_razon_social']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria_padre', 'is_active']
    list_filter = ['is_active']
    search_fields = ['nombre']
    ordering = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nombre', 'categoria', 'precio_bs', 'precio_usd',
        'stock_actual', 'stock_minimo', 'is_active',
    ]
    list_filter = ['categoria', 'is_active', 'permite_stock_negativo']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']


@admin.register(CabeceraFactura)
class CabeceraFacturaAdmin(admin.ModelAdmin):
    list_display = [
        'numero_factura', 'cliente', 'usuario', 'fecha_emision',
        'estatus', 'tipo_documento', 'total_bs', 'total_usd',
    ]
    list_filter = ['estatus', 'tipo_documento', 'moneda_principal', 'fecha_emision']
    search_fields = ['numero_factura', 'cliente__nombre_razon_social']
    ordering = ['-fecha_emision']
    date_hierarchy = 'fecha_emision'


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ['cabecera', 'producto', 'cantidad', 'precio_unitario_bs', 'total_bs']
    list_filter = ['cabecera__estatus']
    search_fields = ['cabecera__numero_factura', 'producto__nombre']