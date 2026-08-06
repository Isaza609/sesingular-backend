# Epica 12: Gestión de pedidos

**Épica ID:** 12
**Módulo / prefijo HU:** PED
**Swagger tags:** `buyer`, `seller`, `seller-orders`
**Prefijos de rutas:** `/api/v1/orders`, `/api/v1/seller/orders`
**Autenticación:** `Authorization: Bearer <JWT Supabase>`
**Scope:** comprador (lo suyo) · tienda del vendedor (lo suyo)
**Última actualización:** 2026-08-06

---

## Resumen del módulo

Gestión del pedido después de la compra: seguimiento de estados (independiente del pago), notificaciones automáticas de cambio de estado, historial con filtros, anulación por el vendedor con motivo (libera stock), y asignación manual del responsable dentro del equipo de la tienda con historial de reasignaciones.

### Modelo

- `Order` gana `assignee_id` (FK users, SET NULL), `assigned_at` y `cancel_reason`.
- `OrderAssignmentEvent` (`order_assignment_events`): historial de reasignaciones (`from_user_id`, `to_user_id`, `actor_user_id`, `created_at`).
- Estados del pedido (`OrderStatus`): `pending`, `confirmed`, `preparing`, `shipped`, `delivered`, `cancelled`, `returned`. Transiciones validadas por `_assert_transition`.
- Migración: `0012_invoices_orders_epica11_12.py`.

---

## Índice de HUs implementadas

| HU | Título | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-PED-01 | Seguimiento de estados | 2026-08-06 | `GET /orders/{id}`, `PATCH /seller/orders/{id}/status` | `tests/test_hu_ped_01_order_status_tracking.py` |
| HU-PED-02 | Notificaciones de estado | 2026-08-06 | (efecto de `PATCH .../status` y anulación) | `tests/test_hu_ped_02_status_notifications.py` |
| HU-PED-03 | Historial con filtros | 2026-08-06 | `GET /orders`, `GET /seller/orders` | `tests/test_hu_ped_03_order_history_filters.py` |
| HU-PED-04 | Anulación con motivo | 2026-08-06 | `POST /seller/orders/{id}/cancel` | `tests/test_hu_ped_04_seller_cancel_order.py` |
| HU-PED-05 | Asignación de responsable | 2026-08-06 | `PATCH /seller/orders/{id}/assignee`, `GET /seller/orders?assignee=` | `tests/test_hu_ped_05_order_assignment.py` |

---

## HU-PED-01 · Seguimiento de estados

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Estado del pedido y del pago por separado | ✅ | `OrderOut.status` (pedido) y `OrderOut.payments[].status` (pago). |
| 2 | Actualización refleja de inmediato para el comprador | ✅ | El comprador consulta `GET /orders/{id}` y ve el estado actualizado. |

Transición inválida → 409 (`_assert_transition`). **Tests:** `tests/test_hu_ped_01_order_status_tracking.py`.

## HU-PED-02 · Notificaciones de cambio de estado

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Cada cambio notifica al comprador | ✅ | `order_status_changed_to_buyer` vía `BackgroundTasks` en `PATCH .../status`. |
| 2 | Al despachar, comprador y vendedor | ✅ | Al pasar a `shipped` se notifica también al correo de la tienda. |

**Tests:** `tests/test_hu_ped_02_status_notifications.py` (correo mockeado).

## HU-PED-03 · Historial con filtros

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Comprador ve todos sus pedidos | ✅ | `GET /orders` filtrado por `buyer_id`. |
| 2 | Vendedor ve solo su tienda | ✅ | `GET /seller/orders` filtrado por `store_id`. |
| 3 | Filtro por fecha o estado | ✅ | Query `status`, `date_from`, `date_to` en ambos listados. |

**Tests:** `tests/test_hu_ped_03_order_history_filters.py`.

## HU-PED-04 · Anulación por el vendedor con motivo

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Sin expiración automática | ✅ | No hay job que cancele; la anulación es siempre manual. |
| 2 | Anular con motivo libera stock | ✅ | `POST /seller/orders/{id}/cancel` → `restock_order` + `cancel_reason` + `cancelled`. |
| 3 | Notificación con motivo | ✅ | `order_cancelled_to_buyer`. |
| 4 | Despachado/entregado no se anula | ✅ | 409 "tratar como devolución" (HU-ENV-06). |
| 5 | Liberación registrada en inventario | ✅ | `InventoryMovement` con `reason=release` y `order_id`. |

**Endpoint:** `POST /api/v1/seller/orders/{order_id}/cancel` (`OrderCancelIn.reason`). **Tests:** `tests/test_hu_ped_04_seller_cancel_order.py`.

## HU-PED-05 · Asignación de responsable

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | Pedido nuevo sin responsable | ✅ | `assignee_id` nulo por defecto. |
| 2 | Asignar visible para el equipo | ✅ | `PATCH .../assignee`; `OrderOut.assignee_id`. |
| 3 | Reasignación registrada con usuario anterior | ✅ | `OrderAssignmentEvent` con `from_user_id`/`to_user_id`/fecha. |
| 4 | Filtro por responsable (incluye "sin asignar") | ✅ | `GET /seller/orders?assignee=<id|unassigned>`. |
| 5 | Asignar a usuario ajeno rechazado | ✅ | Valida `StoreMember`; 400 si no pertenece. |
| 6 | Acceso pese a responsable distinto | ✅ | La asignación no restringe: cualquier miembro puede actuar. |

**Endpoint:** `PATCH /api/v1/seller/orders/{order_id}/assignee` (`OrderAssigneeIn.assignee_id`, null para desasignar). **Tests:** `tests/test_hu_ped_05_order_assignment.py`.

---

## Notas para frontend

- El estado del pedido es independiente del estado de pago; mostrarlos por separado (`status` vs `payments[].status`).
- Para despachar (`shipped`) con reserva multi-almacén hay que asignar antes el almacén (`PATCH .../warehouse`, HU-INV-03).
- La anulación (`/cancel`) exige `reason` y falla con 409 si el pedido ya fue despachado/entregado.
- La asignación de responsable es organizativa: no bloquea a otros miembros; `assignee=unassigned` filtra los pendientes de tomar.
- Las notificaciones se envían por correo (Resend) en segundo plano; nunca rompen la operación.
