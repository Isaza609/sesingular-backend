# API por rol

Todas las rutas están bajo `/api/v1`. Las rutas privadas reciben el token Bearer de Supabase.

## Admin supremo

El router `/admin` solo acepta usuarios con `role=admin`.

- `GET/PATCH /admin/users`, `POST /admin/users`: usuarios y roles.
- `GET/PATCH /admin/stores`, `POST /admin/stores`: tiendas, estado y membresía del propietario.
- `GET/PUT /admin/settings`: comisión y configuración de pasarela.
- `GET /admin/reports/sales`, `GET /admin/reports/inventory`: reportes globales.
- `GET/PATCH /admin/moderation/*`: reseñas reportadas y disputas.

## Admin vendedor

El router `/seller` solo acepta usuarios con `role=seller` y resuelve la tienda mediante `store_members`. Un vendedor no puede consultar ni mutar otra tienda.

- Tienda: `GET/PATCH /seller/store`, `GET/PUT /seller/store/settings`.
- Catálogo: CRUD de `/seller/categories`, `/seller/products`, variantes e imágenes.
- Importación: `POST /seller/products/import` recibe filas normalizadas desde CSV/XLSX.
- Inventario: `/seller/warehouses`, `/seller/inventory` y `/seller/inventory/movements`.
- Pedidos: `GET /seller/orders`, cambios de estado y asignación de almacén.
- POS: `POST /seller/pos/orders` descuenta el mismo inventario que una venta online.
- Promociones: CRUD de `/seller/promotions` y `/seller/coupons`.
- Clientes y reportes: `GET /seller/customers`, `/seller/dashboard` y `/seller/reports/sales`.

## Cliente

El primer acceso autenticado con Supabase crea automáticamente un perfil `buyer`. Los roles `seller` y `admin` deben ser provisionados por el administrador.

- Perfil: `GET/PATCH /auth/me`.
- Catálogo público: `/catalog/stores`, `/catalog/categories`, `/catalog/products` y stock por variante.
- Perfil de envío: CRUD de `/addresses`.
- Carrito: CRUD de `/cart` y `/cart/items`.
- Checkout: `POST /checkout/quote` y `POST /checkout`. El checkout separa automáticamente un carrito multi-tienda en un pedido por tienda.
- Pedidos: `/orders`, cancelación y disputa.
- Reseñas: lectura pública, creación después de un pedido entregado y reporte de contenido.

## Pagos y decisiones pendientes

- `POST /payments/orders/{order_id}/intent` crea o recupera el intento pendiente.
- `POST /payments/webhooks/{provider}` actualiza el pago y el pedido. La firma se valida si existe `webhook_secret` en configuración.

## Pago manual: transferencia bancaria y Bre-B

Método alterno a la pasarela, gestionado por cada vendedor (sin comisiones de intermediarios). Estados del pago: `pending` (sin comprobante) → `in_review` (comprobante subido) → `paid` | `rejected`.

Vendedor:

- `GET/POST /seller/payout-accounts`, `PATCH /seller/payout-accounts/{id}`, `DELETE /seller/payout-accounts/{id}` (baja lógica: conserva la referencia en pedidos ya pagados). Una sola entidad con `type` = `bank` | `bre_b`.
- `GET /seller/payments?status=in_review`: bandeja de comprobantes, con URL firmada del archivo.
- `POST /seller/payments/{id}/confirm` con `{ received_amount, note? }`: registra el monto realmente recibido y confirma el pedido.
- `POST /seller/payments/{id}/reject` con `{ note }`: libera el stock reservado y cancela el pedido.

Comprador:

- `GET /catalog/stores/{store_id}/payment-options` (público): métodos habilitados y cuentas de cobro activas de la tienda.
- `POST /orders/{order_id}/payment/receipt` (multipart): sube o reemplaza el comprobante (JPG/PNG/PDF, máx. 5 MB) y deja el pago en revisión.
- `GET /orders/{order_id}/payment`: estado del pago, cuenta destino y comprobante.

Los comprobantes se guardan en Supabase Storage (bucket privado `comprobantes`, ruta `{tienda_id}/{pedido_id}/`) y se exponen mediante URLs firmadas temporales. Cada cambio de estado dispara notificación por correo al comprador y al vendedor.

La pasarela definitiva, impuestos/facturación, KYC formal y la integración con transportadoras externas siguen aislados como decisiones de integración. El contrato de pagos ya permite conectar Mercado Pago sin cambiar checkout, pedidos ni inventario.
