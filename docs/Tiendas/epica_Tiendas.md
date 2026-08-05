# Epica 02: Gestion de tiendas

**Epica ID:** 02
**Modulo / prefijo HU:** TDA
**Swagger tags:** `catalog`, `seller-catalog`, `seller-inventory`
**Prefijos de rutas:** `/api/v1/catalog`, `/api/v1/seller`
**Autenticacion:** `Authorization: Bearer <JWT Supabase>` en rutas seller; rutas catalogo publicas.
**Scope:** tienda del vendedor / catalogo publico.
**Ultima actualizacion:** 2026-08-05

---

## Resumen del modulo

Esta epica permite que el vendedor mantenga la informacion publica de su tienda, registre puntos o almacenes para operar inventario y defina los metodos de pago aceptados. La creacion, eliminacion y datos administrados de la tienda siguen fuera del alcance del vendedor.

---

## Indice de HUs implementadas

| HU | Titulo | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-TDA-01 | Edicion de la informacion publica de la tienda | 2026-08-05 | `GET/PATCH /api/v1/seller/store`, `GET /api/v1/catalog/stores` | `tests/test_hu_tda_01_store_profile.py` |
| HU-TDA-02 | Registro de puntos/almacenes de la tienda | 2026-08-05 | `GET/POST/PATCH /api/v1/seller/warehouses`, `PATCH /api/v1/seller/inventory/{variant_id}` | `tests/test_hu_tda_02_warehouses.py` |
| HU-TDA-03 | Configuracion de metodos de pago aceptados por la tienda | 2026-08-05 | `GET/PUT /api/v1/seller/store/settings`, `GET /api/v1/catalog/stores/{store_id}/payment-options`, `POST /api/v1/checkout` | `tests/test_hu_tda_03_payment_methods.py` |

---

## HU-TDA-01 · Edicion de la informacion publica de la tienda

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_tda_01_store_profile.py`

### Descripcion funcional

El vendedor puede actualizar solo la informacion publica que ven los compradores: descripcion, logo, telefono, WhatsApp, correo de contacto y enlaces a redes sociales. El nombre, slug, estado activo y datos legales/fiscales son administrados por plataforma.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Editar telefono, correo o enlaces de redes sociales y reflejarlo en ficha publica. | Si | `PATCH /seller/store` guarda campos permitidos y `GET /catalog/stores` los expone inmediatamente. |
| 2 | Actualizar logo o descripcion y verlo en catalogo. | Si | El response publico `StorePublicOut` incluye `description` y `logo_url` actualizados. |
| 3 | Intentar cambiar nombre legal o eliminar tienda no se permite e indica gestion admin. | Si | Campos administrados como `name`, `slug`, `active` o `delete` responden `400` con mensaje de administracion. |
| 4 | Enlace social invalido se rechaza senalando campo. | Si | `SellerStorePatch` valida `social_links` y FastAPI devuelve `422` sobre ese campo. |

### Flujo implementado

```text
1. Seller autenticado llama PATCH /api/v1/seller/store.
2. get_seller_store resuelve la tienda activa asociada.
3. SellerStorePatch valida formato de email, telefono y social_links.
4. Router rechaza campos administrados si llegaron como extra.
5. Se persisten campos publicos en marketplace.stores.
6. Catalogo publico devuelve la informacion actualizada.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/seller/store` -> 200

**Descripcion:** consulta la tienda asociada al vendedor autenticado.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/catalog/router.py`

**Response exitosa:** `SellerStoreOut`, con `id`, `slug`, `name`, `description`, `logo_url`, `contact_email`, `contact_phone`, `whatsapp_phone`, `social_links`, `active`.

#### PATCH `/api/v1/seller/store` -> 200

**Descripcion:** actualiza solo informacion publica editable por el vendedor.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/catalog/router.py`

**Request body:**
```json
{
  "description": "Ropa comoda producida localmente.",
  "logo_url": "https://cdn.example.com/nova/logo-v2.png",
  "contact_email": "contacto@nova.example",
  "contact_phone": "+573001112233",
  "whatsapp_phone": "+573001112233",
  "social_links": {"instagram": "https://instagram.com/nova"}
}
```

**Errores posibles:** `400` campo administrado, `401` token requerido, `403` rol no permitido, `404` tienda no activa, `422` validacion.

#### GET `/api/v1/catalog/stores` -> 200

**Descripcion:** lista tiendas activas con informacion publica de contacto.
**Roles permitidos:** publico
**Archivo:** `app/modules/catalog/router.py`

### Tests de esta HU

- `tests/test_hu_tda_01_store_profile.py`
- Cubre actualizacion de contacto/logo/descripcion, reflejo en catalogo, bloqueo de `name` y validacion de URL social.
- Ejecutar: `pytest tests/test_hu_tda_01_store_profile.py -v`

### Notas para frontend

- No enviar `name`, `slug`, `active`, datos legales ni acciones de eliminacion desde panel vendedor.
- `social_links` es un objeto `{red: url}` y cada URL debe iniciar con `http://` o `https://`.

---

## HU-TDA-02 · Registro de puntos/almacenes de la tienda

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_tda_02_warehouses.py`

### Descripcion funcional

El vendedor puede registrar almacenes de su tienda y asociarlos a stock. La desactivacion es baja logica: el almacen deja de estar disponible para operaciones nuevas, pero los historicos siguen consultables.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Registrar nuevo almacen con nombre y direccion, disponible para stock. | Si | `POST /seller/warehouses` crea el almacen; `PATCH /seller/inventory/{variant_id}` acepta almacenes activos. |
| 2 | Si solo hay un almacen, no exige seleccion manual de despacho. | Si | `WarehouseOut.requires_manual_dispatch_selection=false` cuando hay 0 o 1 almacenes activos; el primer almacen activo queda default. |
| 3 | Desactivar almacen lo quita de nuevas asignaciones sin afectar historicos. | Si | Stock nuevo rechaza almacen inactivo; movimientos historicos conservan `warehouse_id` y relacion `warehouse`. |

### Flujo implementado

```text
1. Seller crea almacenes con POST /api/v1/seller/warehouses.
2. Si es el primer almacen activo, queda como default operativo.
3. Si marca otro default, se desmarcan los demas de la misma tienda.
4. Stock y despacho validan que el almacen este activo para operaciones nuevas.
5. Movimientos historicos no se eliminan al desactivar.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/seller/warehouses` -> 200

**Descripcion:** lista almacenes activos e inactivos de la tienda.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/inventory/router.py`

#### POST `/api/v1/seller/warehouses` -> 201

**Descripcion:** crea un almacen de la tienda.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/inventory/router.py`

**Request body:**
```json
{
  "name": "Bodega principal",
  "address_line": "Calle 10 # 20-30",
  "city": "Bogota",
  "region": "Cundinamarca",
  "is_default": true,
  "active": true
}
```

#### PATCH `/api/v1/seller/warehouses/{warehouse_id}` -> 200

**Descripcion:** actualiza o desactiva un almacen propio.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/inventory/router.py`

### Tests de esta HU

- `tests/test_hu_tda_02_warehouses.py`
- Cubre creacion, stock en almacen activo, default unico, seleccion manual derivada, rechazo de almacen inactivo e historial.
- Ejecutar: `pytest tests/test_hu_tda_02_warehouses.py -v`

### Notas para frontend

- `requires_manual_dispatch_selection=false` significa que no debe pedir seleccion manual de almacen.
- Desactivar no elimina historicos; mostrar almacenes inactivos con estado claro.

---

## HU-TDA-03 · Configuracion de metodos de pago aceptados por la tienda

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_tda_03_payment_methods.py`

### Descripcion funcional

El vendedor define si acepta pasarela automatizada, transferencia bancaria y/o Bre-B. El catalogo publico y checkout muestran o permiten solo metodos habilitados por la tienda y disponibles por configuracion global/cuentas activas.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Habilitar pasarela automatizada la muestra al comprador. | Si | `payment-options` incluye `card`, `pse`, `nequi` si `gateway_enabled=true` y existe `payment_gateway`. |
| 2 | Habilitar cobro manual muestra transferencia y/o Bre-B segun cuentas activas. | Si | `payment-options` filtra cuentas activas por tipo `bank` o `bre_b` y solo agrega el metodo correspondiente. |
| 3 | Deshabilitar un metodo lo oculta en checkout. | Si | `payment-options` lo omite y `POST /checkout` lo rechaza con `400`. |

### Flujo implementado

```text
1. Seller llama GET/PUT /api/v1/seller/store/settings.
2. Backend normaliza payment_methods tipado y soporta lista legacy.
3. Comprador consulta GET /api/v1/catalog/stores/{store_id}/payment-options.
4. Backend combina settings, payment_gateway global y cuentas activas.
5. Checkout valida el metodo por tienda antes de crear pedido o pago.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/seller/store/settings` -> 200

**Descripcion:** consulta configuracion de pagos/envios de la tienda.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/catalog/router.py`

#### PUT `/api/v1/seller/store/settings` -> 200

**Descripcion:** actualiza metodos de pago aceptados por la tienda.
**Roles permitidos:** `seller`
**Archivo:** `app/modules/catalog/router.py`

**Request body:**
```json
{
  "payment_methods": {
    "gateway_enabled": true,
    "manual_transfer_enabled": true,
    "manual_breb_enabled": false
  },
  "shipping_flat_cost": 12900,
  "shipping_free_threshold": 120000,
  "shipping_zones": []
}
```

#### GET `/api/v1/catalog/stores/{store_id}/payment-options` -> 200

**Descripcion:** devuelve metodos y cuentas disponibles para checkout.
**Roles permitidos:** publico
**Archivo:** `app/modules/catalog/router.py`

#### POST `/api/v1/checkout` -> 201

**Descripcion:** valida que el metodo elegido este disponible para cada tienda del carrito.
**Roles permitidos:** `buyer`
**Archivo:** `app/modules/orders/router.py`

### Tests de esta HU

- `tests/test_hu_tda_03_payment_methods.py`
- Cubre pasarela, transferencia, Bre-B, ocultamiento de metodo deshabilitado y rechazo en checkout.
- Ejecutar: `pytest tests/test_hu_tda_03_payment_methods.py -v`

### Notas para frontend

- `payment_methods` de settings es un objeto booleano, no una lista nueva.
- `payment-options.payment_methods` conserva los valores de checkout: `card`, `pse`, `nequi`, `transfer`, `breb`.
- Para manuales, el comprador debe seleccionar una cuenta activa retornada en `payout_accounts`.

---

## Validaciones ejecutadas

- `pytest tests -v -k "hu_tda or tda_openapi"` -> 10 passed.
- `pytest tests -q` -> 40 passed, 3 skipped.
- Sync backend-only de `docs/openapi.json` y `docs/API_REFERENCE.md`.
