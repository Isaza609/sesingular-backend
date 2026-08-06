# Epica 07: Canal de venta (online / presencial)

**Epica ID:** 07
**Modulo / prefijo HU:** CANAL
**Swagger tag:** `seller`, `buyer`
**Prefijo de rutas:** `/api/v1/checkout`, `/api/v1/seller`
**Autenticacion:** `Authorization: Bearer <JWT Supabase>`
**Scope:** comprador autenticado / tienda del vendedor autenticado
**Ultima actualizacion:** 2026-08-05

---

## Resumen del modulo

Esta epica permite distinguir el origen de cada pedido entre venta online y venta presencial. El checkout buyer registra ventas `online`; el mini-POS seller registra ventas `presencial`, descuenta inventario de inmediato y crea un pago POS pagado. El seller tambien puede consultar un reporte comparativo por canal en un rango de fechas.

---

## Indice de HUs implementadas

| HU | Titulo | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-CANAL-01 | Registro de canal de origen de la transaccion | 2026-08-05 | `POST /api/v1/checkout`, `POST /api/v1/seller/pos/orders`, `PATCH /api/v1/seller/orders/{order_id}/status` | `tests/test_hu_canal_01_order_channel.py` |
| HU-CANAL-02 | Venta rapida / mini-POS | 2026-08-05 | `POST /api/v1/seller/pos/orders` | `tests/test_hu_canal_02_pos_sales.py` |
| HU-CANAL-03 | Reportes comparativos de ventas online vs. presenciales | 2026-08-05 | `GET /api/v1/seller/reports/sales` | `tests/test_hu_canal_03_sales_channel_report.py` |

---

## HU-CANAL-01 - Registro de canal de origen de la transaccion

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_canal_01_order_channel.py`

### Descripcion funcional

Cada pedido conserva el canal de origen desde su creacion. Los pedidos generados por checkout buyer quedan como `online`; las ventas creadas por mini-POS seller quedan como `presencial`. El canal se expone en `OrderOut` y no cambia cuando el seller actualiza el estado operativo del pedido.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Una compra desde tienda online queda con canal `online`. | Si | `POST /api/v1/checkout` crea `Order(channel=SaleChannel.online)` y la respuesta incluye `channel`. |
| 2 | Una venta desde mini-POS queda con canal `presencial`. | Si | `POST /api/v1/seller/pos/orders` crea `Order(channel=SaleChannel.presencial)`. |

### Flujo implementado

```text
1. Buyer llama POST /api/v1/checkout con carrito y direccion.
2. Backend crea pedidos por tienda con channel=online.
3. Seller llama POST /api/v1/seller/pos/orders para venta presencial.
4. Backend crea el pedido POS con channel=presencial.
5. PATCH /api/v1/seller/orders/{order_id}/status actualiza estado sin modificar channel.
```

### Endpoints implementados en esta HU

#### POST `/api/v1/checkout` -> 201

**Descripcion:** Crea pedidos online para el comprador autenticado y registra `channel=online`.
**Roles permitidos:** `buyer`
**Archivo:** `app/modules/orders/router.py`

**Headers requeridos:**
| Header | Valor |
|---|---|
| `Authorization` | `Bearer <JWT>` |

**Request body:**
```json
{
  "address_id": "addr-123",
  "payment_method": "card",
  "coupon_code": "VERANO10",
  "payout_account_id": null,
  "notes": "Entregar en porteria"
}
```

**Response exitosa:** objeto con `orders`, cada pedido compatible con `OrderOut` e incluyendo `channel`.

**Errores posibles:**
| Codigo | Situacion | Mensaje tipico |
|---|---|---|
| 400 | Carrito vacio, cupon invalido o metodo no disponible | `"El carrito esta vacio"` |
| 401 | Sin autenticacion | `"Token invalido o expirado"` |
| 403 | Direccion fuera del comprador | `"La direccion no pertenece al usuario"` |
| 409 | Stock insuficiente | `"Stock insuficiente"` |
| 422 | Validacion Pydantic | Array `detail` |

#### POST `/api/v1/seller/pos/orders` -> 201

**Descripcion:** Crea pedido presencial para la tienda del seller autenticado y registra `channel=presencial`.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/seller/router.py`

**Headers requeridos:**
| Header | Valor |
|---|---|
| `Authorization` | `Bearer <JWT>` |

**Request body:**
```json
{
  "items": [
    {"variant_id": "variant-123", "quantity": 2}
  ],
  "buyer_id": null,
  "payment_method": "cash",
  "notes": "Cliente retira en caja"
}
```

**Response exitosa:** `OrderOut` con `channel="presencial"`, `status="delivered"` y pago POS.

### Tests de esta HU

- Archivo: `tests/test_hu_canal_01_order_channel.py`
- Cubre: canal `online` en checkout, canal `presencial` en mini-POS y estabilidad del canal ante cambio de estado.
- Ejecucion: `pytest tests/test_hu_canal_01_order_channel.py -v`

### Notas y advertencias para frontend

- `channel` solo acepta `online` o `presencial`.
- Frontend no debe enviar `channel`; el backend lo define segun el flujo.
- Cambios de estado no modifican el canal.

---

## HU-CANAL-02 - Venta rapida / mini-POS

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_canal_02_pos_sales.py`

### Descripcion funcional

El seller puede registrar ventas presenciales desde su panel sin exigir cuenta de comprador. El backend valida almacen activo, variantes propias, comprador opcional si se envia, disponibilidad real por almacen y evita pedidos parciales. Si todo es valido, crea el pedido presencial entregado, descuenta inventario y registra pago POS pagado.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Al confirmar productos y cantidades, se descuenta inventario de inmediato. | Si | POS prevalida stock y ejecuta `consume_variant(..., order_id=order.id, warehouse_id=warehouse.id)`. |
| 2 | No se requiere que el comprador tenga cuenta. | Si | `buyer_id` es opcional y el pedido permite `buyer_id=null`. |
| 3 | Vender mas de lo disponible rechaza indicando disponibilidad real. | Si | POS responde `409` con `Disponible: {available}` antes de crear pedido o descontar inventario. |

### Flujo implementado

```text
1. Seller llama POST /api/v1/seller/pos/orders.
2. Backend selecciona almacen default activo o primer almacen activo.
3. Valida comprador opcional, variantes activas y pertenencia a la tienda.
4. Agrupa cantidades por variante y valida disponibilidad real.
5. Crea pedido presencial delivered.
6. Descuenta inventario y registra movimientos sale con order_id.
7. Crea Payment provider=pos, status=paid.
8. Retorna OrderOut.
```

### Endpoints implementados en esta HU

#### POST `/api/v1/seller/pos/orders` -> 201

**Descripcion:** Crea venta presencial mini-POS para la tienda autenticada.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/seller/router.py`

**Headers requeridos:**
| Header | Valor |
|---|---|
| `Authorization` | `Bearer <JWT>` |

**Request body:**
```json
{
  "items": [
    {"variant_id": "variant-123", "quantity": 2}
  ],
  "buyer_id": null,
  "payment_method": "cash",
  "notes": "Cliente retira en caja"
}
```

| Campo | Tipo | Req/Opt | Descripcion |
|---|---|---|---|
| `items` | `array` | requerido | Variantes y cantidades a vender. |
| `buyer_id` | `string|null` | opcional | Comprador existente, o `null` para venta anonima. |
| `payment_method` | `string` | requerido | Metodo presencial, por ejemplo `cash`. |
| `notes` | `string|null` | opcional | Nota interna de la venta. |

**Response exitosa:**
```json
{
  "id": "order-123",
  "buyer_id": null,
  "channel": "presencial",
  "status": "delivered",
  "total": 90000,
  "payments": [
    {"provider": "pos", "method": "cash", "status": "paid", "amount": 90000, "currency": "COP"}
  ]
}
```

**Errores posibles:**
| Codigo | Situacion | Mensaje tipico |
|---|---|---|
| 400 | Tienda sin almacen activo | `"Debes registrar un almacen antes de vender"` |
| 401 | Sin autenticacion | `"Token invalido o expirado"` |
| 403 | Rol no permitido | `"Requiere rol seller"` |
| 404 | Comprador inexistente o variante fuera de tienda | `"Una variante no pertenece a tu tienda"` |
| 409 | Stock insuficiente | `"Stock insuficiente para SKU. Disponible: 1"` |
| 422 | Validacion Pydantic | Array `detail` |

### Tests de esta HU

- Archivo: `tests/test_hu_canal_02_pos_sales.py`
- Cubre: venta sin comprador, descuento inmediato, pago POS pagado, stock insuficiente con disponibilidad real, comprador inexistente, variante fuera de tienda, tienda sin almacen activo y ausencia de descuentos parciales.
- Ejecucion: `pytest tests/test_hu_canal_02_pos_sales.py -v`

### Notas y advertencias para frontend

- No enviar `store_id`; el backend usa la tienda del seller autenticado.
- `buyer_id` puede omitirse. Si se envia, debe existir.
- Para stock insuficiente, mostrar al seller el valor de `Disponible`.

---

## HU-CANAL-03 - Reportes comparativos de ventas online vs. presenciales

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_canal_03_sales_channel_report.py`

### Descripcion funcional

El seller consulta un reporte de ventas por canal para su tienda autenticada. El rango `date_from` y `date_to` es inclusivo por dia. El reporte excluye pedidos cancelados, no mezcla ventas de otras tiendas y siempre retorna filas para `online` y `presencial`, aunque un canal no tenga ventas.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | El reporte muestra ventas online y presenciales por separado y su suma. | Si | `GET /api/v1/seller/reports/sales` retorna `by_channel` y `totals`. |
| 2 | Si no hay ventas de un canal, se muestra cero sin error. | Si | El reporte itera siempre `SaleChannel.online` y `SaleChannel.presencial`. |

### Flujo implementado

```text
1. Seller llama GET /api/v1/seller/reports/sales con date_from/date_to opcionales.
2. Backend filtra pedidos por store.id del seller y excluye cancelled.
3. Aplica rango de fechas inclusivo por dia.
4. Calcula online y presencial por separado.
5. Calcula totals como suma de canales y retorna el reporte.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/seller/reports/sales` -> 200

**Descripcion:** Retorna reporte comparativo de ventas online vs presenciales.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/seller/router.py`

**Headers requeridos:**
| Header | Valor |
|---|---|
| `Authorization` | `Bearer <JWT>` |

**Query params:**
| Param | Tipo | Req/Opt | Descripcion |
|---|---|---|---|
| `date_from` | `date` | opcional | Fecha inicial inclusiva, formato `YYYY-MM-DD`. |
| `date_to` | `date` | opcional | Fecha final inclusiva, formato `YYYY-MM-DD`. |

**Response exitosa:**
```json
{
  "totals": {
    "orders": 2,
    "gross": 50000,
    "costs": 20000,
    "platform_fees": 0,
    "profit": 30000
  },
  "by_channel": [
    {"channel": "online", "orders": 1, "gross": 20000},
    {"channel": "presencial", "orders": 1, "gross": 30000}
  ]
}
```

**Errores posibles:**
| Codigo | Situacion | Mensaje tipico |
|---|---|---|
| 401 | Sin autenticacion | `"Token invalido o expirado"` |
| 403 | Rol no permitido | `"Requiere rol seller"` |
| 404 | Tienda no encontrada | `"Recurso no encontrado"` |
| 422 | Fecha invalida | Array `detail` |

### Tests de esta HU

- Archivo: `tests/test_hu_canal_03_sales_channel_report.py`
- Cubre: separacion por canal, suma total, canal sin ventas en cero, rango de fechas, scope de tienda y exclusion de cancelados.
- Ejecucion: `pytest tests/test_hu_canal_03_sales_channel_report.py -v`

### Notas y advertencias para frontend

- El frontend puede renderizar siempre dos filas porque `online` y `presencial` vienen garantizadas.
- `date_from` y `date_to` son inclusivos.
- `gross` y `totals.gross` estan en COP enteros.

---

## Tests y contrato OpenAPI de cierre

- Tests HU: `tests/test_hu_canal_01_order_channel.py`, `tests/test_hu_canal_02_pos_sales.py`, `tests/test_hu_canal_03_sales_channel_report.py`
- Contrato OpenAPI: `tests/test_canal_openapi_contract.py`
- Ejecucion focalizada: `pytest tests -v -k "hu_canal or canal_openapi"`
