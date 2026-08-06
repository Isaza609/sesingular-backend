# Epica 09: Carrito y checkout

**Epica ID:** 09
**Modulo / prefijo HU:** CHK
**Swagger tag:** `Orders`
**Prefijo de rutas:** `/api/v1`
**Autenticacion:** `Authorization: Bearer <JWT Supabase>`
**Scope:** comprador autenticado; tienda del seller/equipo para panel de pedidos
**Ultima actualizacion:** 2026-08-05

---

## Resumen del modulo

La Epica 09 implementa el carrito persistente del comprador, la cotizacion previa al pago con desglose por tienda, la validacion final de stock antes de confirmar, la confirmacion con resumen y correo, y la asignacion de compras multi-tienda a pedidos independientes por tienda.

El checkout usa el carrito como fuente de items, conserva precios/montos historicos en pedidos, valida disponibilidad real antes de confirmar y crea una compra agrupada (`CheckoutGroup`) cuando la confirmacion genera uno o varios pedidos.

Swagger y `docs/openapi.json` siguen siendo la fuente de verdad contractual de la API.

---

## Indice de HUs implementadas

| HU | Titulo | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-CHK-01 | Carrito de compras persistente | 2026-08-05 | `GET /api/v1/cart`, `POST /api/v1/cart/items`, `PATCH /api/v1/cart/items/{item_id}`, `DELETE /api/v1/cart/items/{item_id}`, `DELETE /api/v1/cart` | `tests/test_hu_chk_01_cart_persistence.py` |
| HU-CHK-02 | Desglose del total con envio y cargos definidos por el vendedor | 2026-08-05 | `POST /api/v1/checkout/quote` | `tests/test_hu_chk_02_checkout_totals.py` |
| HU-CHK-03 | Validacion de stock disponible antes de confirmar | 2026-08-05 | `POST /api/v1/checkout` | `tests/test_hu_chk_03_stock_validation.py` |
| HU-CHK-04 | Confirmacion de pedido con resumen | 2026-08-05 | `POST /api/v1/checkout` | `tests/test_hu_chk_04_checkout_confirmation.py` |
| HU-CHK-05 | Asignacion de la compra a la tienda | 2026-08-05 | `POST /api/v1/checkout`, `GET /api/v1/purchases`, `GET /api/v1/purchases/{purchase_id}`, `GET /api/v1/orders`, `GET /api/v1/orders/{order_id}`, `GET /api/v1/seller/orders` | `tests/test_hu_chk_05_store_assignment.py` |

Prueba contractual OpenAPI: `tests/test_chk_openapi_contract.py`.

---

## HU-CHK-01 - Carrito de compras persistente

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_chk_01_cart_persistence.py`

### Descripcion funcional

El comprador mantiene un carrito propio entre sesiones. La API crea o reutiliza el carrito del usuario autenticado, retorna items tipados, agrupa por tienda y recalcula precio efectivo y disponibilidad antes de permitir el checkout.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Al cerrar sesion e iniciar nuevamente, el carrito conserva los productos agregados. | Si | Los items se persisten en `Cart` y `CartItem` asociados al `buyer_id`; `GET /cart` reutiliza el carrito del comprador autenticado. |
| 2 | Si un producto guardado se agota, el carrito lo senala antes del checkout. | Si | La respuesta incluye `available`, `availability_status`, `availability_message`, `checkout_blocked` y `blocking_reasons` con stock agregado vigente. |

### Flujo implementado

```text
1. Frontend agrega una variante con POST /api/v1/cart/items.
2. La API valida rol buyer, variante/producto activo y cantidad 1..100.
3. El item queda persistido en el carrito del comprador.
4. GET /api/v1/cart recalcula precio efectivo, stock y grupos por tienda.
5. Si algun item no puede comprarse, el carrito queda bloqueado para checkout.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/cart` -> 200

Retorna el carrito persistente del comprador con items, grupos por tienda, totales estimados y bloqueos.

Errores: `401` sin autenticacion, `403` rol no permitido.

#### POST `/api/v1/cart/items` -> 200

Agrega una variante al carrito persistente.

Request:

```json
{
  "variant_id": "variant-123",
  "quantity": 2
}
```

Tambien puede resolver por `product_id` y `color` cuando no se envia `variant_id`.

Errores: `400` body invalido, `401`, `403`, `404` variante/producto no encontrado, `409` disponibilidad insuficiente, `422`.

#### PATCH `/api/v1/cart/items/{item_id}` -> 200

Actualiza la cantidad de un item propio.

Request:

```json
{
  "quantity": 3
}
```

Errores: `401`, `403`, `404`, `409`, `422`.

#### DELETE `/api/v1/cart/items/{item_id}` -> 200

Elimina un item propio del carrito y retorna el carrito recalculado.

#### DELETE `/api/v1/cart` -> 200

Vacia el carrito del comprador autenticado.

### Tests de esta HU

- Archivo: `tests/test_hu_chk_01_cart_persistence.py`
- Cubre persistencia por comprador, aislamiento de scope y senales de producto agotado.
- Ejecutar: `.venv\Scripts\python.exe -m pytest tests/test_hu_chk_01_cart_persistence.py -v`

### Notas y advertencias para frontend

- No eliminar automaticamente items con `available=false`; se muestran para que el comprador ajuste el carrito.
- `checkout_blocked=true` indica que no debe mostrarse accion de confirmacion sin resolver bloqueos.
- `store_groups` permite pintar el carrito separado por tienda sin hacer llamadas adicionales.

---

## HU-CHK-02 - Desglose del total con envio y cargos definidos por el vendedor

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_chk_02_checkout_totals.py`

### Descripcion funcional

El comprador puede cotizar el checkout antes de confirmar. La cotizacion retorna subtotal, descuentos, cargos extra, envio y total por tienda y de forma agregada. El envio se calcula desde la configuracion del vendedor: plano, por zonas o a convenir.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Si la direccion coincide con una zona configurada, se suma el envio correspondiente. | Si | `POST /checkout/quote` acepta `address_id`, `address` o `shipping_location` y resuelve zonas activas por ciudad/region. |
| 2 | Los cargos extra activos aparecen con nombre y valor en linea independiente. | Si | La cotizacion reutiliza `calculate_store_pricing()` y retorna ajustes `extra_charge` por tienda. |
| 3 | Envio a convenir no suma envio y muestra contacto del vendedor. | Si | `shipping.mode=to_agree`, `cost=0`, `requires_contact=true` y `contact` incluye datos publicos de la tienda. |
| 4 | La promocion de envio gratis deja envio en cero y marcado como promocion. | Si | Cuando aplica umbral o zona con envio gratis, `cost=0`, `original_cost` conserva el costo y `promotion_applied=true`. |
| 5 | Si el lugar no esta en las zonas, se indica contactar al vendedor. | Si | Sin zona activa compatible, la respuesta usa modalidad a convenir y mensaje de contacto. |

### Flujo implementado

```text
1. Frontend llama POST /api/v1/checkout/quote con direccion, lugar o direccion guardada.
2. La API valida comprador y carrito listo.
3. Agrupa items por tienda.
4. Calcula descuentos/cargos extra por tienda.
5. Resuelve envio por tienda y retorna totales agregados.
```

### Endpoint implementado en esta HU

#### POST `/api/v1/checkout/quote` -> 200

Request:

```json
{
  "address_id": "addr-123",
  "shipping_location": {
    "city": "Bogota",
    "region": "Cundinamarca",
    "country": "Colombia"
  },
  "coupon_code": "VERANO10",
  "payment_method": "card"
}
```

Response incluye `subtotal`, `discount`, `extra_charge_total`, `shipping_cost`, `tax`, `total`, `currency` y `store_quotes`.

Errores: `400` carrito vacio o datos invalidos, `401`, `403`, `404` direccion no encontrada, `409` carrito bloqueado por disponibilidad, `422`.

### Tests de esta HU

- Archivo: `tests/test_hu_chk_02_checkout_totals.py`
- Cubre envio por zona, envio a convenir, envio gratis, cargos extra y desglose multi-tienda.
- Ejecutar: `.venv\Scripts\python.exe -m pytest tests/test_hu_chk_02_checkout_totals.py -v`

### Notas y advertencias para frontend

- Pintar `store_quotes` por tienda; no sumar manualmente cargos extra fuera de la respuesta.
- Si `shipping.requires_contact=true`, mostrar `contact` de la tienda.
- Si `shipping.original_cost > shipping.cost`, mostrar el costo original como referencia de promocion.

---

## HU-CHK-03 - Validacion de stock disponible antes de confirmar

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_chk_03_stock_validation.py`

### Descripcion funcional

Antes de crear pedidos, pagos o movimientos, el checkout recarga el carrito y valida disponibilidad real agregada. Si un item ya no puede comprarse, la transaccion se rechaza y el carrito permanece intacto.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Con stock disponible, la compra se procesa normalmente. | Si | `POST /checkout` valida disponibilidad y luego crea compra agrupada, pedidos, pagos y movimientos de inventario. |
| 2 | Si un producto se agota justo antes de confirmar, se informa y no se permite continuar. | Si | `_assert_cart_ready()` responde `409` con detalle por item y no se crean efectos colaterales. |

### Flujo implementado

```text
1. Frontend confirma con POST /api/v1/checkout.
2. La API recarga carrito, variantes, tiendas y disponibilidad.
3. Si hay bloqueo, responde 409 con items afectados.
4. Si todo esta disponible, crea la compra dentro de la transaccion.
5. Consume o reserva inventario segun la configuracion de almacenes.
```

### Endpoint implementado en esta HU

#### POST `/api/v1/checkout` -> 201

Request:

```json
{
  "address_id": "addr-123",
  "coupon_code": "VERANO10",
  "payment_method": "card",
  "payout_account_id": null,
  "notes": "Entregar en porteria"
}
```

Tambien acepta `address` para crear y usar una direccion nueva.

Errores: `400` carrito vacio o direccion faltante, `401`, `403`, `404`, `409` item sin disponibilidad, `422`.

### Tests de esta HU

- Archivo: `tests/test_hu_chk_03_stock_validation.py`
- Cubre camino feliz, rechazo `409` y atomicidad ante stock agotado.
- Ejecutar: `.venv\Scripts\python.exe -m pytest tests/test_hu_chk_03_stock_validation.py -v`

### Notas y advertencias para frontend

- En `409`, usar el detalle de items para guiar al comprador a actualizar cantidades o eliminar productos.
- No asumir que una cotizacion previa garantiza confirmacion; la validacion final ocurre en `POST /checkout`.

---

## HU-CHK-04 - Confirmacion de pedido con resumen

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_chk_04_checkout_confirmation.py`

### Descripcion funcional

Al confirmar, la API responde una confirmacion tipada con compra agrupada, pedidos, resumen monetario, direccion, metodo de pago y notas de envio. Tambien agenda el correo de resumen al comprador.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | La pantalla recibe un resumen completo con productos, montos, direccion, metodo de pago y envio. | Si | `CheckoutConfirmationOut` incluye `orders`, `summary`, `payment_required` y `shipping_notes`. Cada `OrderOut` incluye items, ajustes, direccion y montos historicos. |
| 2 | El comprador recibe correo con el mismo resumen. | Si | `mailer.checkout_summary_to_buyer()` se agenda con `BackgroundTasks` luego de confirmar correctamente. |
| 3 | Si el envio es a convenir, el resumen lo indica explicitamente. | Si | Las notas de envio a convenir se agregan a la confirmacion y a las notas del pedido correspondiente. |

### Flujo implementado

```text
1. La confirmacion valida stock y calcula totales finales.
2. Se crea `CheckoutGroup` con resumen agregado.
3. Se crea un pedido por tienda con items, ajustes y pagos.
4. Se limpia el carrito solo despues del commit exitoso.
5. Se agenda el correo de resumen al comprador.
```

### Endpoint implementado en esta HU

#### POST `/api/v1/checkout` -> 201

Response:

```json
{
  "purchase_id": "purchase-123",
  "orders": [],
  "summary": {
    "subtotal": 90000,
    "discount": 0,
    "extra_charge_total": 5000,
    "shipping_cost": 12000,
    "tax": 0,
    "total": 107000,
    "currency": "COP",
    "payment_method": "card",
    "address": null
  },
  "payment_required": true,
  "shipping_notes": []
}
```

Errores: `400`, `401`, `403`, `404`, `409`, `422`.

### Tests de esta HU

- Archivo: `tests/test_hu_chk_04_checkout_confirmation.py`
- Cubre respuesta de confirmacion, resumen, envio a convenir y correo stubbeado.
- Ejecutar: `.venv\Scripts\python.exe -m pytest tests/test_hu_chk_04_checkout_confirmation.py -v`

### Notas y advertencias para frontend

- Usar `purchase_id` como identificador visual de la compra agrupada.
- `orders` puede contener uno o varios pedidos; no asumir una sola tienda.
- Mostrar `shipping_notes` cuando existan, especialmente en modalidad a convenir.

---

## HU-CHK-05 - Asignacion de la compra a la tienda

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_chk_05_store_assignment.py`

### Descripcion funcional

Cada compra se asigna a la tienda que vende los productos. Si el carrito contiene productos de varias tiendas, el checkout crea un pedido por tienda asociado a una compra agrupada. El comprador ve una vista unificada y cada tienda ve solo sus pedidos.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Una compra de una sola tienda queda asignada a esa tienda y aparece en su panel. | Si | `Order.store_id` se define desde los items de la tienda y `GET /seller/orders` filtra por tienda del seller/equipo. |
| 2 | Una compra multi-tienda crea un pedido por tienda y cada tienda ve solo el suyo. | Si | `POST /checkout` agrupa items por tienda y crea pedidos separados con el mismo `checkout_group_id`. |
| 3 | El comprador ve la compra agrupada con estado por tienda. | Si | `GET /purchases` y `GET /purchases/{purchase_id}` retornan `PurchaseOut` con pedidos y estados por tienda. |
| 4 | Varios usuarios de una tienda ven el mismo pedido asignado a la tienda. | Si | El panel seller usa scope de tienda/equipo, no un panel por usuario individual. |

### Flujo implementado

```text
1. Checkout agrupa items del carrito por `store_id`.
2. Crea `CheckoutGroup` con totales generales.
3. Crea un `Order` por tienda con sus items y ajustes.
4. Asociacion: `Order.checkout_group_id = CheckoutGroup.id`.
5. Comprador consulta compras agrupadas; seller consulta pedidos de su tienda.
```

### Endpoints implementados en esta HU

#### POST `/api/v1/checkout` -> 201

Crea la compra agrupada y uno o mas pedidos por tienda.

#### GET `/api/v1/purchases` -> 200

Lista compras agrupadas del comprador autenticado.

Errores: `401`, `403`.

#### GET `/api/v1/purchases/{purchase_id}` -> 200

Retorna una compra agrupada propia con pedidos por tienda.

Errores: `401`, `403`, `404`.

#### GET `/api/v1/orders` -> 200

Lista pedidos del comprador. Acepta filtro opcional `status`.

#### GET `/api/v1/orders/{order_id}` -> 200

Retorna detalle de un pedido propio del comprador.

#### GET `/api/v1/seller/orders` -> 200

Lista pedidos asignados a la tienda del seller/equipo autenticado.

Errores: `401`, `403`.

### Tests de esta HU

- Archivo: `tests/test_hu_chk_05_store_assignment.py`
- Cubre separacion de pedidos por tienda, vista agrupada del comprador y aislamiento del panel seller.
- Ejecutar: `.venv\Scripts\python.exe -m pytest tests/test_hu_chk_05_store_assignment.py -v`

### Notas y advertencias para frontend

- Para historial del comprador, usar `GET /api/v1/purchases` como vista agrupada.
- Para panel de tienda, usar `GET /api/v1/seller/orders`; no usar endpoints de comprador.
- El estado operativo sigue estando en cada pedido de tienda, aunque la compra agrupada tenga un total general.

---

## Validaciones ejecutadas

- `.venv\Scripts\python.exe -m pytest tests -v -k "hu_chk or chk_openapi"` -> `10 passed, 113 deselected`.
- `.venv\Scripts\python.exe -m pytest tests -q` -> `120 passed, 3 skipped`.
- `scripts.sync_docs` actualizado para `docs/openapi.json` y `docs/API_REFERENCE.md`.

