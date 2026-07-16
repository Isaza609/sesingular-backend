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

La pasarela definitiva, impuestos/facturación, KYC formal y la integración con transportadoras externas siguen aislados como decisiones de integración. El contrato de pagos ya permite conectar Mercado Pago sin cambiar checkout, pedidos ni inventario.
