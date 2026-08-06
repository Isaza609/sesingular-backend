# Epica 13: Envíos y entregas

**Épica ID:** 13
**Módulo / prefijo HU:** ENV
**Swagger tags:** `buyer`, `seller`, `seller-orders`, `catalog`
**Prefijos de rutas:** `/api/v1/orders`, `/api/v1/seller/orders`, `/api/v1/seller/store/settings`, `/api/v1/catalog`
**Autenticación:** `Authorization: Bearer <JWT Supabase>` (la ficha y las opciones públicas de envío son públicas)
**Scope:** comprador (lo suyo) · tienda del vendedor (lo suyo)
**Última actualización:** 2026-08-06

---

## Resumen del módulo

Cada vendedor maneja su envío de forma personalizada: **sin transportadoras ni cálculo automático de tarifas**. Define la modalidad de su tienda (tarifas propias por lugar / a convenir), sobrescribible por producto; configura lugares y precios; ofrece envío gratis con vigencia; actualiza manualmente el estado del envío con una línea de tiempo que el comprador consulta; y gestiona devoluciones con reingreso condicional a inventario.

### Modelo

- `ShipmentEvent` (`shipment_events`): línea de tiempo del envío (`status`, `note`, `created_at`). `Shipment` gana `tracking_status` (etiqueta vigente) y `note`.
- `Product.shipping_mode` (nullable): override de la modalidad de envío del producto sobre la tienda (`own_rates`/`to_agree`).
- Configuración de envío en `store_config` (`StoreSettingsIn`): `shipping_mode` (flat/zones/to_agree), `shipping_flat_cost`, `shipping_free_threshold`, `free_shipping_from`/`free_shipping_to` (vigencia), y `shipping_zones[]` con `cost`/`active`/`free_shipping`/`free_shipping_min_subtotal`/`free_shipping_from`/`free_shipping_to`.
- Migración: `0013_shipping_tracking_epica13.py`.

---

## Índice de HUs implementadas

| HU | Título | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-ENV-01 | Modalidad de tienda + override por producto | 2026-08-06 | `PUT /seller/store/settings`, `POST/PATCH /seller/products*` | `tests/test_hu_env_01_shipping_mode.py` |
| HU-ENV-02 | Lugares y precios | 2026-08-06 | `PUT /seller/store/settings`, `POST /checkout/quote` | `tests/test_hu_env_02_shipping_locations.py` |
| HU-ENV-03 | Envío a convenir con contacto | 2026-08-06 | `GET /catalog/products/{slug}`, `GET /orders/{id}` | `tests/test_hu_env_03_shipping_to_agree.py` |
| HU-ENV-04 | Envío gratis con vigencia | 2026-08-06 | `PUT /seller/store/settings`, `POST /checkout/quote` | `tests/test_hu_env_04_free_shipping_promo.py` |
| HU-ENV-05 | Seguimiento del envío | 2026-08-06 | `PATCH /seller/orders/{id}/shipment`, `GET /orders/{id}/shipment` | `tests/test_hu_env_05_shipment_tracking.py` |
| HU-ENV-06 | Devoluciones con reingreso | 2026-08-06 | `POST /seller/orders/{id}/return` | `tests/test_hu_env_06_returns.py` |

---

## HU-ENV-01 · Modalidad de tienda + override por producto

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Tarifas propias exige ≥1 lugar | ✅ | `PUT /seller/store/settings` con `shipping_mode=zones` sin lugar activo → 400. |
| 2 | A convenir no cobra en checkout | ✅ | `shipping_mode=to_agree` → `_shipping_for_store` retorna costo 0 y `to_agree`. |
| 3 | Override por producto prevalece | ✅ | `Product.shipping_mode=to_agree` fuerza a convenir en la ficha y el quote. |
| 4 | Cambio de modalidad no altera pedidos previos | ✅ | El pedido conserva su `shipping_cost` histórico. |

## HU-ENV-02 · Lugares y precios

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Precio por lugar visible en checkout | ✅ | `shipping_zones[].cost` resuelto por `_zone_matches`. |
| 2 | Edición conserva tarifa histórica | ✅ | El pedido guarda `shipping_cost` al confirmarse. |
| 3 | Lugar no configurado/desactivado → contacto | ✅ | Zona no encontrada → `to_agree`/contacto. |

## HU-ENV-03 · Envío a convenir con contacto

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Indicación + contacto en la ficha | ✅ | `_product_shipping_out.to_agree` + `store_contact`. |
| 2 | Resumen sin envío incluido | ✅ | Checkout a convenir con costo 0 y mensaje. |
| 3 | Contacto en el detalle del pedido | ✅ | `OrderOut.shipping_to_agree` + `OrderOut.store_contact`. |

## HU-ENV-04 · Envío gratis con vigencia

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Envío gratis por lugar | ✅ | `shipping_zones[].free_shipping`. |
| 2 | Monto mínimo no alcanzado cobra e informa | ✅ | `free_shipping_min_subtotal` / umbral con mensaje de faltante. |
| 3 | Fuera de vigencia vuelve a cobrar | ✅ | `_free_shipping_window_active` valida `free_shipping_from`/`free_shipping_to`. |
| 4 | Envío gratis para toda la tienda | ✅ | `shipping_free_threshold` a nivel tienda. |

## HU-ENV-05 · Seguimiento del envío

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Actualización notifica al comprador | ✅ | `PATCH .../shipment` + `shipment_status_to_buyer`. |
| 2 | Nota/referencia visible | ✅ | `ShipmentEvent.note` en la línea de tiempo. |
| 3 | Línea de tiempo de solo lectura | ✅ | `GET /orders/{id}/shipment` (`ShipmentOut.events`). |
| 4 | Sin actualizaciones no inventa tracking | ✅ | Sin envío devuelve `status=pending`, `events=[]`. |

**Endpoints:** `PATCH /api/v1/seller/orders/{order_id}/shipment` (`ShipmentUpdateIn`) · `GET /api/v1/orders/{order_id}/shipment` (`ShipmentOut`).

## HU-ENV-06 · Devoluciones con reingreso condicional

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Devolución con reingreso | ✅ | `POST .../return` `restock=true` → `restock_order` (movimiento `return_in`). |
| 2 | Devolución sin reingreso (dañado) | ✅ | `restock=false` → no repone, guarda el motivo en `cancel_reason`. |
| 3 | El comprador ve el resultado | ✅ | Pedido `returned` + motivo en el detalle. |
| 4 | Pedido no despachado no se devuelve | ✅ | Exige `shipped`/`delivered` (409 si no). |

**Endpoint:** `POST /api/v1/seller/orders/{order_id}/return` (`OrderReturnIn`: `restock`, `reason`).

---

## Notas para frontend

- El estado de **envío** (`ShipmentOut.status`: preparing/shipped/in_transit/delivered/returned) es independiente del estado del **pedido** (`OrderOut.status`) y del **pago**.
- La línea de tiempo del envío es de solo lectura para el comprador; la actualiza el vendedor.
- `OrderOut.shipping_to_agree` indica que el envío se coordina con el vendedor; usar `OrderOut.store_contact` para mostrar cómo contactarlo.
- Envío gratis con vigencia: `free_shipping_from`/`free_shipping_to` (ISO date) a nivel tienda y por zona; fuera de la ventana se cobra la tarifa.
- Override por producto: `ProductOut.shipping_mode` (`to_agree` fuerza a convenir; `own_rates` fuerza tarifas de tienda; `null` hereda).
- Devoluciones: solo aplican a pedidos `shipped`/`delivered`; `restock=false` no reintegra stock (producto dañado).

## Cómo correr los tests

Los tests de la épica son de integración contra las **APIs reales sobre la BD** (autorizado por el usuario). La fixture `real_db_context` usa **aislamiento por transacción + rollback**: nada de lo que crean los tests queda persistido (limpieza garantizada, sin `DELETE`/`TRUNCATE`/`DROP`). Requieren la migración `0013` aplicada en la BD.

```bash
.venv\Scripts\python.exe -m pytest tests -v -m integration -k env
```

El contrato Swagger y el smoke de arranque corren siempre (SQLite):

```bash
.venv\Scripts\python.exe -m pytest tests -q -k "env_openapi or boot"
```
