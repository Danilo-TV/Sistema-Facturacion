### Especificación de Vistas y URLs — Sistema de Facturación
#### Overview
Sistema de facturación con CBVs, AJAX, Select2 y DataTables para gestión de inventario y facturación.

--------------------------------------------------------------------------------

#### 1. URLs del Sistema
##### Estructura de URLs

--------------------------------------------------------------------------------

#### 2. Vistas de Inventario (CBVs)
##### 2.1 ProductoListView
| Campo | Valor |
| ------ | ------ |
| herencia | LoginRequiredMixin + ListView |
| modelo | Producto |
| template | facturacion/producto_list.html |
| paginate_by | 25 |
| ordering | nombre |

--------------------------------------------------------------------------------

#### 3. Vista Principal de Facturación
##### 3.1 FacturaCreateView (Especial)
| Campo | Detalle |
| ------ | ------ |
| Herencia | LoginRequiredMixin + TemplateView |
| Template | facturacion/factura_form.html |
| Métodos | GET, POST, AJAX |

###### Flujo de la Vista
###### Componentes del Formulario
| Componente | Descripción |
| ------ | ------ |
| Cliente | Select2 con búsqueda AJAX |
| Tasa Cambio | Input number, required |
| Detalles | DataTables editable |
| Subtotal Bs/USD | Calculado automático |
| IVA 16% | Calculado automático |
| Descuento | Input opcional |
| Total Bs/USD | Calculado automático |

###### Reglas de Negocio Aplicadas
*  IVA = 16% fijo (facturacion_venezuela.md)
*  Moneda dual: ambos campos (_bs, _usd)
*  Stock estricto: validar antes de agregar línea
*  Tasa cambio: guardada con la factura

--------------------------------------------------------------------------------

#### 4. API Endpoints (JSON)
##### 4.1 Buscar Producto (Select2)
##### 4.2 Buscar Cliente (Select2)
##### 4.3 Calcular Línea
##### 4.4 Detalle Temporal (DataTables)

--------------------------------------------------------------------------------

#### 5. DataTables Configuración
##### Columnas
| # | Columna | Tipo |
| ------ | ------ | ------ |
| 0 | ID | hidden |
| 1 | Producto | text (readonly) |
| 2 | Cantidad | number (editable) |
| 3 | Precio Bs | number (readonly) |
| 4 | Descuento Bs | number (editable) |
| 5 | IVA 16% | number (readonly) |
| 6 | Subtotal | number (readonly) |
| 7 | Acciones | buttons |

##### Eventos
*   **onRowClick** : Abrir edición
*   **onChange** : Recalcular línea + totales globales
*   **onDelete** : Confirmar + recalcular

--------------------------------------------------------------------------------

#### 6. Select2 Configuración
##### Cliente
##### Producto (en DataTables)

--------------------------------------------------------------------------------

#### 7. Templates
##### Estructura

--------------------------------------------------------------------------------

#### 8. Checklist de Implementación
*  [ ] URLs básicas configuradas
*  [ ] LoginRequiredMixin en todas las vistas
*  [ ] Select2 para cliente (búsqueda AJAX)
*  [ ] Select2 para producto (búsqueda AJAX)
*  [ ] DataTables editable para detalles
*  [ ] Cálculo automático IVA 16%
*  [ ] Moneda dual (Bs/USD)
*  [ ] Validación de stock en tiempo real
*  [ ] Templates con diseño profesional
*  [ ] Tests para cada vista

--------------------------------------------------------------------------------

#### 9. NotasImportantes
1.  **CBVs obligatorias** : NUNCA usar FBVs (django_best_practices.md)
2.  **IVA 16%** : Siempre automático (facturacion_venezuela.md)
3.  **Moneda dual** : Ambos campos en cadaTransaction
4.  **Stock** : Validar antes de agregar línea
5.  **Security** : CSRF + LoginRequiredMixin

--------------------------------------------------------------------------------
