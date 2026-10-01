### Especificación de Base de Datos — Sistema de Facturación
#### Overview del Proyecto
Sistema de facturación electrónico para Venezuela con soporte para moneda dual (Bolívares/Dólares), cálculo automático de IVA al 16% y gestión de inventario con stock estricto.

--------------------------------------------------------------------------------

#### Modelos de Datos

##### 1. Usuario
| Campo | Tipo | Requerido | Descripción |
| ------ | ------ | ------ | ------ |
| id | UUID | Sí | Identificador único |
| username | Char(150) | Sí | Nombre de usuario único |
| email | Email | Sí | Correo electrónico único |
| password | Char(255) | Sí | Hash de contraseña |
| first_name | Char(100) | No | Nombres |
| last_name | Char(100) | No | Apellidos |
| rol | Enum | Sí | Rol del usuario (admin, vendedor, contador) |
| is_active | Boolean | Sí | Estado activo |
| created_at | DateTime | Sí | Fecha de creación |
| updated_at | DateTime | Sí | Fecha de última modificación |

##### 2. Cliente
**Relaciones** : Un Cliente puede tener múltiples facturas (ForeignKey inversa).
**Validaciones** :
* El número de documento debe ser único por tipo de documento.
* Si tipo_documento es "rif", el formato debe iniciar con letra (J, G, V, E, etc.).

--------------------------------------------------------------------------------

##### 3. Categoría
| Campo | Tipo | Requerido | Descripción |
| ------ | ------ | ------ | ------ |
| id | UUID | Sí | Identificador único |
| nombre | Char(100) | Sí | Nombre de la categoría |
| descripcion | Text | No | Descripción detallada |
| categoria_padre | ForeignKey | No | Categoría padre (para jerarquía) |
| is_active | Boolean | Sí | Estado activo |
| created_at | DateTime | Sí | Fecha de creación |
| updated_at | DateTime | Sí | Fecha de última modificación |

##### 4. Producto
**Relaciones** : Un Producto pertenece a una Categoría. Un Producto puede tener muchos DetalleVenta.
**Reglas de Negocio** :
* El stock_actual debe ser >= 0 si permite_stock_negativo es False.
* Al registrar una venta, el stock se descuenta automáticamente.
* Si stock_actual <= stock_minimo, generar alerta de reposición.

--------------------------------------------------------------------------------

##### 5. CabeceraFactura
| Campo | Tipo | Requerido | Descripción |
| ------ | ------ | ------ | ------ |
| id | UUID | Sí | Identificador único |
| numero_factura | Char(20) | Sí | Número de factura único |
| cliente | ForeignKey | Sí | Cliente asociado |
| usuario | ForeignKey | Sí | Usuario que genera la factura |
| fecha_emision | DateTime | Sí | Fecha y hora de emisión |
| tipo_documento | Enum | Sí | Tipo (factura, nota_débito, nota_credito) |
| estatus | Enum | Sí | Estatus (borrador, pagada, cancelada) |
| tasa_cambio | Decimal(10,4) | Sí | Tasa de cambio vigente al momento |
| moneda_principal | Enum | Sí | Moneda principal (bs, usd) |
| subtotal_bs | Decimal(12,2) | Sí | Subtotal en Bs |
| subtotal_usd | Decimal(12,2) | Sí | Subtotal en USD |
| monto_iva_bs | Decimal(12,2) | Sí | Monto IVA en Bs |
| monto_iva_usd | Decimal(12,2) | Sí | Monto IVA en USD |
| descuento_bs | Decimal(12,2) | No | Descuento en Bs |
| descuento_usd | Decimal(12,2) | No | Descuento en USD |
| total_bs | Decimal(12,2) | Sí | Total en Bs |
| total_usd | Decimal(12,2) | Sí | Total en USD |
| numero_control | Char(20) | No | Número de control SENIAT |
| serie | Char(10) | No | Serie del equipo |
| observaciones | Text | No | Notas adicionales |
| created_at | DateTime | Sí | Fecha de creación |
| updated_at | DateTime | Sí | Fecha de última modificación |

##### Moneda Dual
* El sistema almacena AMBAS monedas en cada transacción.
* La tasa de cambio se guarda con la factura (histórico).
* Campos _bs se calculan usando los precios originales del producto.
* Campos _usd se calculan dividiendo entre la tasa de cambio oficial.
* La moneda principal determina cómo se muestra en reportes.

##### Stock Estricto
* Por defecto, no se permiten ventas que excedan el stock disponible.
* Solo si permite_stock_negativo=True en el producto, se permite venta sin inventario.
* El stock se descuenta al confirmar la venta, no al crear la factura en borrador.

--------------------------------------------------------------------------------

##### Tasa de Cambio (DECIDIDO)
* **Modalidad** : Manual — el usuario ingresa la tasa de cambio al momento de facturar.
* **Almacenamiento** : Se guarda en cada factura para mantener histórico.
* **Implicaciones en el modelo** : El campo tasa_cambio en CabeceraFactura es obligatorio.

--------------------------------------------------------------------------------

##### 2. Facturación SENIAT (DECIDIDO)
* **Modalidad** : Factura simple con número de control interno.
* **Campos adicionales** : numero_control (Char), serie (Char) — sin integración con SENIAT.
* **Implicaciones en el modelo** : No se requiere código de seguridad ni validación rigurosa.

--------------------------------------------------------------------------------

##### 3. Productos (DECIDIDO)
* **Modalidad** : Productos simples — un SKU = un producto.
* **Variantes** : No hay tallas, colores ni tamaños.
* **Lotes** : No hay control de lotes ni fechas de vencimiento.
* **Implicaciones en el modelo** : Solo el modelo Producto, sin ProductoVariante.

--------------------------------------------------------------------------------

##### 4. Acceso al Sistema (DECIDIDO)
* **Usuarios** : Solo empleados (vendedores y administradores).
* **Roles definidos** : admin, vendedor, contador.
* **Portal de clientes** : No se implementará.
* **Implicaciones en el modelo** : El modelo Usuario sirve para autenticación interna.

--------------------------------------------------------------------------------

##### 5. Otros (DECIDIDO)
* **Empresa** : Una sola empresa (mono-empresa).
* **Moneda principal** : Boliviaves (Bs) como moneda principal, USD como referencia.
* **Facturación PDF** : No requerida por ahora.

--------------------------------------------------------------------------------

#### Preguntas Pendientes
*Todas las preguntas han sido respondidas y aprobadas.*

--------------------------------------------------------------------------------

#### Próximos Pasos Propuestos
1. Confirmar las preguntas pendientes.
2. Aprobar el diseño de modelos.
3. Generar las migrationes de Django.
4. Implementar las validaciones y señales.
5. Crear los serializers de API.

--------------------------------------------------------------------------------

#### Plan de Migraciones
##### Secuencia de Migraciones
El sistema generará las siguientes migraciones automáticamente:
| Orden | Modelo | Dependencias |
| ------ | ------ | ------ |
| 0001 | Usuario | Ninguna |
| 0002 | Categoria | Ninguna |
| 0003 | Cliente | Ninguna |
| 0004 | Producto | Categoria |
| 0005 | CabeceraFactura | Usuario, Cliente |
| 0006 | DetalleVenta | CabeceraFactura, Producto |

##### Cómo Generar y Aplicar las Migraciones

##### Notas Importantes
1. **Usuario requiere AUTH_USER_MODEL** : Asegúrate de que AUTH_USER_MODEL = 'facturacion.Usuario' está en settings.py
2. **ForeignKey circular** : CabeceraFactura depende de Usuario y Cliente, DetalleVenta depende de CabeceraFactura y Producto
3. **Índices** : Todos los modelos tienen índices para optimización
4. **Validaciones** : Las validaciones están en los métodos clean() de cada modelo

--------------------------------------------------------------------------------

*Documento generado bajo metodología Spec-Driven Development*