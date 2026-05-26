import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models, transaction
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy

from weasyprint import HTML
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .models import (
    CabeceraFactura,
    Categoria,
    Cliente,
    DetalleVenta,
    Producto,
    Usuario,
)


# ======================================================================
# DASHBOARD
# ======================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'facturacion/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_productos'] = Producto.objects.filter(is_active=True).count()
        context['total_clientes'] = Cliente.objects.filter(is_active=True).count()
        context['total_facturas'] = CabeceraFactura.objects.count()
        context['productos_stajo_bajo'] = (
            Producto.objects
            .filter(is_active=True, stock_actual__lte=models.F('stock_minimo'))
            .count()
        )
        context['ultimas_facturas'] = (
            CabeceraFactura.objects
            .select_related('cliente')
            .order_by('-fecha_emision')[:10]
        )
        return context


# ======================================================================
# PRODUCTO — CRUD
# ======================================================================

class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'facturacion/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 25
    ordering = ['nombre']

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('categoria')
            .only(
                'id', 'codigo', 'nombre', 'precio_bs', 'precio_usd',
                'stock_actual', 'stock_minimo', 'is_active',
                'categoria__nombre',
            )
        )


class ProductoCreateView(LoginRequiredMixin, CreateView):
    model = Producto
    template_name = 'facturacion/producto_form.html'
    fields = [
        'codigo', 'nombre', 'descripcion', 'categoria',
        'precio_bs', 'precio_usd', 'costo_bs',
        'stock_actual', 'stock_minimo',
        'permite_stock_negativo', 'is_active',
    ]
    success_url = reverse_lazy('facturacion:producto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nuevo Producto'
        context['icono'] = 'plus-circle'
        context['categorias'] = Categoria.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Producto creado exitosamente.')
        return super().form_valid(form)


class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    model = Producto
    template_name = 'facturacion/producto_form.html'
    fields = [
        'codigo', 'nombre', 'descripcion', 'categoria',
        'precio_bs', 'precio_usd', 'costo_bs',
        'stock_actual', 'stock_minimo',
        'permite_stock_negativo', 'is_active',
    ]
    success_url = reverse_lazy('facturacion:producto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Producto'
        context['icono'] = 'edit'
        context['categorias'] = Categoria.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Producto actualizado exitosamente.')
        return super().form_valid(form)


class ProductoDeleteView(LoginRequiredMixin, DeleteView):
    model = Producto
    template_name = 'facturacion/producto_confirm_delete.html'
    success_url = reverse_lazy('facturacion:producto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Producto eliminado exitosamente.')
        return super().form_valid(form)


# ======================================================================
# CLIENTE — CRUD
# ======================================================================

class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'facturacion/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 25
    ordering = ['nombre_razon_social']


class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    template_name = 'facturacion/cliente_form.html'
    fields = [
        'tipo_documento', 'numero_documento', 'nombre_razon_social',
        'direccion', 'telefono', 'email', 'is_active',
    ]
    success_url = reverse_lazy('facturacion:cliente_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nuevo Cliente'
        context['icono'] = '-plus'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    template_name = 'facturacion/cliente_form.html'
    fields = [
        'tipo_documento', 'numero_documento', 'nombre_razon_social',
        'direccion', 'telefono', 'email', 'is_active',
    ]
    success_url = reverse_lazy('facturacion:cliente_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Cliente'
        context['icono'] = '-edit'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)


# ======================================================================
# CATEGORÍA — CRUD
# ======================================================================

class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'facturacion/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['nombre']

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('categoria_padre')
            .only('id', 'nombre', 'descripcion', 'is_active', 'categoria_padre__nombre')
        )


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    template_name = 'facturacion/categoria_form.html'
    fields = ['nombre', 'descripcion', 'categoria_padre', 'is_active']
    success_url = reverse_lazy('facturacion:categoria_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nueva Categoría'
        context['categorias'] = Categoria.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Categoría creada exitosamente.')
        return super().form_valid(form)


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    template_name = 'facturacion/categoria_form.html'
    fields = ['nombre', 'descripcion', 'categoria_padre', 'is_active']
    success_url = reverse_lazy('facturacion:categoria_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Categoría'
        context['categorias'] = Categoria.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Categoría actualizada exitosamente.')
        return super().form_valid(form)


# ======================================================================
# FACTURA — CRUD
# ======================================================================

class FacturaListView(LoginRequiredMixin, ListView):
    model = CabeceraFactura
    template_name = 'facturacion/factura_list.html'
    context_object_name = 'facturas'
    paginate_by = 25
    ordering = ['-fecha_emision']

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('cliente')
            .only(
                'id', 'numero_factura', 'fecha_emision', 'tipo_documento',
                'moneda_principal', 'total_bs', 'total_usd', 'estatus',
                'cliente__nombre_razon_social',
            )
        )


class FacturaDetailView(LoginRequiredMixin, DetailView):
    model = CabeceraFactura
    template_name = 'facturacion/factura_detail.html'
    context_object_name = 'factura'

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('cliente', 'usuario')
            .prefetch_related('detalles__producto')
        )


class FacturaPdfView(LoginRequiredMixin, DetailView):
    """Genera un PDF de la factura usando WeasyPrint."""

    model = CabeceraFactura

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('cliente', 'usuario')
            .prefetch_related('detalles__producto')
        )

    def get(self, request, *args, **kwargs):
        factura = self.get_object()
        context = {
            'factura': factura,
            'detalles': factura.detalles.all(),
            'cliente': factura.cliente,
            'usuario': factura.usuario,
        }
        html_string = render_to_string('facturacion/factura_pdf.html', context, request)
        pdf_file = HTML(string=html_string).write_pdf(base_url=request.build_absolute_uri())

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="factura_{factura.numero_factura}.pdf"'
        )
        return response


class FacturaCreateView(LoginRequiredMixin, TemplateView):
    """Vista principal de creación de facturas.

    GET  → Renderiza el formulario vacío con DataTables y Select2.
    POST → Recibe JSON con los datos completos, valida y crea la factura.
    """
    template_name = 'facturacion/factura_form.html'

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)

        # --- Validar campos requeridos ---
        cliente_id = data.get('cliente')
        tasa_cambio = data.get('tasa_cambio')
        moneda_principal = data.get('moneda_principal', 'bs')
        tipo_documento = data.get('tipo_documento', 'factura')
        observaciones = data.get('observaciones', '')
        detalles_data = data.get('detalles', [])

        if not cliente_id:
            return JsonResponse({'success': False, 'error': 'Debe seleccionar un cliente.'}, status=400)
        if not tasa_cambio or Decimal(str(tasa_cambio)) <= 0:
            return JsonResponse({'success': False, 'error': 'Tasa de cambio inválida.'}, status=400)
        if not detalles_data:
            return JsonResponse({'success': False, 'error': 'Debe agregar al menos un producto.'}, status=400)

        tasa_cambio = Decimal(str(tasa_cambio))

        # --- Validar cliente ---
        try:
            cliente = Cliente.objects.get(pk=cliente_id, is_active=True)
        except Cliente.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cliente no encontrado.'}, status=404)

        # --- Generar número de factura ---
        hoy = timezone.now()
        ultima = (
            CabeceraFactura.objects
            .filter(fecha_emision__date=hoy.date())
            .order_by('-numero_factura')
            .first()
        )
        if ultima:
            try:
                correlativo = int(ultima.numero_factura.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1
        numero_factura = f"FAC-{hoy.strftime('%Y%m%d')}-{correlativo:04d}"

        # --- Procesar detalles con validación ---
        detalles_validados = []
        total_sub_bs = Decimal('0')
        total_sub_usd = Decimal('0')
        total_iva_bs = Decimal('0')
        total_iva_usd = Decimal('0')
        total_desc_bs = Decimal('0')
        total_desc_usd = Decimal('0')
        total_gral_bs = Decimal('0')
        total_gral_usd = Decimal('0')

        for idx, det in enumerate(detalles_data):
            producto_id = det.get('producto_id')
            cantidad = det.get('cantidad', 0)

            try:
                cantidad = int(cantidad)
            except (TypeError, ValueError):
                return JsonResponse(
                    {'success': False, 'error': f'Detalle #{idx + 1}: cantidad inválida.'}, status=400
                )
            if cantidad <= 0:
                return JsonResponse(
                    {'success': False, 'error': f'Detalle #{idx + 1}: la cantidad debe ser mayor a cero.'}, status=400
                )

            try:
                producto = Producto.objects.get(pk=producto_id, is_active=True)
            except Producto.DoesNotExist:
                return JsonResponse(
                    {'success': False, 'error': f'Detalle #{idx + 1}: producto no encontrado.'}, status=404
                )

            # Validar stock (estricto)
            if not producto.permite_stock_negativo and cantidad > producto.stock_actual:
                return JsonResponse({
                    'success': False,
                    'error': (
                        f'Stock insuficiente para "{producto.nombre}". '
                        f'Disponible: {producto.stock_actual}, solicitado: {cantidad}.'
                    ),
                }, status=400)

            # Tomar precios del producto (snapshot histórico)
            precio_bs = producto.precio_bs
            precio_usd = (precio_bs / tasa_cambio).quantize(Decimal('0.01'))

            # Calcular montos (re-calculo del lado del servidor, siempre fuente de verdad)
            descuento_bs = Decimal(str(det.get('descuento_bs', 0)))
            if descuento_bs < 0:
                descuento_bs = Decimal('0')

            subtotal_bs = cantidad * precio_bs
            subtotal_usd = cantidad * precio_usd

            # Validar descuento máximo 20%
            desc_max = (subtotal_bs * Decimal('0.20')).quantize(Decimal('0.01'))
            if descuento_bs > desc_max:
                return JsonResponse({
                    'success': False,
                    'error': (
                        f'Detalle #{idx + 1}: descuento excede el 20% '
                        f'(máx: {desc_max} Bs).'
                    ),
                }, status=400)

            base_imponible_bs = subtotal_bs - descuento_bs
            base_imponible_usd = subtotal_usd - (descuento_bs / tasa_cambio).quantize(Decimal('0.01'))

            iva_bs = (base_imponible_bs * DetalleVenta.IVA).quantize(Decimal('0.01'))
            iva_usd = (base_imponible_usd * DetalleVenta.IVA).quantize(Decimal('0.01'))

            total_bs = (base_imponible_bs + iva_bs).quantize(Decimal('0.01'))
            total_usd = (base_imponible_usd + iva_usd).quantize(Decimal('0.01'))

            # Acumular totales
            total_sub_bs += subtotal_bs
            total_sub_usd += subtotal_usd
            total_desc_bs += descuento_bs
            total_desc_usd += (descuento_bs / tasa_cambio).quantize(Decimal('0.01'))
            total_iva_bs += iva_bs
            total_iva_usd += iva_usd
            total_gral_bs += total_bs
            total_gral_usd += total_usd

            detalles_validados.append({
                'producto': producto,
                'cantidad': cantidad,
                'precio_unitario_bs': precio_bs,
                'precio_unitario_usd': precio_usd,
                'descuento_bs': descuento_bs,
                'subtotal_bs': subtotal_bs,
                'subtotal_usd': subtotal_usd,
                'monto_iva_bs': iva_bs,
                'monto_iva_usd': iva_usd,
                'total_bs': total_bs,
                'total_usd': total_usd,
            })

        # --- Crear factura (transacción atómica) ---
        try:
            with transaction.atomic():
                factura = CabeceraFactura.objects.create(
                    numero_factura=numero_factura,
                    cliente=cliente,
                    usuario=request.user,
                    tipo_documento=tipo_documento,
                    estatus=CabeceraFactura.Estatus.PAGADA,
                    tasa_cambio=tasa_cambio,
                    moneda_principal=moneda_principal,
                    subtotal_bs=total_sub_bs.quantize(Decimal('0.01')),
                    subtotal_usd=total_sub_usd.quantize(Decimal('0.01')),
                    monto_iva_bs=total_iva_bs.quantize(Decimal('0.01')),
                    monto_iva_usd=total_iva_usd.quantize(Decimal('0.01')),
                    descuento_bs=total_desc_bs.quantize(Decimal('0.01')),
                    descuento_usd=total_desc_usd.quantize(Decimal('0.01')),
                    total_bs=total_gral_bs.quantize(Decimal('0.01')),
                    total_usd=total_gral_usd.quantize(Decimal('0.01')),
                    observaciones=observaciones,
                )

                # Crear DetalleVenta y descontar stock
                for det in detalles_validados:
                    DetalleVenta.objects.create(
                        cabecera=factura,
                        producto=det['producto'],
                        cantidad=det['cantidad'],
                        precio_unitario_bs=det['precio_unitario_bs'],
                        precio_unitario_usd=det['precio_unitario_usd'],
                        subtotal_bs=det['subtotal_bs'],
                        subtotal_usd=det['subtotal_usd'],
                        monto_iva_bs=det['monto_iva_bs'],
                        monto_iva_usd=det['monto_iva_usd'],
                        total_bs=det['total_bs'],
                        total_usd=det['total_usd'],
                    )

                    # Descontar stock (solo si la factura se crea como pagada)
                    producto = det['producto']
                    producto.stock_actual -= det['cantidad']
                    producto.save(update_fields=['stock_actual'])

            return JsonResponse({
                'success': True,
                'redirect_url': reverse('facturacion:factura_detail', kwargs={'pk': factura.pk}),
                'numero_factura': factura.numero_factura,
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al crear la factura: {str(e)}',
            }, status=500)


# ======================================================================
# AJAX — SELECT2 SEARCH
# ======================================================================

class ClienteSearchAJAXView(LoginRequiredMixin, View):
    """Endpoint para Select2: busca clientes por nombre o documento."""

    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        if len(q) < 2:
            return JsonResponse({'items': []})

        clientes = Cliente.objects.filter(is_active=True).filter(
            models.Q(nombre_razon_social__icontains=q) |
            models.Q(numero_documento__icontains=q)
        ).only('id', 'nombre_razon_social', 'tipo_documento', 'numero_documento')[:15]

        items = [
            {
                'id': str(c.pk),
                'text': f'{c.nombre_razon_social} — {c.get_tipo_documento_display()}: {c.numero_documento}',
            }
            for c in clientes
        ]

        return JsonResponse({'items': items})


class ProductoSearchAJAXView(LoginRequiredMixin, View):
    """Endpoint para Select2: busca productos por código o nombre."""

    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        if len(q) < 1:
            return JsonResponse({'items': []})

        productos = Producto.objects.filter(is_active=True).filter(
            models.Q(codigo__icontains=q) |
            models.Q(nombre__icontains=q)
        ).only(
            'id', 'codigo', 'nombre', 'precio_bs', 'precio_usd',
            'stock_actual', 'permite_stock_negativo',
        )[:15]

        items = [
            {
                'id': str(p.pk),
                'text': f'{p.codigo} — {p.nombre} (Bs {p.precio_bs:.2f})',
                'precio_bs': float(p.precio_bs),
                'precio_usd': float(p.precio_usd),
                'stock_actual': p.stock_actual,
                'permite_stock_negativo': p.permite_stock_negativo,
            }
            for p in productos
        ]

        return JsonResponse({'items': items})


# ======================================================================
# DASHBOARD — AJAX DATA
# ======================================================================

class DashboardDataAJAXView(LoginRequiredMixin, View):
    """Endpoint JSON para el dashboard interactivo.

    GET → devuelve:
      - monthly_sales: [{month: '2026-01', total: 1234.56}, ...]
      - top_products:  [{name: 'Producto X', y: 45.2}, ...]
    """

    def get(self, request, *args, **kwargs):
        # --- Ventas agrupadas por mes ---
        monthly_qs = (
            CabeceraFactura.objects
            .filter(estatus=CabeceraFactura.Estatus.PAGADA)
            .annotate(month=TruncMonth('fecha_emision'))
            .values('month')
            .annotate(total=Sum('total_bs'))
            .order_by('month')
        )

        monthly_sales = [
            {
                'month': entry['month'].strftime('%Y-%m') if entry['month'] else None,
                'total': float(entry['total']),
            }
            for entry in monthly_qs
        ]

        # --- Top productos por cantidad vendida ---
        top_qs = (
            DetalleVenta.objects
            .values('producto__nombre')
            .annotate(total_qty=Sum('cantidad'))
            .order_by('-total_qty')[:10]
        )

        total_qty_all = sum(entry['total_qty'] for entry in top_qs) or 1

        top_products = [
            {
                'name': entry['producto__nombre'] or 'Sin nombre',
                'y': round(float(entry['total_qty']) / total_qty_all * 100, 1),
            }
            for entry in top_qs
        ]

        return JsonResponse({
            'monthly_sales': monthly_sales,
            'top_products': top_products,
        })


# ======================================================================
# REPORTES
# ======================================================================

class ReportSaleView(LoginRequiredMixin, TemplateView):
    template_name = 'facturacion/report.html'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'search_report':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            # Filter pagadas only by default
            queryset = CabeceraFactura.objects.filter(
                estatus='pagada',
                fecha_emision__date__gte=start_date,
                fecha_emision__date__lte=end_date,
            ).select_related('cliente')

            # Aggregate totals
            totals = queryset.aggregate(
                subtotal_usd=Sum('subtotal_usd'),
                monto_iva_usd=Sum('monto_iva_usd'),
                total_usd=Sum('total_usd'),
            )

            data = []
            for f in queryset:
                data.append({
                    'numero': f.numero_factura,
                    'fecha': f.fecha_emision.strftime('%d/%m/%Y'),
                    'cliente': f.cliente.nombre_razon_social,
                    'tipo': f.get_tipo_documento_display(),
                    'total_bs': float(f.total_bs),
                    'total_usd': float(f.total_usd),
                    'estatus': f.get_estatus_display(),
                })

            return JsonResponse({
                'data': data,
                'totals': {
                    'subtotal_usd': float(totals['subtotal_usd'] or 0),
                    'monto_iva_usd': float(totals['monto_iva_usd'] or 0),
                    'total_usd': float(totals['total_usd'] or 0),
                },
            })

        return JsonResponse({'error': 'Acción no válida'}, status=400)
