# singular-api

**Versión:** 0.1.0

Marketplace Singular — API Python

---

## Índice de endpoints

- [GET `/api/v1/health`](#get-apiv1health) — Health
- [GET `/api/v1/health/ready`](#get-apiv1healthready) — Ready
- [POST `/api/v1/auth/register`](#post-apiv1authregister) — Registrar comprador
- [POST `/api/v1/auth/login`](#post-apiv1authlogin) — Iniciar sesion
- [GET `/api/v1/auth/me`](#get-apiv1authme) — Consultar perfil
- [PATCH `/api/v1/auth/me`](#patch-apiv1authme) — Actualizar perfil
- [POST `/api/v1/auth/change-password`](#post-apiv1authchange-password) — Cambiar contrasena
- [POST `/api/v1/auth/password-recovery/request`](#post-apiv1authpassword-recoveryrequest) — Solicitar recuperacion
- [POST `/api/v1/auth/password-recovery/confirm`](#post-apiv1authpassword-recoveryconfirm) — Confirmar recuperacion
- [GET `/api/v1/admin/users`](#get-apiv1adminusers) — Listar usuarios
- [POST `/api/v1/admin/users`](#post-apiv1adminusers) — Crear usuario
- [GET `/api/v1/admin/users/{user_id}`](#get-apiv1adminusersuser-id) — Consultar usuario
- [PATCH `/api/v1/admin/users/{user_id}`](#patch-apiv1adminusersuser-id) — Actualizar usuario
- [POST `/api/v1/admin/users/{user_id}/temporary-password`](#post-apiv1adminusersuser-idtemporary-password) — Regenerar credencial temporal
- [GET `/api/v1/admin/stores`](#get-apiv1adminstores) — List Stores
- [POST `/api/v1/admin/stores`](#post-apiv1adminstores) — Create Store
- [GET `/api/v1/admin/stores/{store_id}`](#get-apiv1adminstoresstore-id) — Get Store
- [PATCH `/api/v1/admin/stores/{store_id}`](#patch-apiv1adminstoresstore-id) — Patch Store
- [GET `/api/v1/admin/stores/{store_id}/members`](#get-apiv1adminstoresstore-idmembers) — Listar miembros de tienda
- [POST `/api/v1/admin/stores/{store_id}/members`](#post-apiv1adminstoresstore-idmembers) — Crear miembro de tienda
- [PATCH `/api/v1/admin/stores/{store_id}/members/{user_id}`](#patch-apiv1adminstoresstore-idmembersuser-id) — Actualizar miembro de tienda
- [GET `/api/v1/admin/settings`](#get-apiv1adminsettings) — Get Settings
- [PUT `/api/v1/admin/settings/commission`](#put-apiv1adminsettingscommission) — Put Commission
- [PUT `/api/v1/admin/settings/payment-gateway`](#put-apiv1adminsettingspayment-gateway) — Put Gateway
- [GET `/api/v1/admin/reports/sales`](#get-apiv1adminreportssales) — Report Sales
- [GET `/api/v1/admin/reports/inventory`](#get-apiv1adminreportsinventory) — Report Inventory
- [GET `/api/v1/admin/moderation/reviews`](#get-apiv1adminmoderationreviews) — Moderation Reviews
- [PATCH `/api/v1/admin/moderation/reviews/{review_id}`](#patch-apiv1adminmoderationreviewsreview-id) — Patch Review
- [PATCH `/api/v1/admin/moderation/reports/{report_id}`](#patch-apiv1adminmoderationreportsreport-id) — Patch Report
- [GET `/api/v1/admin/moderation/disputes`](#get-apiv1adminmoderationdisputes) — Moderation Disputes
- [PATCH `/api/v1/admin/moderation/disputes/{dispute_id}`](#patch-apiv1adminmoderationdisputesdispute-id) — Patch Dispute
- [GET `/api/v1/catalog/stores`](#get-apiv1catalogstores) — Listar tiendas
- [GET `/api/v1/catalog/stores/{store_id}/payment-options`](#get-apiv1catalogstoresstore-idpayment-options) — Consultar opciones de pago
- [GET `/api/v1/catalog/categories`](#get-apiv1catalogcategories) — Listar categorias publicas
- [GET `/api/v1/catalog/products`](#get-apiv1catalogproducts) — Listar productos publicos
- [GET `/api/v1/catalog/products/{slug}`](#get-apiv1catalogproductsslug) — Consultar producto publico
- [GET `/api/v1/seller/store`](#get-apiv1sellerstore) — Consultar mi tienda
- [PATCH `/api/v1/seller/store`](#patch-apiv1sellerstore) — Actualizar mi tienda
- [GET `/api/v1/seller/store/settings`](#get-apiv1sellerstoresettings) — Consultar configuracion de tienda
- [PUT `/api/v1/seller/store/settings`](#put-apiv1sellerstoresettings) — Actualizar configuracion de tienda
- [GET `/api/v1/seller/categories`](#get-apiv1sellercategories) — Listar mis categorias
- [POST `/api/v1/seller/categories`](#post-apiv1sellercategories) — Crear categoria de mi tienda
- [PATCH `/api/v1/seller/categories/{category_id}`](#patch-apiv1sellercategoriescategory-id) — Actualizar categoria de mi tienda
- [DELETE `/api/v1/seller/categories/{category_id}`](#delete-apiv1sellercategoriescategory-id) — Desactivar categoria de mi tienda
- [GET `/api/v1/seller/products`](#get-apiv1sellerproducts) — Listar mis productos
- [POST `/api/v1/seller/products`](#post-apiv1sellerproducts) — Crear producto de mi tienda
- [PATCH `/api/v1/seller/products/{product_id}`](#patch-apiv1sellerproductsproduct-id) — Actualizar producto de mi tienda
- [DELETE `/api/v1/seller/products/{product_id}`](#delete-apiv1sellerproductsproduct-id) — Descontinuar producto
- [POST `/api/v1/seller/products/{product_id}/variants`](#post-apiv1sellerproductsproduct-idvariants) — Crear variante de producto
- [PATCH `/api/v1/seller/variants/{variant_id}`](#patch-apiv1sellervariantsvariant-id) — Actualizar variante de producto
- [DELETE `/api/v1/seller/variants/{variant_id}`](#delete-apiv1sellervariantsvariant-id) — Desactivar variante de producto
- [POST `/api/v1/seller/products/{product_id}/images`](#post-apiv1sellerproductsproduct-idimages) — Crear imagen de producto
- [PATCH `/api/v1/seller/products/{product_id}/images/{image_id}`](#patch-apiv1sellerproductsproduct-idimagesimage-id) — Actualizar imagen de producto
- [DELETE `/api/v1/seller/products/{product_id}/images/{image_id}`](#delete-apiv1sellerproductsproduct-idimagesimage-id) — Eliminar imagen de producto
- [GET `/api/v1/seller/products/import/template`](#get-apiv1sellerproductsimporttemplate) — Descargar plantilla de productos
- [POST `/api/v1/seller/products/import`](#post-apiv1sellerproductsimport) — Importar productos
- [GET `/api/v1/catalog/variants/{variant_id}/stock`](#get-apiv1catalogvariantsvariant-idstock) — Public Variant Stock
- [GET `/api/v1/seller/warehouses`](#get-apiv1sellerwarehouses) — Listar almacenes
- [POST `/api/v1/seller/warehouses`](#post-apiv1sellerwarehouses) — Crear almacen
- [PATCH `/api/v1/seller/warehouses/{warehouse_id}`](#patch-apiv1sellerwarehouseswarehouse-id) — Actualizar almacen
- [GET `/api/v1/seller/inventory`](#get-apiv1sellerinventory) — List Inventory
- [PATCH `/api/v1/seller/inventory/{variant_id}`](#patch-apiv1sellerinventoryvariant-id) — Adjust Inventory
- [GET `/api/v1/seller/inventory/movements`](#get-apiv1sellerinventorymovements) — Inventory Movements
- [GET `/api/v1/addresses`](#get-apiv1addresses) — Listar direcciones
- [POST `/api/v1/addresses`](#post-apiv1addresses) — Crear direccion
- [PATCH `/api/v1/addresses/{address_id}`](#patch-apiv1addressesaddress-id) — Actualizar direccion
- [DELETE `/api/v1/addresses/{address_id}`](#delete-apiv1addressesaddress-id) — Eliminar direccion
- [GET `/api/v1/favorites`](#get-apiv1favorites) — List Favorites
- [POST `/api/v1/favorites/{product_id}`](#post-apiv1favoritesproduct-id) — Add Favorite
- [DELETE `/api/v1/favorites/{product_id}`](#delete-apiv1favoritesproduct-id) — Remove Favorite
- [GET `/api/v1/cart`](#get-apiv1cart) — Get Cart
- [DELETE `/api/v1/cart`](#delete-apiv1cart) — Clear Cart
- [POST `/api/v1/cart/items`](#post-apiv1cartitems) — Add Cart Item
- [PATCH `/api/v1/cart/items/{item_id}`](#patch-apiv1cartitemsitem-id) — Patch Cart Item
- [DELETE `/api/v1/cart/items/{item_id}`](#delete-apiv1cartitemsitem-id) — Delete Cart Item
- [POST `/api/v1/checkout/quote`](#post-apiv1checkoutquote) — Cotizar checkout
- [POST `/api/v1/checkout`](#post-apiv1checkout) — Crear checkout
- [GET `/api/v1/orders`](#get-apiv1orders) — Buyer Orders
- [GET `/api/v1/orders/{order_id}`](#get-apiv1ordersorder-id) — Buyer Order
- [POST `/api/v1/orders/{order_id}/cancel`](#post-apiv1ordersorder-idcancel) — Cancel Order
- [GET `/api/v1/orders/{order_id}/payment`](#get-apiv1ordersorder-idpayment) — Buyer Order Payment
- [POST `/api/v1/orders/{order_id}/payment/receipt`](#post-apiv1ordersorder-idpaymentreceipt) — Upload Payment Receipt
- [GET `/api/v1/seller/dashboard`](#get-apiv1sellerdashboard) — Seller Dashboard
- [GET `/api/v1/seller/reports/sales`](#get-apiv1sellerreportssales) — Seller Sales Report
- [GET `/api/v1/seller/store/members`](#get-apiv1sellerstoremembers) — Listar usuarios de mi tienda
- [GET `/api/v1/seller/orders`](#get-apiv1sellerorders) — Seller Orders
- [PATCH `/api/v1/seller/orders/{order_id}/status`](#patch-apiv1sellerordersorder-idstatus) — Patch Order Status
- [PATCH `/api/v1/seller/orders/{order_id}/warehouse`](#patch-apiv1sellerordersorder-idwarehouse) — Assign Order Warehouse
- [POST `/api/v1/seller/pos/orders`](#post-apiv1sellerposorders) — Create Pos Order
- [GET `/api/v1/seller/promotions`](#get-apiv1sellerpromotions) — Listar promociones
- [POST `/api/v1/seller/promotions`](#post-apiv1sellerpromotions) — Crear promocion
- [PATCH `/api/v1/seller/promotions/{promotion_id}`](#patch-apiv1sellerpromotionspromotion-id) — Actualizar promocion
- [DELETE `/api/v1/seller/promotions/{promotion_id}`](#delete-apiv1sellerpromotionspromotion-id) — Desactivar promocion
- [GET `/api/v1/seller/coupons`](#get-apiv1sellercoupons) — Listar cupones
- [POST `/api/v1/seller/coupons`](#post-apiv1sellercoupons) — Crear cupon
- [PATCH `/api/v1/seller/coupons/{coupon_id}`](#patch-apiv1sellercouponscoupon-id) — Actualizar cupon
- [DELETE `/api/v1/seller/coupons/{coupon_id}`](#delete-apiv1sellercouponscoupon-id) — Desactivar cupon
- [GET `/api/v1/seller/extra-charges`](#get-apiv1sellerextra-charges) — Listar cargos extra
- [POST `/api/v1/seller/extra-charges`](#post-apiv1sellerextra-charges) — Crear cargo extra
- [PATCH `/api/v1/seller/extra-charges/{charge_id}`](#patch-apiv1sellerextra-chargescharge-id) — Actualizar cargo extra
- [DELETE `/api/v1/seller/extra-charges/{charge_id}`](#delete-apiv1sellerextra-chargescharge-id) — Desactivar cargo extra
- [GET `/api/v1/seller/customers`](#get-apiv1sellercustomers) — Seller Customers
- [GET `/api/v1/seller/payout-accounts`](#get-apiv1sellerpayout-accounts) — List Payout Accounts
- [POST `/api/v1/seller/payout-accounts`](#post-apiv1sellerpayout-accounts) — Create Payout Account
- [PATCH `/api/v1/seller/payout-accounts/{account_id}`](#patch-apiv1sellerpayout-accountsaccount-id) — Patch Payout Account
- [DELETE `/api/v1/seller/payout-accounts/{account_id}`](#delete-apiv1sellerpayout-accountsaccount-id) — Deactivate Payout Account
- [GET `/api/v1/seller/payments`](#get-apiv1sellerpayments) — Seller Payments
- [POST `/api/v1/seller/payments/{payment_id}/confirm`](#post-apiv1sellerpaymentspayment-idconfirm) — Confirm Manual Payment
- [POST `/api/v1/seller/payments/{payment_id}/reject`](#post-apiv1sellerpaymentspayment-idreject) — Reject Manual Payment
- [POST `/api/v1/payments/orders/{order_id}/intent`](#post-apiv1paymentsordersorder-idintent) — Create Payment Intent
- [POST `/api/v1/payments/webhooks/{provider}`](#post-apiv1paymentswebhooksprovider) — Payment Webhook
- [GET `/api/v1/catalog/products/{product_id}/reviews`](#get-apiv1catalogproductsproduct-idreviews) — Product Reviews
- [POST `/api/v1/catalog/products/{product_id}/reviews`](#post-apiv1catalogproductsproduct-idreviews) — Create Review
- [POST `/api/v1/reviews/{review_id}/report`](#post-apiv1reviewsreview-idreport) — Report Review
- [GET `/api/v1/orders/{order_id}/dispute`](#get-apiv1ordersorder-iddispute) — Order Dispute
- [POST `/api/v1/orders/{order_id}/dispute`](#post-apiv1ordersorder-iddispute) — Create Dispute

---

## `GET` `/api/v1/health`

**Health**

**Tags:** health

### Respuesta `200`

Successful Response

---

## `GET` `/api/v1/health/ready`

**Ready**

**Tags:** health

### Respuesta `200`

Successful Response

---

## `POST` `/api/v1/auth/register`

**Registrar comprador**

Rol permitido: publico. HU-USR-01. Registra exclusivamente compradores; vendedores y administradores solo se crean desde administracion.

**Tags:** auth

### Request body

### Respuesta `201`

Sesion o estado de confirmacion del comprador creado.

### Errores posibles

| Código | Situación                                                                     | Mensaje típico |
| ------ | ----------------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.                                   |                |
| 401    | Credenciales invalidas.                                                       |                |
| 403    | Usuario inactivo, credencial temporal vencida o cambio obligatorio pendiente. |                |
| 409    | El correo ya existe.                                                          |                |
| 422    | Validacion Pydantic.                                                          |                |
| 502    | Supabase Auth no disponible o no configurado.                                 |                |

---

## `POST` `/api/v1/auth/login`

**Iniciar sesion**

Rol permitido: publico. HU-USR-01 y HU-USR-02. Autentica con Supabase Auth, rechaza credenciales invalidas sin revelar cual dato fallo y senala cambio obligatorio.

**Tags:** auth

### Request body

### Respuesta `200`

Sesion autenticada con perfil local y bandera de cambio obligatorio.

### Errores posibles

| Código | Situación                                                                     | Mensaje típico |
| ------ | ----------------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.                                   |                |
| 401    | Credenciales invalidas.                                                       |                |
| 403    | Usuario inactivo, credencial temporal vencida o cambio obligatorio pendiente. |                |
| 409    | El correo ya existe.                                                          |                |
| 422    | Validacion Pydantic.                                                          |                |
| 502    | Supabase Auth no disponible o no configurado.                                 |                |

---

## `GET` `/api/v1/auth/me`

**Consultar perfil**

Rol permitido: buyer, seller, admin. HU-USR-03. Retorna el perfil del usuario autenticado.

**Tags:** auth

### Respuesta `200`

Perfil del usuario autenticado.

### Errores posibles

| Código | Situación                   | Mensaje típico |
| ------ | --------------------------- | -------------- |
| 401    | Token requerido o invalido. |                |
| 403    | Usuario desactivado.        |                |

---

## `PATCH` `/api/v1/auth/me`

**Actualizar perfil**

Rol permitido: buyer, seller, admin. HU-USR-03. Actualiza nombre y telefono del usuario autenticado.

**Tags:** auth

### Request body

### Respuesta `200`

Perfil actualizado.

### Errores posibles

| Código | Situación                   | Mensaje típico |
| ------ | --------------------------- | -------------- |
| 401    | Token requerido o invalido. |                |
| 403    | Usuario desactivado.        |                |
| 422    | Validacion Pydantic.        |                |

---

## `POST` `/api/v1/auth/change-password`

**Cambiar contrasena**

Rol permitido: buyer, seller, admin. HU-USR-02 y HU-USR-04. Cambia la contrasena del usuario autenticado y libera el bloqueo de primer ingreso cuando aplica.

**Tags:** auth

### Request body

### Respuesta `200`

Perfil actualizado sin cambio obligatorio pendiente.

### Errores posibles

| Código | Situación                                        | Mensaje típico |
| ------ | ------------------------------------------------ | -------------- |
| 400    | Datos invalidos o regla de negocio violada.      |                |
| 401    | Token requerido o invalido.                      |                |
| 403    | Usuario inactivo o cambio obligatorio pendiente. |                |
| 422    | Validacion Pydantic.                             |                |
| 502    | Supabase Auth no disponible o no configurado.    |                |

---

## `POST` `/api/v1/auth/password-recovery/request`

**Solicitar recuperacion**

Rol permitido: publico. HU-USR-04. Solicita enlace o codigo de recuperacion por correo sin devolver tokens ni secretos.

**Tags:** auth

### Request body

### Respuesta `202`

Confirmacion de recepcion de la solicitud.

### Errores posibles

| Código | Situación                                                                     | Mensaje típico |
| ------ | ----------------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.                                   |                |
| 401    | Credenciales invalidas.                                                       |                |
| 403    | Usuario inactivo, credencial temporal vencida o cambio obligatorio pendiente. |                |
| 409    | El correo ya existe.                                                          |                |
| 422    | Validacion Pydantic.                                                          |                |
| 502    | Supabase Auth no disponible o no configurado.                                 |                |

---

## `POST` `/api/v1/auth/password-recovery/confirm`

**Confirmar recuperacion**

Rol permitido: publico. HU-USR-04. Usa un token o codigo vigente de recuperacion para definir una nueva contrasena.

**Tags:** auth

### Request body

### Respuesta `200`

Confirmacion del cambio de contrasena.

### Errores posibles

| Código | Situación                                                                     | Mensaje típico |
| ------ | ----------------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.                                   |                |
| 401    | Credenciales invalidas.                                                       |                |
| 403    | Usuario inactivo, credencial temporal vencida o cambio obligatorio pendiente. |                |
| 409    | El correo ya existe.                                                          |                |
| 422    | Validacion Pydantic.                                                          |                |
| 502    | Supabase Auth no disponible o no configurado.                                 |                |

---

## `GET` `/api/v1/admin/users`

**Listar usuarios**

Rol permitido: admin. HU-USR-05. Lista usuarios de plataforma con filtros de rol y estado.

**Tags:** admin

### Parámetros de query

| Nombre    | Tipo    | Requerido | Descripción |
| --------- | ------- | --------- | ----------- |
| q         | string  |           |             |
| role      | string  |           |             |
| active    | string  |           |             |
| page      | integer |           |             |
| page_size | integer |           |             |

### Respuesta `200`

Lista paginada de usuarios.

### Errores posibles

| Código | Situación                                     | Mensaje típico |
| ------ | --------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.   |                |
| 401    | Token requerido o invalido.                   |                |
| 403    | Requiere rol admin.                           |                |
| 404    | Recurso no encontrado.                        |                |
| 409    | Conflicto con recurso existente.              |                |
| 422    | Validacion Pydantic.                          |                |
| 502    | Supabase Auth no disponible o no configurado. |                |

---

## `POST` `/api/v1/admin/users`

**Crear usuario**

Rol permitido: admin. HU-USR-02 y HU-USR-05. Crea usuarios no autorregistrables con credencial temporal cuando el rol es seller o admin.

**Tags:** admin

### Request body

### Respuesta `201`

Usuario creado; si aplica, incluye credencial temporal visible una sola vez.

### Errores posibles

| Código | Situación                                     | Mensaje típico |
| ------ | --------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.   |                |
| 401    | Token requerido o invalido.                   |                |
| 403    | Requiere rol admin.                           |                |
| 404    | Recurso no encontrado.                        |                |
| 409    | Conflicto con recurso existente.              |                |
| 422    | Validacion Pydantic.                          |                |
| 502    | Supabase Auth no disponible o no configurado. |                |

---

## `GET` `/api/v1/admin/users/{user_id}`

**Consultar usuario**

Rol permitido: admin. HU-USR-05. Consulta un usuario de plataforma por identificador.

**Tags:** admin

### Parámetros de ruta

| Nombre  | Tipo   | Requerido | Descripción |
| ------- | ------ | --------- | ----------- |
| user_id | string | ✓         |             |

### Respuesta `200`

Usuario encontrado.

### Errores posibles

| Código | Situación                                     | Mensaje típico |
| ------ | --------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.   |                |
| 401    | Token requerido o invalido.                   |                |
| 403    | Requiere rol admin.                           |                |
| 404    | Recurso no encontrado.                        |                |
| 409    | Conflicto con recurso existente.              |                |
| 422    | Validacion Pydantic.                          |                |
| 502    | Supabase Auth no disponible o no configurado. |                |

---

## `PATCH` `/api/v1/admin/users/{user_id}`

**Actualizar usuario**

Rol permitido: admin. HU-USR-05. Actualiza rol o estado activo de un usuario sin borrar historico.

**Tags:** admin

### Parámetros de ruta

| Nombre  | Tipo   | Requerido | Descripción |
| ------- | ------ | --------- | ----------- |
| user_id | string | ✓         |             |

### Request body

### Respuesta `200`

Usuario actualizado.

### Errores posibles

| Código | Situación                                     | Mensaje típico |
| ------ | --------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.   |                |
| 401    | Token requerido o invalido.                   |                |
| 403    | Requiere rol admin.                           |                |
| 404    | Recurso no encontrado.                        |                |
| 409    | Conflicto con recurso existente.              |                |
| 422    | Validacion Pydantic.                          |                |
| 502    | Supabase Auth no disponible o no configurado. |                |

---

## `POST` `/api/v1/admin/users/{user_id}/temporary-password`

**Regenerar credencial temporal**

Rol permitido: admin. HU-USR-02. Invalida la contrasena anterior en Supabase, genera una nueva credencial temporal y fuerza cambio en el siguiente ingreso.

**Tags:** admin

### Parámetros de ruta

| Nombre  | Tipo   | Requerido | Descripción |
| ------- | ------ | --------- | ----------- |
| user_id | string | ✓         |             |

### Parámetros de query

| Nombre | Tipo    | Requerido | Descripción                                        |
| ------ | ------- | --------- | -------------------------------------------------- |
| hours  | integer |           | Horas de vigencia de la nueva credencial temporal. |

### Respuesta `200`

Usuario actualizado con nueva credencial temporal visible una sola vez.

### Errores posibles

| Código | Situación                                     | Mensaje típico |
| ------ | --------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.   |                |
| 401    | Token requerido o invalido.                   |                |
| 403    | Requiere rol admin.                           |                |
| 404    | Recurso no encontrado.                        |                |
| 409    | Conflicto con recurso existente.              |                |
| 422    | Validacion Pydantic.                          |                |
| 502    | Supabase Auth no disponible o no configurado. |                |

---

## `GET` `/api/v1/admin/stores`

**List Stores**

**Tags:** admin

### Parámetros de query

| Nombre    | Tipo    | Requerido | Descripción |
| --------- | ------- | --------- | ----------- |
| q         | string  |           |             |
| active    | string  |           |             |
| page      | integer |           |             |
| page_size | integer |           |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/admin/stores`

**Create Store**

**Tags:** admin

### Request body

### Respuesta `201`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/admin/stores/{store_id}`

**Get Store**

**Tags:** admin

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/admin/stores/{store_id}`

**Patch Store**

**Tags:** admin

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/admin/stores/{store_id}/members`

**Listar miembros de tienda**

Rol permitido: admin. HU-USR-05. Lista usuarios activos e inactivos asociados a una tienda.

**Tags:** admin

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string | ✓         |             |

### Respuesta `200`

Miembros de la tienda.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación                                     | Mensaje típico |
| ------ | --------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.   |                |
| 401    | Token requerido o invalido.                   |                |
| 403    | Requiere rol admin.                           |                |
| 404    | Recurso no encontrado.                        |                |
| 409    | Conflicto con recurso existente.              |                |
| 422    | Validacion Pydantic.                          |                |
| 502    | Supabase Auth no disponible o no configurado. |                |

---

## `POST` `/api/v1/admin/stores/{store_id}/members`

**Crear miembro de tienda**

Rol permitido: admin. HU-USR-05. Crea un usuario adicional asociado a una tienda, con credencial temporal y acceso al mismo panel de la tienda.

**Tags:** admin

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string | ✓         |             |

### Request body

### Respuesta `201`

Miembro creado con credencial temporal visible una sola vez.

### Errores posibles

| Código | Situación                                     | Mensaje típico |
| ------ | --------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.   |                |
| 401    | Token requerido o invalido.                   |                |
| 403    | Requiere rol admin.                           |                |
| 404    | Recurso no encontrado.                        |                |
| 409    | Conflicto con recurso existente.              |                |
| 422    | Validacion Pydantic.                          |                |
| 502    | Supabase Auth no disponible o no configurado. |                |

---

## `PATCH` `/api/v1/admin/stores/{store_id}/members/{user_id}`

**Actualizar miembro de tienda**

Rol permitido: admin. HU-USR-05. Cambia estado o rol interno del usuario de equipo sin borrar historico.

**Tags:** admin

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string | ✓         |             |
| user_id  | string | ✓         |             |

### Request body

### Respuesta `200`

Miembro actualizado.

### Errores posibles

| Código | Situación                                     | Mensaje típico |
| ------ | --------------------------------------------- | -------------- |
| 400    | Datos invalidos o regla de negocio violada.   |                |
| 401    | Token requerido o invalido.                   |                |
| 403    | Requiere rol admin.                           |                |
| 404    | Recurso no encontrado.                        |                |
| 409    | Conflicto con recurso existente.              |                |
| 422    | Validacion Pydantic.                          |                |
| 502    | Supabase Auth no disponible o no configurado. |                |

---

## `GET` `/api/v1/admin/settings`

**Get Settings**

**Tags:** admin

### Respuesta `200`

Successful Response

```json
[
  {}
]
```

---

## `PUT` `/api/v1/admin/settings/commission`

**Put Commission**

**Tags:** admin

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PUT` `/api/v1/admin/settings/payment-gateway`

**Put Gateway**

**Tags:** admin

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/admin/reports/sales`

**Report Sales**

**Tags:** admin

### Parámetros de query

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| date_from | string |           |             |
| date_to   | string |           |             |
| store_id  | string |           |             |
| channel   | string |           |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/admin/reports/inventory`

**Report Inventory**

**Tags:** admin

### Parámetros de query

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string |           |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/admin/moderation/reviews`

**Moderation Reviews**

**Tags:** admin

### Parámetros de query

| Nombre | Tipo   | Requerido | Descripción |
| ------ | ------ | --------- | ----------- |
| status | string |           |             |

### Respuesta `200`

Successful Response

```json
[
  {}
]
```

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/admin/moderation/reviews/{review_id}`

**Patch Review**

**Tags:** admin

### Parámetros de ruta

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| review_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/admin/moderation/reports/{report_id}`

**Patch Report**

**Tags:** admin

### Parámetros de ruta

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| report_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/admin/moderation/disputes`

**Moderation Disputes**

**Tags:** admin

### Parámetros de query

| Nombre | Tipo   | Requerido | Descripción |
| ------ | ------ | --------- | ----------- |
| status | string |           |             |

### Respuesta `200`

Successful Response

```json
[
  {}
]
```

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/admin/moderation/disputes/{dispute_id}`

**Patch Dispute**

**Tags:** admin

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| dispute_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/catalog/stores`

**Listar tiendas**

Endpoint publico. HU-TDA-01. Lista tiendas activas con informacion publica de contacto visible para compradores.

**Tags:** catalog

### Respuesta `200`

Tiendas activas con datos publicos actualizados.

### Errores posibles

| Código | Situación            | Mensaje típico |
| ------ | -------------------- | -------------- |
| 422    | Validacion Pydantic. |                |

---

## `GET` `/api/v1/catalog/stores/{store_id}/payment-options`

**Consultar opciones de pago**

Endpoint publico. HU-TDA-03. Muestra solo metodos de pago habilitados por la tienda y disponibles por cuentas activas/configuracion de pasarela.

**Tags:** catalog

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string | ✓         |             |

### Respuesta `200`

Metodos y cuentas de cobro disponibles para checkout.

### Errores posibles

| Código | Situación                        | Mensaje típico |
| ------ | -------------------------------- | -------------- |
| 404    | Tienda no encontrada o inactiva. |                |
| 422    | Validacion Pydantic.             |                |

---

## `GET` `/api/v1/catalog/categories`

**Listar categorias publicas**

Endpoint publico. HU-CAT-01. Lista categorias y subcategorias activas. Para navegar el catalogo de una tienda se debe enviar `store_id`; asi el comprador ve solo la jerarquia definida por esa tienda y no categorias de otras tiendas.

**Tags:** catalog

### Parámetros de query

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string |           |             |

### Respuesta `200`

Categorias activas con parent_id para reconstruir la jerarquia.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación            | Mensaje típico |
| ------ | -------------------- | -------------- |
| 422    | Validacion Pydantic. |                |

---

## `GET` `/api/v1/catalog/products`

**Listar productos publicos**

Endpoint publico. HU-CAT-02, HU-PROD-01, HU-PROD-06 y HU-PROM-01. Lista productos visibles para compradores: `active` y `out_of_stock`; oculta `draft` y `discontinued`. Permite filtrar por `store_id` y `category` para navegar productos asignados a multiples categorias.

**Tags:** catalog

### Parámetros de query

| Nombre    | Tipo    | Requerido | Descripción |
| --------- | ------- | --------- | ----------- |
| q         | string  |           |             |
| category  | string  |           |             |
| store_id  | string  |           |             |
| min_price | string  |           |             |
| max_price | string  |           |             |
| in_stock  | boolean |           |             |
| sort      | string  |           |             |
| page      | integer |           |             |
| page_size | integer |           |             |

### Respuesta `200`

Pagina de productos visibles filtrados por busqueda, tienda, categoria y precio.

### Errores posibles

| Código | Situación                                         | Mensaje típico |
| ------ | ------------------------------------------------- | -------------- |
| 404    | Producto no encontrado o no visible publicamente. |                |
| 422    | Validacion Pydantic.                              |                |

---

## `GET` `/api/v1/catalog/products/{slug}`

**Consultar producto publico**

Endpoint publico. HU-PROD-02, HU-PROD-04, HU-PROD-05, HU-PROD-06, HU-PROM-01 y HU-PROM-03. Retorna detalle publico del producto visible, variantes con precio efectivo/stock/disponibilidad e imagenes, sin exponer costos internos.

**Tags:** catalog

### Parámetros de ruta

| Nombre | Tipo   | Requerido | Descripción |
| ------ | ------ | --------- | ----------- |
| slug   | string | ✓         |             |

### Parámetros de query

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| store_id | string |           |             |

### Respuesta `200`

Detalle publico del producto sin costo interno.

### Errores posibles

| Código | Situación                                         | Mensaje típico |
| ------ | ------------------------------------------------- | -------------- |
| 404    | Producto no encontrado o no visible publicamente. |                |
| 422    | Validacion Pydantic.                              |                |

---

## `GET` `/api/v1/seller/store`

**Consultar mi tienda**

Rol permitido: seller. HU-TDA-01. Retorna la tienda asociada y separa datos publicos editables de campos administrados.

**Tags:** seller-catalog

### Respuesta `200`

Perfil de tienda del vendedor autenticado.

### Errores posibles

| Código | Situación                                             | Mensaje típico |
| ------ | ----------------------------------------------------- | -------------- |
| 400    | Campo administrado o regla de negocio no permitida.   |                |
| 401    | Token requerido o invalido.                           |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente. |                |
| 404    | El vendedor no tiene una tienda activa.               |                |
| 422    | Validacion Pydantic.                                  |                |

---

## `PATCH` `/api/v1/seller/store`

**Actualizar mi tienda**

Rol permitido: seller. HU-TDA-01. Actualiza solo informacion publica; nombre, slug, estado y datos legales son gestion de administracion.

**Tags:** seller-catalog

### Request body

### Respuesta `200`

Perfil publico de tienda actualizado.

### Errores posibles

| Código | Situación                                             | Mensaje típico |
| ------ | ----------------------------------------------------- | -------------- |
| 400    | Campo administrado o regla de negocio no permitida.   |                |
| 401    | Token requerido o invalido.                           |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente. |                |
| 404    | El vendedor no tiene una tienda activa.               |                |
| 422    | Validacion Pydantic.                                  |                |

---

## `GET` `/api/v1/seller/store/settings`

**Consultar configuracion de tienda**

Rol permitido: seller. HU-TDA-03. Retorna metodos de pago aceptados y configuracion operativa de la tienda.

**Tags:** seller-catalog

### Respuesta `200`

Configuracion vigente de la tienda.

### Errores posibles

| Código | Situación                                             | Mensaje típico |
| ------ | ----------------------------------------------------- | -------------- |
| 401    | Token requerido o invalido.                           |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente. |                |
| 404    | El vendedor no tiene una tienda activa.               |                |
| 422    | Validacion Pydantic.                                  |                |

---

## `PUT` `/api/v1/seller/store/settings`

**Actualizar configuracion de tienda**

Rol permitido: seller. HU-TDA-03. Define pasarela automatizada, transferencia bancaria y Bre-B aceptados por la tienda.

**Tags:** seller-catalog

### Request body

### Respuesta `200`

Configuracion actualizada de la tienda.

### Errores posibles

| Código | Situación                                             | Mensaje típico |
| ------ | ----------------------------------------------------- | -------------- |
| 401    | Token requerido o invalido.                           |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente. |                |
| 404    | El vendedor no tiene una tienda activa.               |                |
| 422    | Validacion Pydantic.                                  |                |

---

## `GET` `/api/v1/seller/categories`

**Listar mis categorias**

Rol permitido: seller. HU-CAT-01. Lista categorias y subcategorias propias de la tienda autenticada, incluidas inactivas, para administrar la jerarquia del catalogo.

**Tags:** seller-catalog

### Respuesta `200`

Categorias de la tienda autenticada con parent_id y estado.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación                                                                    | Mensaje típico |
| ------ | ---------------------------------------------------------------------------- | -------------- |
| 400    | Categoria padre invalida, jerarquia ciclica o regla de negocio no permitida. |                |
| 401    | Token requerido o invalido.                                                  |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                        |                |
| 404    | Categoria o tienda no encontrada.                                            |                |
| 409    | Ya existe una categoria con el mismo slug en la tienda.                      |                |
| 422    | Validacion Pydantic.                                                         |                |

---

## `POST` `/api/v1/seller/categories`

**Crear categoria de mi tienda**

Rol permitido: seller. HU-CAT-01. Crea una categoria raiz o subcategoria propia. `parent_id`, cuando se envia, debe pertenecer a la misma tienda; el slug es unico por tienda.

**Tags:** seller-catalog

### Request body

### Respuesta `201`

Categoria creada y disponible para asignar productos de la tienda.

### Errores posibles

| Código | Situación                                                                    | Mensaje típico |
| ------ | ---------------------------------------------------------------------------- | -------------- |
| 400    | Categoria padre invalida, jerarquia ciclica o regla de negocio no permitida. |                |
| 401    | Token requerido o invalido.                                                  |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                        |                |
| 404    | Categoria o tienda no encontrada.                                            |                |
| 409    | Ya existe una categoria con el mismo slug en la tienda.                      |                |
| 422    | Validacion Pydantic.                                                         |                |

---

## `PATCH` `/api/v1/seller/categories/{category_id}`

**Actualizar categoria de mi tienda**

Rol permitido: seller. HU-CAT-01. Actualiza nombre, slug, parent, orden o estado de una categoria propia. Rechaza parent de otra tienda, autociclos y ciclos de jerarquia.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre      | Tipo   | Requerido | Descripción |
| ----------- | ------ | --------- | ----------- |
| category_id | string | ✓         |             |

### Request body

### Respuesta `200`

Categoria actualizada manteniendo el scope de la tienda.

### Errores posibles

| Código | Situación                                                                    | Mensaje típico |
| ------ | ---------------------------------------------------------------------------- | -------------- |
| 400    | Categoria padre invalida, jerarquia ciclica o regla de negocio no permitida. |                |
| 401    | Token requerido o invalido.                                                  |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                        |                |
| 404    | Categoria o tienda no encontrada.                                            |                |
| 409    | Ya existe una categoria con el mismo slug en la tienda.                      |                |
| 422    | Validacion Pydantic.                                                         |                |

---

## `DELETE` `/api/v1/seller/categories/{category_id}`

**Desactivar categoria de mi tienda**

Rol permitido: seller. HU-CAT-01. Realiza baja logica de una categoria propia (`active=false`) para conservar historicos y ocultarla del catalogo publico.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre      | Tipo   | Requerido | Descripción |
| ----------- | ------ | --------- | ----------- |
| category_id | string | ✓         |             |

### Respuesta `204`

Categoria desactivada sin cuerpo de respuesta.

### Errores posibles

| Código | Situación                                                                    | Mensaje típico |
| ------ | ---------------------------------------------------------------------------- | -------------- |
| 400    | Categoria padre invalida, jerarquia ciclica o regla de negocio no permitida. |                |
| 401    | Token requerido o invalido.                                                  |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                        |                |
| 404    | Categoria o tienda no encontrada.                                            |                |
| 409    | Ya existe una categoria con el mismo slug en la tienda.                      |                |
| 422    | Validacion Pydantic.                                                         |                |

---

## `GET` `/api/v1/seller/products`

**Listar mis productos**

Rol permitido: seller. HU-PROD-01, HU-PROD-05, HU-PROD-06, HU-PROM-01 y HU-PROM-03. Lista productos de la tienda autenticada, incluidos borradores, agotados y descontinuados, con precio efectivo, costo interno y margen.

**Tags:** seller-catalog

### Parámetros de query

| Nombre    | Tipo    | Requerido | Descripción |
| --------- | ------- | --------- | ----------- |
| status    | string  |           |             |
| q         | string  |           |             |
| page      | integer |           |             |
| page_size | integer |           |             |

### Respuesta `200`

Productos de la tienda autenticada con datos operativos seller.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `POST` `/api/v1/seller/products`

**Crear producto de mi tienda**

Rol permitido: seller. HU-PROD-01, HU-PROD-02, HU-PROD-04, HU-PROD-05, HU-PROM-01, HU-PROM-03 y HU-CAT-02. Crea un producto propio con variantes, precio regular/especial, costo interno, imagenes y estado inicial; puede asociarlo a categorias activas de la misma tienda.

**Tags:** seller-catalog

### Request body

### Respuesta `201`

Producto creado con datos operativos seller.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `PATCH` `/api/v1/seller/products/{product_id}`

**Actualizar producto de mi tienda**

Rol permitido: seller. HU-PROD-01, HU-PROD-05, HU-PROD-06, HU-PROM-03 y HU-CAT-02. Actualiza datos del producto propio y, si `category_ids` viene en el payload, reemplaza sus categorias por categorias activas de la misma tienda.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |

### Request body

### Respuesta `200`

Producto actualizado con datos operativos seller.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `DELETE` `/api/v1/seller/products/{product_id}`

**Descontinuar producto**

Rol permitido: seller. HU-PROD-01 y HU-PROD-06. Cambia el producto propio a `discontinued` como baja logica y lo oculta del catalogo publico.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |

### Respuesta `200`

Producto descontinuado conservado para panel seller e historicos.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `POST` `/api/v1/seller/products/{product_id}/variants`

**Crear variante de producto**

Rol permitido: seller. HU-PROD-02, HU-PROD-05, HU-PROM-01 y HU-PROM-03. Crea una variante propia con SKU unico, atributos, precio regular, precio especial temporal y costo interno.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |

### Request body

### Respuesta `201`

Variante creada con stock, costo y margen seller.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `PATCH` `/api/v1/seller/variants/{variant_id}`

**Actualizar variante de producto**

Rol permitido: seller. HU-PROD-02, HU-PROD-05, HU-PROM-01 y HU-PROM-03. Actualiza una variante propia, incluido precio regular, precio especial temporal, costo interno y estado activo.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| variant_id | string | ✓         |             |

### Request body

### Respuesta `200`

Variante actualizada con stock, costo y margen seller.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `DELETE` `/api/v1/seller/variants/{variant_id}`

**Desactivar variante de producto**

Rol permitido: seller. HU-PROD-02. Realiza baja logica de una variante propia para que deje de estar disponible como opcion seleccionable.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| variant_id | string | ✓         |             |

### Respuesta `200`

Variante desactivada conservada para historial.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `POST` `/api/v1/seller/products/{product_id}/images`

**Crear imagen de producto**

Rol permitido: seller. HU-PROD-04. Agrega una imagen general del producto o una imagen especifica de una variante del mismo producto.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |

### Request body

### Respuesta `201`

Imagen creada y asociada al producto o variante.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `PATCH` `/api/v1/seller/products/{product_id}/images/{image_id}`

**Actualizar imagen de producto**

Rol permitido: seller. HU-PROD-04. Actualiza URL, texto alternativo, orden o variante asociada de una imagen propia.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |
| image_id   | string | ✓         |             |

### Request body

### Respuesta `200`

Imagen actualizada.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `DELETE` `/api/v1/seller/products/{product_id}/images/{image_id}`

**Eliminar imagen de producto**

Rol permitido: seller. HU-PROD-04. Elimina una imagen propia para que deje de mostrarse en la ficha publica.

**Tags:** seller-catalog

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |
| image_id   | string | ✓         |             |

### Respuesta `204`

Imagen eliminada sin cuerpo de respuesta.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `GET` `/api/v1/seller/products/import/template`

**Descargar plantilla de productos**

Rol permitido: seller. HU-PROD-03. Devuelve una plantilla CSV con columnas esperadas para carga masiva de productos.

**Tags:** seller-catalog

### Respuesta `200`

Archivo CSV de ejemplo para importacion.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `POST` `/api/v1/seller/products/import`

**Importar productos**

Rol permitido: seller. HU-PROD-03. Procesa un archivo CSV/XLSX, crea filas validas y reporta errores por fila sin abortar todo el lote.

**Tags:** seller-catalog

### Request body

### Respuesta `201`

Resumen de productos creados y errores por fila.

### Errores posibles

| Código | Situación                                                               | Mensaje típico |
| ------ | ----------------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, estado no permitido o recurso asociado fuera de scope. |                |
| 401    | Token requerido o invalido.                                             |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente.                   |                |
| 404    | Producto, variante, imagen o tienda no encontrada.                      |                |
| 409    | Slug de producto o SKU de variante duplicado.                           |                |
| 422    | Validacion Pydantic.                                                    |                |

---

## `GET` `/api/v1/catalog/variants/{variant_id}/stock`

**Public Variant Stock**

**Tags:** catalog-inventory

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| variant_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/seller/warehouses`

**Listar almacenes**

Rol permitido: seller. HU-TDA-02. Lista puntos o almacenes activos e inactivos de la tienda autenticada.

**Tags:** seller-inventory

### Respuesta `200`

Almacenes de la tienda con indicador de seleccion manual de despacho.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación                                             | Mensaje típico |
| ------ | ----------------------------------------------------- | -------------- |
| 400    | Almacen inactivo o regla de negocio no permitida.     |                |
| 401    | Token requerido o invalido.                           |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente. |                |
| 404    | Almacen o recurso no encontrado en la tienda.         |                |
| 422    | Validacion Pydantic.                                  |                |

---

## `POST` `/api/v1/seller/warehouses`

**Crear almacen**

Rol permitido: seller. HU-TDA-02. Registra un punto o almacen de la tienda para asociarle stock.

**Tags:** seller-inventory

### Request body

### Respuesta `201`

Almacen creado y disponible segun su estado activo.

### Errores posibles

| Código | Situación                                             | Mensaje típico |
| ------ | ----------------------------------------------------- | -------------- |
| 400    | Almacen inactivo o regla de negocio no permitida.     |                |
| 401    | Token requerido o invalido.                           |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente. |                |
| 404    | Almacen o recurso no encontrado en la tienda.         |                |
| 422    | Validacion Pydantic.                                  |                |

---

## `PATCH` `/api/v1/seller/warehouses/{warehouse_id}`

**Actualizar almacen**

Rol permitido: seller. HU-TDA-02. Actualiza o desactiva un almacen sin afectar pedidos ni movimientos historicos.

**Tags:** seller-inventory

### Parámetros de ruta

| Nombre       | Tipo   | Requerido | Descripción |
| ------------ | ------ | --------- | ----------- |
| warehouse_id | string | ✓         |             |

### Request body

### Respuesta `200`

Almacen actualizado.

### Errores posibles

| Código | Situación                                             | Mensaje típico |
| ------ | ----------------------------------------------------- | -------------- |
| 400    | Almacen inactivo o regla de negocio no permitida.     |                |
| 401    | Token requerido o invalido.                           |                |
| 403    | Requiere rol seller o cambio de contrasena pendiente. |                |
| 404    | Almacen o recurso no encontrado en la tienda.         |                |
| 422    | Validacion Pydantic.                                  |                |

---

## `GET` `/api/v1/seller/inventory`

**List Inventory**

**Tags:** seller-inventory

### Parámetros de query

| Nombre       | Tipo    | Requerido | Descripción |
| ------------ | ------- | --------- | ----------- |
| warehouse_id | string  |           |             |
| low_stock    | boolean |           |             |

### Respuesta `200`

Successful Response

```json
[
  {}
]
```

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/seller/inventory/{variant_id}`

**Adjust Inventory**

**Tags:** seller-inventory

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| variant_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

```json
[
  {}
]
```

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/seller/inventory/movements`

**Inventory Movements**

**Tags:** seller-inventory

### Parámetros de query

| Nombre     | Tipo    | Requerido | Descripción |
| ---------- | ------- | --------- | ----------- |
| variant_id | string  |           |             |
| limit      | integer |           |             |

### Respuesta `200`

Successful Response

```json
[
  {}
]
```

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/addresses`

**Listar direcciones**

Rol permitido: buyer. HU-USR-03. Lista solo las direcciones de envio del comprador autenticado.

**Tags:** buyer

### Respuesta `200`

Direcciones guardadas del comprador.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación                                                   | Mensaje típico |
| ------ | ----------------------------------------------------------- | -------------- |
| 401    | Token requerido o invalido.                                 |                |
| 403    | Requiere rol buyer o recurso fuera del scope del comprador. |                |
| 404    | Direccion no encontrada.                                    |                |
| 422    | Validacion Pydantic.                                        |                |

---

## `POST` `/api/v1/addresses`

**Crear direccion**

Rol permitido: buyer. HU-USR-03. Crea una direccion de envio asociada al comprador autenticado.

**Tags:** buyer

### Request body

### Respuesta `201`

Direccion creada y disponible para checkout.

### Errores posibles

| Código | Situación                                                   | Mensaje típico |
| ------ | ----------------------------------------------------------- | -------------- |
| 401    | Token requerido o invalido.                                 |                |
| 403    | Requiere rol buyer o recurso fuera del scope del comprador. |                |
| 404    | Direccion no encontrada.                                    |                |
| 422    | Validacion Pydantic.                                        |                |

---

## `PATCH` `/api/v1/addresses/{address_id}`

**Actualizar direccion**

Rol permitido: buyer. HU-USR-03. Actualiza solo una direccion propia del comprador autenticado.

**Tags:** buyer

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| address_id | string | ✓         |             |

### Request body

### Respuesta `200`

Direccion actualizada.

### Errores posibles

| Código | Situación                                                   | Mensaje típico |
| ------ | ----------------------------------------------------------- | -------------- |
| 401    | Token requerido o invalido.                                 |                |
| 403    | Requiere rol buyer o recurso fuera del scope del comprador. |                |
| 404    | Direccion no encontrada.                                    |                |
| 422    | Validacion Pydantic.                                        |                |

---

## `DELETE` `/api/v1/addresses/{address_id}`

**Eliminar direccion**

Rol permitido: buyer. HU-USR-03. Elimina solo una direccion propia del comprador autenticado.

**Tags:** buyer

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| address_id | string | ✓         |             |

### Respuesta `204`

Direccion eliminada sin contenido.

### Errores posibles

| Código | Situación                                                   | Mensaje típico |
| ------ | ----------------------------------------------------------- | -------------- |
| 401    | Token requerido o invalido.                                 |                |
| 403    | Requiere rol buyer o recurso fuera del scope del comprador. |                |
| 404    | Direccion no encontrada.                                    |                |
| 422    | Validacion Pydantic.                                        |                |

---

## `GET` `/api/v1/favorites`

**List Favorites**

**Tags:** buyer

### Respuesta `200`

Successful Response

---

## `POST` `/api/v1/favorites/{product_id}`

**Add Favorite**

**Tags:** buyer

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |

### Respuesta `201`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `DELETE` `/api/v1/favorites/{product_id}`

**Remove Favorite**

**Tags:** buyer

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |

### Respuesta `204`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/cart`

**Get Cart**

**Tags:** buyer

### Respuesta `200`

Successful Response

---

## `DELETE` `/api/v1/cart`

**Clear Cart**

**Tags:** buyer

### Respuesta `200`

Successful Response

---

## `POST` `/api/v1/cart/items`

**Add Cart Item**

**Tags:** buyer

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/cart/items/{item_id}`

**Patch Cart Item**

**Tags:** buyer

### Parámetros de ruta

| Nombre  | Tipo   | Requerido | Descripción |
| ------- | ------ | --------- | ----------- |
| item_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `DELETE` `/api/v1/cart/items/{item_id}`

**Delete Cart Item**

**Tags:** buyer

### Parámetros de ruta

| Nombre  | Tipo   | Requerido | Descripción |
| ------- | ------ | --------- | ----------- |
| item_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/checkout/quote`

**Cotizar checkout**

Rol permitido: buyer. HU-PROM-01, HU-PROM-02 y HU-PROM-04. Calcula precios efectivos, descuentos, cupones, cargos extra desglosados y envio antes de crear pedidos.

**Tags:** buyer

### Request body

### Respuesta `200`

Cotizacion del checkout con descuentos y cargos separados.

### Errores posibles

| Código | Situación                   | Mensaje típico |
| ------ | --------------------------- | -------------- |
| 400    | Cupon invalido o expirado.  |                |
| 401    | Token requerido o invalido. |                |
| 403    | Requiere rol buyer.         |                |
| 422    | Validacion Pydantic.        |                |

---

## `POST` `/api/v1/checkout`

**Crear checkout**

Rol permitido: buyer. HU-PROM-01, HU-PROM-02 y HU-PROM-04. Crea pedidos usando precio efectivo, promociones, cupones vigentes y cargos extra desglosados por tienda.

**Tags:** buyer

### Request body

### Respuesta `201`

Pedidos creados con pagos pendientes y ajustes historicos.

### Errores posibles

| Código | Situación                                                     | Mensaje típico |
| ------ | ------------------------------------------------------------- | -------------- |
| 400    | Carrito vacio, cupon invalido o metodo de pago no disponible. |                |
| 401    | Token requerido o invalido.                                   |                |
| 403    | Direccion fuera del comprador.                                |                |
| 409    | Stock insuficiente.                                           |                |
| 422    | Validacion Pydantic.                                          |                |

---

## `GET` `/api/v1/orders`

**Buyer Orders**

**Tags:** buyer

### Parámetros de query

| Nombre | Tipo   | Requerido | Descripción |
| ------ | ------ | --------- | ----------- |
| status | string |           |             |

### Respuesta `200`

Successful Response

```json
[
  {}
]
```

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/orders/{order_id}`

**Buyer Order**

**Tags:** buyer

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/orders/{order_id}/cancel`

**Cancel Order**

**Tags:** buyer

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/orders/{order_id}/payment`

**Buyer Order Payment**

Estado del pago, cuenta destino y comprobante ya subido.

**Tags:** buyer

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/orders/{order_id}/payment/receipt`

**Upload Payment Receipt**

Sube (o reemplaza) el comprobante y deja el pago en revisión del vendedor.

**Tags:** buyer

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/seller/dashboard`

**Seller Dashboard**

**Tags:** seller

### Parámetros de query

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| date_from | string |           |             |
| date_to   | string |           |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/seller/reports/sales`

**Seller Sales Report**

**Tags:** seller

### Parámetros de query

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| date_from | string |           |             |
| date_to   | string |           |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/seller/store/members`

**Listar usuarios de mi tienda**

Rol permitido: seller. HU-USR-05. Permite al vendedor consultar usuarios activos e inactivos asociados a su misma tienda, sin crearlos ni desactivarlos.

**Tags:** seller

### Respuesta `200`

Usuarios asociados a la tienda del vendedor.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Recurso no encontrado.                                            |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `GET` `/api/v1/seller/orders`

**Seller Orders**

**Tags:** seller

### Parámetros de query

| Nombre  | Tipo   | Requerido | Descripción |
| ------- | ------ | --------- | ----------- |
| status  | string |           |             |
| channel | string |           |             |

### Respuesta `200`

Successful Response

```json
[
  {}
]
```

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/seller/orders/{order_id}/status`

**Patch Order Status**

**Tags:** seller

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/seller/orders/{order_id}/warehouse`

**Assign Order Warehouse**

**Tags:** seller

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/seller/pos/orders`

**Create Pos Order**

**Tags:** seller

### Request body

### Respuesta `201`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/seller/promotions`

**Listar promociones**

Rol permitido: seller. HU-PROM-02. Lista promociones de porcentaje, valor fijo o volumen configuradas para la tienda autenticada.

**Tags:** seller

### Parámetros de query

| Nombre | Tipo   | Requerido | Descripción |
| ------ | ------ | --------- | ----------- |
| active | string |           |             |

### Respuesta `200`

Promociones de la tienda con vigencia, alcance y estado.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `POST` `/api/v1/seller/promotions`

**Crear promocion**

Rol permitido: seller. HU-PROM-02. Crea una promocion con vigencia y alcance de tienda o productos propios; las promociones de volumen se aplican automaticamente en checkout.

**Tags:** seller

### Request body

### Respuesta `201`

Promocion creada.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `PATCH` `/api/v1/seller/promotions/{promotion_id}`

**Actualizar promocion**

Rol permitido: seller. HU-PROM-02. Actualiza una promocion propia, su vigencia, valor, alcance o estado activo para pedidos nuevos.

**Tags:** seller

### Parámetros de ruta

| Nombre       | Tipo   | Requerido | Descripción |
| ------------ | ------ | --------- | ----------- |
| promotion_id | string | ✓         |             |

### Request body

### Respuesta `200`

Promocion actualizada.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `DELETE` `/api/v1/seller/promotions/{promotion_id}`

**Desactivar promocion**

Rol permitido: seller. HU-PROM-02. Desactiva una promocion propia para que deje de aplicar a pedidos nuevos.

**Tags:** seller

### Parámetros de ruta

| Nombre       | Tipo   | Requerido | Descripción |
| ------------ | ------ | --------- | ----------- |
| promotion_id | string | ✓         |             |

### Respuesta `200`

Promocion desactivada.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `GET` `/api/v1/seller/coupons`

**Listar cupones**

Rol permitido: seller. HU-PROM-02. Lista cupones de la tienda autenticada con vigencia, usos y alcance.

**Tags:** seller

### Parámetros de query

| Nombre | Tipo   | Requerido | Descripción |
| ------ | ------ | --------- | ----------- |
| active | string |           |             |

### Respuesta `200`

Cupones configurados por la tienda.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `POST` `/api/v1/seller/coupons`

**Crear cupon**

Rol permitido: seller. HU-PROM-02. Crea un cupon con codigo normalizado, vigencia, usos y alcance de tienda o productos propios.

**Tags:** seller

### Request body

### Respuesta `201`

Cupon creado.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `PATCH` `/api/v1/seller/coupons/{coupon_id}`

**Actualizar cupon**

Rol permitido: seller. HU-PROM-02. Actualiza un cupon propio, incluido codigo, vigencia, usos, alcance o estado activo.

**Tags:** seller

### Parámetros de ruta

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| coupon_id | string | ✓         |             |

### Request body

### Respuesta `200`

Cupon actualizado.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `DELETE` `/api/v1/seller/coupons/{coupon_id}`

**Desactivar cupon**

Rol permitido: seller. HU-PROM-02. Desactiva un cupon propio para que deje de aplicar a pedidos nuevos.

**Tags:** seller

### Parámetros de ruta

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| coupon_id | string | ✓         |             |

### Respuesta `200`

Cupon desactivado.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `GET` `/api/v1/seller/extra-charges`

**Listar cargos extra**

Rol permitido: seller. HU-PROM-04. Lista cargos extra manuales definidos por la tienda para desglose en checkout.

**Tags:** seller

### Parámetros de query

| Nombre | Tipo   | Requerido | Descripción |
| ------ | ------ | --------- | ----------- |
| active | string |           |             |

### Respuesta `200`

Cargos extra de la tienda.

```json
[
  {}
]
```

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `POST` `/api/v1/seller/extra-charges`

**Crear cargo extra**

Rol permitido: seller. HU-PROM-04. Crea un cargo extra manual fijo o porcentual con alcance de tienda o productos propios.

**Tags:** seller

### Request body

### Respuesta `201`

Cargo extra creado.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `PATCH` `/api/v1/seller/extra-charges/{charge_id}`

**Actualizar cargo extra**

Rol permitido: seller. HU-PROM-04. Actualiza nombre, tipo, valor, alcance o estado de un cargo extra propio para pedidos nuevos.

**Tags:** seller

### Parámetros de ruta

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| charge_id | string | ✓         |             |

### Request body

### Respuesta `200`

Cargo extra actualizado.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `DELETE` `/api/v1/seller/extra-charges/{charge_id}`

**Desactivar cargo extra**

Rol permitido: seller. HU-PROM-04. Desactiva un cargo extra para que deje de aplicarse a pedidos nuevos sin alterar pedidos historicos.

**Tags:** seller

### Parámetros de ruta

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| charge_id | string | ✓         |             |

### Respuesta `200`

Cargo extra desactivado.

### Errores posibles

| Código | Situación                                                         | Mensaje típico |
| ------ | ----------------------------------------------------------------- | -------------- |
| 400    | Datos invalidos, vigencia incoherente o productos fuera de scope. |                |
| 401    | Token requerido o invalido.                                       |                |
| 403    | Requiere rol seller o cambio obligatorio de contrasena pendiente. |                |
| 404    | Promocion, cupon, cargo o producto no encontrado.                 |                |
| 409    | Codigo de cupon duplicado en la tienda.                           |                |
| 422    | Validacion Pydantic.                                              |                |

---

## `GET` `/api/v1/seller/customers`

**Seller Customers**

**Tags:** seller

### Respuesta `200`

Successful Response

---

## `GET` `/api/v1/seller/payout-accounts`

**List Payout Accounts**

**Tags:** seller

### Respuesta `200`

Successful Response

---

## `POST` `/api/v1/seller/payout-accounts`

**Create Payout Account**

**Tags:** seller

### Request body

### Respuesta `201`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `PATCH` `/api/v1/seller/payout-accounts/{account_id}`

**Patch Payout Account**

**Tags:** seller

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| account_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `DELETE` `/api/v1/seller/payout-accounts/{account_id}`

**Deactivate Payout Account**

Baja lógica: conserva la referencia en pedidos ya pagados con esa cuenta.

**Tags:** seller

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| account_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/seller/payments`

**Seller Payments**

Bandeja de pagos manuales de la tienda (por defecto, los que esperan revisión).

**Tags:** seller

### Parámetros de query

| Nombre | Tipo   | Requerido | Descripción |
| ------ | ------ | --------- | ----------- |
| status | string |           |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/seller/payments/{payment_id}/confirm`

**Confirm Manual Payment**

El vendedor confirma que el dinero llegó, registrando el monto recibido.

**Tags:** seller

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| payment_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/seller/payments/{payment_id}/reject`

**Reject Manual Payment**

Rechaza el pago: libera el stock reservado y cancela el pedido.

**Tags:** seller

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| payment_id | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/payments/orders/{order_id}/intent`

**Create Payment Intent**

**Tags:** payments

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Parámetros de query

| Nombre         | Tipo   | Requerido | Descripción |
| -------------- | ------ | --------- | ----------- |
| payment_method | string |           |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/payments/webhooks/{provider}`

**Payment Webhook**

**Tags:** payments

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| provider | string | ✓         |             |

### Request body

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/catalog/products/{product_id}/reviews`

**Product Reviews**

**Tags:** reviews

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/catalog/products/{product_id}/reviews`

**Create Review**

**Tags:** reviews

### Parámetros de ruta

| Nombre     | Tipo   | Requerido | Descripción |
| ---------- | ------ | --------- | ----------- |
| product_id | string | ✓         |             |

### Request body

### Respuesta `201`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/reviews/{review_id}/report`

**Report Review**

**Tags:** reviews

### Parámetros de ruta

| Nombre    | Tipo   | Requerido | Descripción |
| --------- | ------ | --------- | ----------- |
| review_id | string | ✓         |             |

### Request body

### Respuesta `201`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `GET` `/api/v1/orders/{order_id}/dispute`

**Order Dispute**

**Tags:** reviews

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Respuesta `200`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---

## `POST` `/api/v1/orders/{order_id}/dispute`

**Create Dispute**

**Tags:** reviews

### Parámetros de ruta

| Nombre   | Tipo   | Requerido | Descripción |
| -------- | ------ | --------- | ----------- |
| order_id | string | ✓         |             |

### Request body

### Respuesta `201`

Successful Response

### Errores posibles

| Código | Situación        | Mensaje típico |
| ------ | ---------------- | -------------- |
| 422    | Validation Error |                |

---
