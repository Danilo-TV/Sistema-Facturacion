from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect


class ValidarPermisosMixin(AccessMixin):
    """Mixin que verifica autenticación y permisos antes de ejecutar la vista.

    Uso:
        class MiVista(ValidarPermisosMixin, LoginRequiredMixin, TemplateView):
            permission_required = ('facturacion.add_cabecerafactura',)
    """

    permission_required = []

    def dispatch(self, request, *args, **kwargs):
        # 1. Verificar autenticación
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2. Verificar permisos si están definidos
        if self.permission_required:
            if not request.user.has_perms(self.permission_required):
                messages.error(
                    request,
                    'No tiene permiso para ingresar a este módulo',
                )
                return redirect('facturacion:dashboard')

        return super().dispatch(request, *args, **kwargs)
