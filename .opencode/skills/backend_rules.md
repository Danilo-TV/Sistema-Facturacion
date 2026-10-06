# Skill: Backend Rules (Django 5.x &amp; ORM) 

## Vistas Basadas en Clases (CBVs) 
- **Obligatorio**: Usar CBVs de Django (`ListView`, `DetailView`, `CreateView`, `UpdateView`). Prohibido usar FBVs. - **Seguridad**: Extender siempre de `LoginRequiredMixin` y `PermissionRequiredMixin`. 

## Optimización de Base de Datos y Concurrencia 
- **Evitar N+1**: Usar `select_related()` para claves foráneas y `prefetch_related()` para ManyToMany. 
- **Operaciones de Caja / Stock**: Encapsular en bloques `transaction.atomic()`. Para lecturas con actualización crítica de inventario, usar `select_for_update()`.
- **Mapeo Eficiente**: Utilizar `.only()` o `.defer()` al consultar grandes volúmenes de datos.

## Zonas Horarias y Moneda - Importar fecha/hora nativa con `from zoneinfo import ZoneInfo`. Usar `ZoneInfo('America/Caracas')`. - Todo registro de venta debe almacenar el monto en ambas monedas (Bs. y USD).