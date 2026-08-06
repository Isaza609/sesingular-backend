# Epica 10: Pagos

**Épica ID:** 10
**Módulo / prefijo HU:** PAG
**Swagger tags:** `payments`, `seller`, `buyer`, `admin`, `catalog`
**Prefijos de rutas:** `/api/v1/payments`, `/api/v1/seller`, `/api/v1/orders`, `/api/v1/admin`, `/api/v1/catalog`
**Autenticación:** `Authorization: Bearer <JWT Supabase>` (el webhook y las opciones de pago son públicos)
**Scope:** comprador (lo suyo) · tienda del vendedor (lo suyo) · plataforma (admin)
**Última actualización:** 2026-08-05

---

## Resumen del módulo

La Épica 10 cubre todo el ciclo de pago del marketplace:

- **Selección y pago:** el comprador elige entre los métodos habilitados por la tienda (pasarela automatizada, transferencia bancaria o Bre-B) y paga.
- **Pasarela:** intento de pago y confirmación vía webhook, con validación de firma.
- **Cobro manual:** el vendedor registra cuentas de cobro (banco/Bre-B); el comprador sube el comprobante; el vendedor lo confirma, rechaza o registra una novedad por monto incorrecto.
- **Novedad por monto:** si faltó dinero, el pago pasa a `pago_incompleto` y se reabre la carga; si sobró, se registra el acuerdo y la devolución se coordina por fuera.
- **Conciliación:** toda transacción queda registrada con su estado y un historial de estados anteriores, consultable por el administrador.

### Estados de pago (`marketplace.payment_status`)

| Enum código | Significado funcional |
|---|---|
| `pending` | `pendiente_pago`: aún sin comprobante |
| `in_review` | `comprobante_subido`: esperando revisión del vendedor |
| `incomplete` | `pago_incompleto`: recibido de menos, carga reabierta (HU-PAG-07) |
| `paid` | `pago_confirmado` |
| `rejected` | `pago_rechazado` |
| `refunded` | `reembolsado` |

### Modelo de datos

- `payments`: estado vigente + rastro del pago manual (`payout_account_id`, `receipt_path`, `received_amount`, `review_note`, `agreement_note`, ...).
- `payment_events`: bitácora inmutable de transiciones (`from_status`, `to_status`, `actor_role`, `actor_user_id`, `received_amount`, `note`, `created_at`). Alimenta la conciliación (HU-PAG-09).
- `payout_accounts`: cuentas de cobro manual de la tienda (banco/Bre-B), con baja lógica.

Toda transición de estado pasa por `app/modules/payments/service.py` (`transition` / `record_event`), que mantiene sincronizados el estado vigente y la bitácora, y aplica los efectos deterministas (confirmar pedido, reponer stock).

Migración: `alembic/versions/0011_payments_epica10.py`.

---

## Índice de HUs implementadas

| HU | Título | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-PAG-01 | Selección del método de pago | 2026-08-05 | `GET /api/v1/catalog/stores/{id}/payment-options` | `tests/test_hu_pag_01_payment_methods_checkout.py` |
| HU-PAG-02 | Pago por pasarela + webhook | 2026-08-05 | `POST /api/v1/payments/orders/{id}/intent`, `POST /api/v1/payments/webhooks/{provider}` | `tests/test_hu_pag_02_gateway_payment.py` |
| HU-PAG-03 | Cuentas de cobro manual | 2026-08-05 | `GET/POST /api/v1/seller/payout-accounts` | `tests/test_hu_pag_03_payout_accounts.py` |
| HU-PAG-04 | Activar/desactivar cuenta | 2026-08-05 | `PATCH/DELETE /api/v1/seller/payout-accounts/{id}` | `tests/test_hu_pag_03_payout_accounts.py` |
| HU-PAG-05 | Subir comprobante | 2026-08-05 | `GET /api/v1/orders/{id}/payment`, `POST /api/v1/orders/{id}/payment/receipt` | `tests/test_hu_pag_05_receipt_upload.py` |
| HU-PAG-06 | Revisión del vendedor | 2026-08-05 | `GET /api/v1/seller/payments`, `POST .../{id}/confirm`, `POST .../{id}/reject` | `tests/test_hu_pag_06_seller_review.py` |
| HU-PAG-07 | Novedad y reapertura | 2026-08-05 | `POST /api/v1/seller/payments/{id}/reopen`, `POST .../{id}/overpaid` | `tests/test_hu_pag_07_payment_novelty_reopen.py` |
| HU-PAG-08 | Notificaciones de pago manual | 2026-08-05 | (efectos de HU-PAG-05/06/07) | `tests/test_hu_pag_08_manual_payment_notifications.py` |
| HU-PAG-09 | Registro y conciliación | 2026-08-05 | `GET /api/v1/admin/transactions`, `GET /api/v1/admin/transactions/{id}` | `tests/test_hu_pag_09_transactions_reconciliation.py` |

---

## HU-PAG-01 · Selección del método de pago en el checkout

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_01_payment_methods_checkout.py`

### Criterios de aceptación

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Pasarela + manual → ve ambas opciones | ✅ | `payment_options_for_store` incluye métodos de pasarela y manuales según configuración. |
| 2 | Elegir transfer/Bre-B → elegir entre cuentas activas | ✅ | La respuesta trae `payout_accounts` activas del tipo habilitado. |
| 3 | Un solo método habilitado → solo esa opción | ✅ | Los métodos deshabilitados no se agregan a `payment_methods`. |

### Endpoint

`GET /api/v1/catalog/stores/{store_id}/payment-options` → 200 (público). Devuelve `payment_methods` y `payout_accounts` disponibles.

---

## HU-PAG-02 · Pago mediante pasarela automatizada

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_02_gateway_payment.py`

### Criterios de aceptación

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Pago confirmado → estado pago_confirmado | ✅ | Webhook `approved`/`paid` → `transition(paid)`; pedido pasa a confirmado. |
| 2 | Pago rechazado → ve motivo y reintenta | ✅ | Webhook `rejected` registra el evento con motivo y cancela/repone; el comprador puede reintentar por otro método. |
| 3 | Confirmación registra la transacción | ✅ | `record_creation` al crear el pago y `payment_events` en cada transición. |

### Endpoints

- `POST /api/v1/payments/orders/{order_id}/intent` → 201. Crea/reutiliza el pago y registra la transacción.
- `POST /api/v1/payments/webhooks/{provider}` → 200. Valida `x-webhook-secret`; mapea el estado de la pasarela. 401 si la firma no coincide; 400 si el estado no es soportado.

---

## HU-PAG-03 · Configuración de cuentas de cobro manual

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_03_payout_accounts.py`

### Criterios de aceptación

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Registrar cuenta bancaria | ✅ | `POST /seller/payout-accounts` con `type=bank` y datos bancarios. |
| 2 | Registrar llave Bre-B | ✅ | `POST /seller/payout-accounts` con `type=bre_b` y `breb_key`. |
| 3 | Varias cuentas activas → elegibles en checkout | ✅ | `payment_options_for_store` lista todas las activas. |

Validación por tipo en `PayoutAccountIn` (banco requiere banco+número; Bre-B requiere llave) → 422. Scope de tienda → 404 en cuenta ajena.

### Endpoints

`GET /api/v1/seller/payout-accounts` · `POST /api/v1/seller/payout-accounts` → 201.

---

## HU-PAG-04 · Activar o desactivar una cuenta de cobro

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_03_payout_accounts.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Desactivar → no aparece en checkout nuevo | ✅ | `DELETE` = baja lógica (`active=false`); el checkout filtra por activas. |
| 2 | Pedido anterior conserva la referencia | ✅ | La cuenta no se borra; `payout_account_id` del pago sigue apuntando a ella. |
| 3 | Reactivar → vuelve a mostrarse | ✅ | `PATCH` con `active=true`. |

### Endpoints

`PATCH /api/v1/seller/payout-accounts/{account_id}` · `DELETE /api/v1/seller/payout-accounts/{account_id}` → 200.

---

## HU-PAG-05 · Flujo de pago manual: subir comprobante

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_05_receipt_upload.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Ver datos de destino y monto exacto | ✅ | `GET /orders/{id}/payment` devuelve `payout_account` y `amount`. |
| 2 | Subir comprobante → comprobante_subido + stock reservado | ✅ | `POST .../receipt` deja `in_review`; la reserva del checkout se mantiene. |
| 3 | Sin comprobante → pendiente_pago | ✅ | Estado inicial `pending`. |
| 4 | Reemplazo tras rechazo/reapertura | ✅ | Re-subir limpia el veredicto y vuelve a `in_review` (incluye reingreso desde `pago_incompleto`). |

### Endpoints

- `GET /api/v1/orders/{order_id}/payment` → 200 (`PaymentOut`, con `receipt_url` firmada).
- `POST /api/v1/orders/{order_id}/payment/receipt` → 200. `multipart/form-data`: `file` (JPG/PNG/PDF ≤ 5 MB) y `payout_account_id`.

---

## HU-PAG-06 · Revisión y confirmación/rechazo del comprobante

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_06_seller_review.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Confirmar → pago_confirmado, pedido continúa | ✅ | `confirm` → `transition(paid)`; pedido pendiente pasa a confirmado. |
| 2 | Rechazar → pago_rechazado, libera stock, notifica | ✅ | `reject` → `transition(rejected)` (repone stock + cancela) + correo con motivo. |
| 3 | Bandeja de pendientes | ✅ | `GET /seller/payments` (por defecto `in_review`). |

409 si el pago ya fue revisado; 404 si el pago es de otra tienda.

### Endpoints

`GET /api/v1/seller/payments` · `POST /api/v1/seller/payments/{payment_id}/confirm` · `POST /api/v1/seller/payments/{payment_id}/reject` → 200.

---

## HU-PAG-07 · Registro de novedad y reapertura por monto incorrecto

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_07_payment_novelty_reopen.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Registrar novedad con monto recibido → queda en historial | ✅ | `reopen`/`overpaid` guardan `received_amount` + `review_note` y un `payment_event`. |
| 2 | Faltó dinero → pago_incompleto + aviso con esperado/recibido/diferencia/cuenta | ✅ | `reopen` → `transition(incomplete)` + correo `payment_incomplete_to_buyer`. |
| 3 | Comprador sube saldo → vuelve a comprobante_subido | ✅ | `POST .../receipt` desde `incomplete` → `in_review`. |
| 4 | En pago_incompleto el stock sigue reservado | ✅ | `incomplete` no aplica efectos de inventario; la reserva se mantiene. |
| 5 | Pagó de más → registra acuerdo + datos de contacto, sin movimiento de dinero | ✅ | `overpaid` confirma y guarda `agreement_note`; la respuesta expone `buyer_email`/`buyer_phone`. |
| 6 | Caso irresoluble → anular (HU-PED-04) libera stock | ✅ | La anulación del pedido usa `restock_order` (Épica 12). |

### Endpoints

- `POST /api/v1/seller/payments/{payment_id}/reopen` → 200. `PaymentIncompleteIn` (`received_amount` < total). 400 si no es menor al total.
- `POST /api/v1/seller/payments/{payment_id}/overpaid` → 200. `PaymentOverpaidIn` (constancia del acuerdo).

---

## HU-PAG-08 · Notificaciones del estado de pago manual

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_08_manual_payment_notifications.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Subida → confirmación al comprador | ✅ | `receipt_uploaded_to_buyer`. |
| 2 | Resultado (confirmado/rechazado/incompleto) al comprador | ✅ | `payment_confirmed_to_buyer` / `payment_rejected_to_buyer` / `payment_incomplete_to_buyer`. |
| 3 | Pendiente de revisión → aviso al vendedor | ✅ | `receipt_uploaded_to_seller`. |

Los correos se envían vía `BackgroundTasks` y nunca rompen el flujo de pago (Resend; si no está configurado, se registra y sigue).

---

## HU-PAG-09 · Registro y conciliación de transacciones

**Fecha:** 2026-08-05 · **Estado:** Implementada · **Tests:** `tests/test_hu_pag_09_transactions_reconciliation.py`

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Toda transacción queda registrada con su estado y pedido | ✅ | `record_creation` al crear el pago; estado vigente en `payments`. |
| 2 | El historial conserva los estados anteriores | ✅ | Cada transición inserta un `payment_event` con `from_status`/`to_status`. |
| 3 | Ver a qué pedido, tienda y método corresponde | ✅ | `TransactionOut` incluye `order_id`, `store_id`, `method`. |

Acceso restringido a `admin` (`require_admin`) → 403 para otros roles.

### Endpoints

- `GET /api/v1/admin/transactions` → 200 (`TransactionListOut`). Filtros: `status`, `store_id`, `method`, `order_id`, `date_from`, `date_to`.
- `GET /api/v1/admin/transactions/{payment_id}` → 200 (`TransactionOut` con `events`).

---

## Notas y advertencias para frontend

- **Estados de pago:** usar los códigos del enum (`pending`, `in_review`, `incomplete`, `paid`, `rejected`, `refunded`); el mapeo funcional (pendiente_pago, comprobante_subido, pago_incompleto, ...) está en la tabla de arriba.
- **`difference`** en `PaymentOut`/`SellerPaymentOut` es `amount − received_amount` (positivo = falta dinero); solo aparece cuando hay `received_amount`.
- **Reapertura:** desde `incomplete` el comprador vuelve a usar `POST /orders/{id}/payment/receipt`; el pago regresa a `in_review`.
- **Monto de más:** la plataforma **no** procesa devoluciones; el acuerdo se registra en `agreement_note` y el vendedor usa `buyer_email`/`buyer_phone` para coordinar por fuera.
- **Comprobantes:** `receipt_url` es una URL firmada temporal (bucket privado); solo se entrega en el detalle.
- **Webhook:** requiere header `x-webhook-secret` si la plataforma configuró `webhook_secret` en `payment_gateway`.

## Cómo correr los tests

Las pruebas de la épica son de integración contra las APIs reales sobre PostgreSQL. Requieren una **BD de test dedicada** (nunca producción) vía `TEST_DATABASE_URL`:

```bash
# PowerShell (BD de test dedicada, p. ej. Postgres local)
$env:TEST_DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/singular_test"
.venv\Scripts\python.exe -m pytest tests -v -m integration -k pag
```

Sin `TEST_DATABASE_URL` (o si apunta a producción) los tests de integración se **saltan** por seguridad. El contrato Swagger corre siempre:

```bash
.venv\Scripts\python.exe -m pytest tests -q -k pag_openapi
```
