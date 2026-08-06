# Epica 6 - Gestion de inventario

## Alcance

La Epica 6 implementa el control de inventario por SKU/variante y almacen para sellers, con disponibilidad agregada para compradores, reserva de stock durante checkout, asignacion de almacen de despacho, reposicion por cancelacion/devolucion, alertas dinamicas y kardex de movimientos.

Swagger y `docs/openapi.json` siguen siendo la fuente de verdad contractual de la API.

## Historias implementadas

### HU-INV-01 - Stock por SKU/variante en multiples almacenes

Endpoints:

- `GET /api/v1/seller/inventory`
- `PATCH /api/v1/seller/inventory/{variant_id}`
- `GET /api/v1/seller/warehouses`
- `POST /api/v1/seller/warehouses`
- `PATCH /api/v1/seller/warehouses/{warehouse_id}`

Validaciones:

- El seller solo consulta y ajusta variantes de su tienda.
- El `warehouse_id` debe pertenecer a la tienda y estar activo para ajustes.
- `quantity` y `threshold` no admiten valores negativos.
- La respuesta agrega `quantity`, `reserved`, `available` y desglose `warehouses`.
- Cada ajuste crea `InventoryMovement` con `restock` cuando sube stock y `adjust` cuando baja.

Pruebas:

- `tests/test_hu_inv_01_stock_multi_warehouse.py`

### HU-INV-02 - Reserva de stock agregado al momento de compra

Endpoint:

- `POST /api/v1/checkout`

Validaciones:

- El checkout usa disponibilidad agregada `quantity - reserved` en almacenes activos.
- Con multiples almacenes activos, el pedido queda con `warehouse_id=null` y unidades reservadas.
- Con un solo almacen activo, el checkout descuenta inmediatamente y asigna `warehouse_id`.
- Si dos compradores compiten por la ultima disponibilidad, el segundo recibe `409`.
- El carrito se vacia solo si toda la transaccion completa exitosamente.

Pruebas:

- `tests/test_hu_inv_02_stock_reservation.py`

### HU-INV-03 - Asignacion manual de almacen de despacho

Endpoint:

- `PATCH /api/v1/seller/orders/{order_id}/warehouse`

Validaciones:

- Solo el seller de la tienda puede asignar almacen.
- El almacen debe pertenecer a la tienda y estar activo.
- El almacen elegido debe cubrir las unidades del pedido.
- Al asignar, se libera la reserva agregada y se registra salida `sale` desde el almacen seleccionado.
- Un pedido ya descontado no se puede descontar dos veces y responde `409`.
- Cambiar a `shipped` sin almacen asignado en flujo multi-almacen responde `409`.

Pruebas:

- `tests/test_hu_inv_03_dispatch_warehouse.py`

### HU-INV-04 - Reposicion ante cancelacion o devolucion

Endpoints:

- `POST /api/v1/orders/{order_id}/cancel`
- `PATCH /api/v1/seller/orders/{order_id}/status`
- `POST /api/v1/seller/payments/{payment_id}/reject`
- `POST /api/v1/payments/webhooks/{provider}`

Validaciones:

- Si el pedido solo tenia reserva, se libera `reserved` y se registra `release`.
- Si el pedido ya tuvo salida fisica, se reintegra `quantity` al almacen de origen y se registra `return_in`.
- La reposicion es idempotente para evitar doble reintegro.
- Estados incompatibles mantienen respuesta `409`.

Pruebas:

- `tests/test_hu_inv_04_restock_returns.py`

### HU-INV-05 - Alertas de stock bajo o agotado

Endpoint:

- `GET /api/v1/seller/inventory/alerts`

Validaciones:

- Las alertas se calculan dinamicamente desde stock disponible agregado.
- `low_stock` aplica cuando `0 < available <= threshold`.
- `out_of_stock` aplica cuando `available == 0`.
- Los ajustes, reservas, ventas, cancelaciones y devoluciones refrescan el estado de stock del producto.
- Productos `draft` y `discontinued` no se reactivan automaticamente.

Pruebas:

- `tests/test_hu_inv_05_stock_alerts.py`

### HU-INV-06 - Historial de movimientos de inventario

Endpoint:

- `GET /api/v1/seller/inventory/movements`

Filtros:

- `product_id`
- `variant_id`
- `warehouse_id`
- `reason`
- `date_from`
- `date_to`
- `limit`

Validaciones:

- El historial queda limitado al scope de la tienda autenticada.
- Los movimientos exponen producto, variante, almacen, delta, motivo, pedido relacionado, nota y fecha.
- Se registran movimientos para ajustes, reposiciones, reservas, liberaciones, ventas y devoluciones.

Pruebas:

- `tests/test_hu_inv_06_inventory_movements.py`

### HU-INV-07 - Visualizacion de stock en tiempo real para comprador

Endpoints:

- `GET /api/v1/catalog/products`
- `GET /api/v1/catalog/products/{slug}`
- `GET /api/v1/catalog/variants/{variant_id}/stock`
- `GET /api/v1/cart`
- `POST /api/v1/cart/items`

Validaciones:

- Catalogo, detalle, carrito y endpoint publico de variante usan el mismo helper de disponibilidad agregada.
- Las reservas reducen el stock visible para compradores en tiempo real.
- Productos agotados o intentos por encima de disponibilidad responden `409`.

Pruebas:

- `tests/test_hu_inv_07_public_availability.py`

## Contrato OpenAPI

Pruebas:

- `tests/test_inv_openapi_contract.py`

La prueba de contrato valida que las rutas HU-INV incluyan trazabilidad en `description`, `summary`, respuestas documentadas y seguridad bearer en endpoints privados.

## Validaciones ejecutadas

- Focalizadas: `.venv\Scripts\python.exe -m pytest tests -q -k "hu_inv or inv_openapi"`
- Suite completa: `.venv\Scripts\python.exe -m pytest tests -q`
- Sync docs backend-only: `scripts.sync_docs` escribiendo solo en `sesingular-backend/docs`

## Notas para frontend

- Para multi-almacen, el checkout devuelve pedidos con `warehouse_id=null`; el panel seller debe pedir asignacion de almacen antes de despacho.
- `GET /api/v1/seller/warehouses` incluye `requires_manual_dispatch_selection`.
- `GET /api/v1/seller/inventory` ya entrega agregado y desglose por almacen; no hace falta calcularlo en frontend.
- `GET /api/v1/catalog/variants/{variant_id}/stock` devuelve `stock`, `available`, `low_stock` y `out_of_stock` para refrescos puntuales de disponibilidad.

