import uuid
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


# ---------------------------------------------------------------------------
# 1. Usuario — modelo de autenticación personalizado
# ---------------------------------------------------------------------------

class Usuario(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    class Rol(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        VENDEDOR = 'vendedor', 'Vendedor'
        CONTADOR = 'contador', 'Contador'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.VENDEDOR,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['rol']),
        ]

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_rol_display()})'


# ---------------------------------------------------------------------------
# 2. Cliente
# ---------------------------------------------------------------------------

class Cliente(models.Model):

    class TipoDocumento(models.TextChoices):
        RIF = 'rif', 'RIF'
        CEDULA = 'cedula', 'Cédula'
        PASAPORTE = 'pasaporte', 'Pasaporte'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
    )
    numero_documento = models.CharField(max_length=20)
    nombre_razon_social = models.CharField(max_length=200)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        unique_together = ['tipo_documento', 'numero_documento']
        indexes = [
            models.Index(fields=['tipo_documento', 'numero_documento']),
            models.Index(fields=['nombre_razon_social']),
        ]

    def clean(self):
        if self.tipo_documento == self.TipoDocumento.RIF and self.numero_documento:
            first_char = self.numero_documento[0]
            if not first_char.isalpha():
                raise ValidationError(
                    {'numero_documento': 'El RIF debe iniciar con una letra (J, G, V, E, etc.).'}
                )
        super().clean()

    def __str__(self):
        return f'{self.nombre_razon_social} ({self.tipo_documento}: {self.numero_documento})'


# ---------------------------------------------------------------------------
# 3. Categoría — jerarquía auto-referencial
# ---------------------------------------------------------------------------

class Categoria(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    categoria_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategorias',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['categoria_padre']),
        ]

    def __str__(self):
        return self.nombre


# ---------------------------------------------------------------------------
# 4. Producto — stock estricto
# ---------------------------------------------------------------------------

class Producto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
    )
    precio_bs = models.DecimalField(max_digits=12, decimal_places=2)
    precio_usd = models.DecimalField(max_digits=12, decimal_places=2)
    costo_bs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    permite_stock_negativo = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['nombre']),
            models.Index(fields=['categoria']),
            models.Index(fields=['stock_actual']),
        ]

    def clean(self):
        if not self.permite_stock_negativo and self.stock_actual < 0:
            raise ValidationError(
                {'stock_actual': 'El stock actual no puede ser negativo si no se permite stock negativo.'}
            )
        super().clean()

    def __str__(self):
        return f'{self.codigo} — {self.nombre}'


# ---------------------------------------------------------------------------
# 5. CabeceraFactura — moneda dual + IVA
# ---------------------------------------------------------------------------

class CabeceraFactura(models.Model):

    class TipoDocumento(models.TextChoices):
        FACTURA = 'factura', 'Factura'
        NOTA_DEBITO = 'nota_debito', 'Nota de Débito'
        NOTA_CREDITO = 'nota_credito', 'Nota de Crédito'

    class Estatus(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        PAGADA = 'pagada', 'Pagada'
        CANCELADA = 'cancelada', 'Cancelada'

    class Moneda(models.TextChoices):
        BS = 'bs', 'Bolívares'
        USD = 'usd', 'Dólares'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_factura = models.CharField(max_length=20, unique=True)

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='facturas',
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='facturas',
    )
    fecha_emision = models.DateTimeField(auto_now_add=True)

    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
    )
    estatus = models.CharField(
        max_length=20,
        choices=Estatus.choices,
        default=Estatus.BORRADOR,
    )

    # Moneda dual
    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4)
    moneda_principal = models.CharField(
        max_length=3,
        choices=Moneda.choices,
    )

    # Subtotal
    subtotal_bs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    subtotal_usd = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    # IVA (16%)
    monto_iva_bs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    monto_iva_usd = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    # Descuentos (opcionales)
    descuento_bs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    descuento_usd = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    # Totales
    total_bs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_usd = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    # SENIAT / control
    numero_control = models.CharField(max_length=20, blank=True)
    serie = models.CharField(max_length=10, blank=True)
    observaciones = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        permissions = [
            ('view_report', 'Puede ver reportes de ventas'),
        ]
        indexes = [
            models.Index(fields=['numero_factura']),
            models.Index(fields=['cliente']),
            models.Index(fields=['usuario']),
            models.Index(fields=['fecha_emision']),
            models.Index(fields=['estatus']),
            models.Index(fields=['tipo_documento']),
        ]

    def clean(self):
        """Validar que el descuento no supere el 20% del subtotal."""
        desc_max = (self.subtotal_bs * Decimal('0.20')).quantize(Decimal('0.01'))
        if self.descuento_bs > desc_max:
            raise ValidationError({
                'descuento_bs': (
                    f'El descuento no puede superar el 20% del subtotal. '
                    f'Máximo permitido: {desc_max} Bs.'
                ),
            })
        super().clean()

    def __str__(self):
        return f'{self.numero_factura} — {self.cliente.nombre_razon_social}'


# ---------------------------------------------------------------------------
# 6. DetalleVenta — línea de factura con moneda dual + IVA
# ---------------------------------------------------------------------------

class DetalleVenta(models.Model):
    """Línea individual dentro de una factura.

    IVA fijo del 16 % sobre el subtotal de cada línea, replicado en Bs y USD
    para mantener coherencia contable en ambas monedas.
    """

    IVA = Decimal('0.16')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cabecera = models.ForeignKey(
        CabeceraFactura,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles_venta',
    )

    cantidad = models.PositiveIntegerField()

    # Precios unitarios al momento de la venta (snapshot histórico)
    precio_unitario_bs = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario_usd = models.DecimalField(max_digits=12, decimal_places=2)

    # Subtotal (cantidad × precio unitario)
    subtotal_bs = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal_usd = models.DecimalField(max_digits=12, decimal_places=2)

    # IVA (16 % del subtotal)
    monto_iva_bs = models.DecimalField(max_digits=12, decimal_places=2)
    monto_iva_usd = models.DecimalField(max_digits=12, decimal_places=2)

    # Total línea (subtotal + IVA)
    total_bs = models.DecimalField(max_digits=12, decimal_places=2)
    total_usd = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'
        indexes = [
            models.Index(fields=['cabecera']),
            models.Index(fields=['producto']),
        ]

    def save(self, *args, **kwargs):
        # Auto-cálculo de montos (consistencia aunque se reciba del frontend)
        self.subtotal_bs = (self.cantidad * self.precio_unitario_bs).quantize(Decimal('0.01'))
        self.subtotal_usd = (self.cantidad * self.precio_unitario_usd).quantize(Decimal('0.01'))
        self.monto_iva_bs = (self.subtotal_bs * self.IVA).quantize(Decimal('0.01'))
        self.monto_iva_usd = (self.subtotal_usd * self.IVA).quantize(Decimal('0.01'))
        self.total_bs = (self.subtotal_bs + self.monto_iva_bs).quantize(Decimal('0.01'))
        self.total_usd = (self.subtotal_usd + self.monto_iva_usd).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.cabecera.numero_factura} - {self.producto.nombre} x{self.cantidad}'
