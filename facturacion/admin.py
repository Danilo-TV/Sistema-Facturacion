from django.contrib import admin

from .models import (
    CabeceraFactura,
    Categoria,
    Cliente,
    DetalleVenta,
    Producto,
    Usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'rol', 'first_name', 'last_name', 'is_active']
    list_filter = ['rol', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']


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
