# Epica 11: Facturación al comprador

**Épica ID:** 11
**Módulo / prefijo HU:** FAC
**Swagger tags:** `invoices`, `seller-invoices`, `admin`, `seller`
**Prefijos de rutas:** `/api/v1/orders/{id}/invoice`, `/api/v1/seller/invoices`, `/api/v1/admin/stores`, `/api/v1/seller/store`
**Autenticación:** `Authorization: Bearer <JWT Supabase>`
**Scope:** comprador (lo suyo) · tienda del vendedor (lo suyo) · plataforma (admin)
**Última actualización:** 2026-08-06

---

## Resumen del módulo

Genera el **comprobante de venta** entre el vendedor y el comprador una vez confirmado el pago. El comprobante toma **snapshots** de los datos fiscales de la tienda, del comprador, de los items y de los cargos, de modo que correcciones o ediciones posteriores no alteran documentos ya emitidos. La plataforma no calcula impuestos; los cargos extra del vendedor (HU-PROM-04) se muestran desglosados uno a uno y el envío "a convenir" no se factura.

### Modelo

- `Invoice` (`invoices`): `number` (secuencial por tienda), `order_id` (único), `store_id`, `buyer_id`, `status` (`issued`/`cancelled`/`returned`), totales, `shipping_to_convenir`, y snapshots JSON `store_fiscal`/`buyer_snapshot`/`items_snapshot`/`charges_snapshot`. Un comprobante por pedido (idempotente).
- `Store` gana campos fiscales: `legal_name`, `tax_id`, `fiscal_address` (los edita el admin).
- Emisión: enganchada a `payments/service.transition` cuando el pago pasa a `paid` (cubre pasarela y pago manual). Módulo: `app/modules/invoices/`. Migración: `0012_invoices_orders_epica11_12.py`.

---

## Índice de HUs implementadas

| HU | Título | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-FAC-01 | Emisión del comprobante | 2026-08-06 | `GET /orders/{id}/invoice`, `GET /orders/{id}/invoice/download` | `tests/test_hu_fac_01_invoice_issue.py` |
| HU-FAC-02 | Datos fiscales de la tienda | 2026-08-06 | `PATCH /admin/stores/{id}`, `GET /seller/store` | `tests/test_hu_fac_02_store_fiscal_data.py` |
| HU-FAC-03 | Comprobantes de la tienda | 2026-08-06 | `GET /seller/invoices`, `GET /seller/invoices/{id}[/download]` | `tests/test_hu_fac_03_seller_invoices.py` |

---

## HU-FAC-01 · Emisión del comprobante de venta

**Fecha:** 2026-08-06 · **Estado:** Implementada · **Tests:** `tests/test_hu_fac_01_invoice_issue.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Pago confirmado → genera comprobante descargable | ✅ | `issue_invoice` se dispara en la transición a `paid` (idempotente por pedido). |
| 2 | Descarga desde pedido pasado | ✅ | `GET /orders/{id}/invoice/download` (HTML autocontenido). |
| 3 | Cargos extra desglosados uno a uno | ✅ | `charges_snapshot` con cada `OrderAdjustment` por separado. |
| 4 | Envío a convenir no facturado | ✅ | `shipping_to_convenir` cuando la tienda es `to_agree` y `shipping_cost=0`. |
| 5 | Refleja cancelación/devolución | ✅ | `sync_invoice_status` actualiza el `status` del comprobante. |

### Endpoints

- `GET /api/v1/orders/{order_id}/invoice` → 200 (`InvoiceOut`). 404 si el pedido no es del comprador o no hay comprobante.
- `GET /api/v1/orders/{order_id}/invoice/download` → 200 `text/html`.

---

## HU-FAC-02 · Datos de facturación del vendedor

**Fecha:** 2026-08-06 · **Estado:** Implementada · **Tests:** `tests/test_hu_fac_02_store_fiscal_data.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Datos fiscales presentes en el comprobante | ✅ | `store_fiscal` snapshotea `legal_name`, `tax_id`, `fiscal_address` y contacto. |
| 2 | Corrección aplica solo a comprobantes nuevos | ✅ | El snapshot se toma al emitir; los ya emitidos conservan el dato original. |
| 3 | El vendedor consulta sus datos fiscales | ✅ | `GET /seller/store` los expone (solo lectura; los edita el admin). |

### Endpoints

- `PATCH /api/v1/admin/stores/{store_id}` → 200 (`StoreOut`): admin registra/corrige `legal_name`/`tax_id`/`fiscal_address`.
- `GET /api/v1/seller/store` → 200 (`SellerStoreOut`): el vendedor consulta (solo lectura).

---

## HU-FAC-03 · Consulta de comprobantes por la tienda

**Fecha:** 2026-08-06 · **Estado:** Implementada · **Tests:** `tests/test_hu_fac_03_seller_invoices.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Listado con fecha, comprador, pedido y monto | ✅ | `GET /seller/invoices` (`InvoiceListItemOut`). |
| 2 | Filtro por fecha o estado | ✅ | Query `date_from`/`date_to`/`status`. |
| 3 | Descarga en el mismo formato | ✅ | `GET /seller/invoices/{id}/download` (HTML). |

Scope: limitado a la tienda del vendedor; 404 en comprobante ajeno.

### Endpoints

`GET /api/v1/seller/invoices` · `GET /api/v1/seller/invoices/{invoice_id}` · `GET /api/v1/seller/invoices/{invoice_id}/download`.

---

## Notas para frontend

- El comprobante se genera automáticamente al confirmarse el pago; antes de eso, `GET .../invoice` responde 404.
- La descarga es un documento **HTML autocontenido** (estilos inline): puede mostrarse en un iframe/nueva pestaña y exportarse a PDF con la impresión del navegador.
- Los datos fiscales son de **solo lectura** para el vendedor; se corrigen desde el panel de administración.
- Estados del comprobante: `issued`, `cancelled`, `returned` (siguen al estado del pedido).
