from django.urls import path

from . import views

app_name = 'facturacion'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Productos
    path('productos/', views.ProductoListView.as_view(), name='producto_list'),
    path('productos/nuevo/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<uuid:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_edit'),
    path('productos/<uuid:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_delete'),

    # Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/nuevo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<uuid:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_edit'),

    # Categorías
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/nuevo/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<uuid:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_edit'),

    # Facturas
    path('facturas/', views.FacturaListView.as_view(), name='factura_list'),
    path('facturas/nueva/', views.FacturaCreateView.as_view(), name='factura_create'),
    path('facturas/<uuid:pk>/', views.FacturaDetailView.as_view(), name='factura_detail'),
    path('facturas/<uuid:pk>/pdf/', views.FacturaPdfView.as_view(), name='factura_pdf'),
    path('facturas/<uuid:pk>/ticket/', views.FacturaTicketView.as_view(), name='factura_ticket'),
    path('facturas/<uuid:pk>/email/', views.FacturaEmailView.as_view(), name='factura_email'),
    path('facturas/<uuid:pk>/eliminar/', views.FacturaDeleteView.as_view(), name='factura_delete'),

    # AJAX — Select2
    path('api/clientes/search/', views.ClienteSearchAJAXView.as_view(), name='cliente_search'),
    path('api/productos/search/', views.ProductoSearchAJAXView.as_view(), name='producto_search'),

    # Reportes
    path('reportes/', views.ReportSaleView.as_view(), name='report_sale'),

    # AJAX — Dashboard
    path('api/dashboard/data/', views.DashboardDataAJAXView.as_view(), name='dashboard_data'),

    # Usuarios
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    path('usuarios/<uuid:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_edit'),

    # Turno Caja — Apertura, Cierre y Historial
    path('caja/apertura/', views.AperturaCajaView.as_view(), name='apertura_caja'),
    path('caja/cierre/', views.CierreCajaView.as_view(), name='cierre_caja'),
    path('caja/historial/', views.HistorialCierresView.as_view(), name='historial_cierres'),
]
