# Requerimientos del Marketplace de Productos Físicos

## 1. Gestión de usuarios

- Registro e inicio de sesión diferenciado por rol: comprador, vendedor (tienda), administrador de la plataforma
- Verificación de identidad para vendedores (KYC básico: nombre, documento, datos bancarios/de pago)
- Edición de perfil y datos de contacto/envío
- Recuperación de contraseña
- Cada vendedor puede tener uno o más usuarios asociados a su tienda (si aplica, para equipos)

## 2. Gestión de tiendas (vendedores)

- Creación de perfil de tienda (nombre, logo, descripción, datos de contacto)
- Registro de uno o más puntos/almacenes por tienda
- Configuración de métodos de pago aceptados (pasarela automatizada y/o cobro manual)
- Configuración de **cuentas de cobro manual** propias del vendedor (cuentas bancarias y/o llaves Bre-B); pertenecen a la tienda, no a la plataforma
- Configuración de zonas/costos de envío propios de la tienda

## 3. Gestión de categorías y catálogo

- Cada **vendedor** define y escoge de forma manual las categorías y subcategorías de sus propios productos (no hay una estructura global impuesta por la plataforma)
- Estas categorías/subcategorías se muestran únicamente dentro del catálogo de esa tienda (son propias de cada vendedor, no compartidas entre tiendas)
- Soporte de jerarquía categoría → subcategoría
- Posibilidad de asignar un producto a más de una categoría/subcategoría si aplica
- El administrador de la plataforma no gestiona categorías globales bajo este esquema; su rol se limita a moderación general del catálogo si aplica

## 4. Gestión de productos

- Alta, edición y baja de productos por parte del vendedor
- Asignación de categoría y subcategoría
- Soporte para variantes (talla, color, presentación, etc.)
- Carga individual y carga masiva (CSV/Excel)
- Múltiples imágenes por producto/variante
- Definición de precio de venta por producto/variante
- **Registro de costo/precio de materiales o costo de producción** (para cálculo de margen/ganancia)
- Estados del producto: activo, borrador, agotado, descontinuado

## 5. Gestión de precios y promociones

- Precio regular por producto/variante
- Precios especiales/temporales (ofertas)
- Promociones configurables por el vendedor:
  - Descuento por porcentaje o valor fijo
  - Descuento por volumen (ej. compra 3 y lleva 4)
  - Cupones o códigos de descuento
  - Vigencia (fecha inicio/fin) de la promoción
- Cálculo automático de margen de ganancia (precio de venta – costo de materiales)

## 6. Gestión de inventario

- Registro de stock por SKU/variante
- Soporte multi-almacén por tienda (1 punto o varios, según configuración)
- Reserva de stock agregado (entre todos los almacenes de la tienda) al momento de la compra, para evitar sobreventa
- Asignación manual del almacén de despacho por parte del vendedor (solo si la tienda tiene más de un punto); el descuento real de stock ocurre en ese momento
- Si la tienda tiene un solo punto, el descuento de stock es automático e inmediato
- Reposición de stock ante cancelación o devolución
- Alertas de stock bajo o agotado
- Historial de movimientos de inventario (auditoría: entradas, salidas, ajustes)
- Stock visible en tiempo real para el comprador

## 7. Canal de venta (online / presencial)

- Cada transacción debe registrar su canal de origen: `online` o `presencial`
- Módulo de **venta rápida / mini-POS** para que el vendedor registre ventas mano a mano desde su panel, sin necesidad de que el comprador tenga cuenta
- La venta presencial descuenta inventario en tiempo real igual que una compra online
- Reportes comparativos de ventas online vs. presenciales

## 8. Búsqueda y navegación (comprador)

- Buscador con filtros: categoría, subcategoría, precio, disponibilidad, vendedor/tienda
- Ordenamiento: relevancia, precio, más vendidos
- Página de detalle de producto con selección de variantes

## 9. Carrito y checkout

- Carrito persistente por usuario
- Cálculo de subtotal, envío e impuestos
- Validación de stock disponible antes de confirmar
- Selección de método de pago (pasarela automatizada o cobro manual: transferencia / Bre-B)
- Confirmación de pedido con resumen
- En cobro manual: visualización de datos de cuenta/llave y carga de comprobante

## 10. Pagos

- Módulo de pagos con dos vías:
  - **Pasarela automatizada** (por definir; en evaluación **Mercado Pago**)
  - **Cobro manual** (transferencia bancaria / Bre-B), gestionado por cada vendedor sin intermediario financiero
- Requisitos generales independientes de la pasarela final:
  - División de pago entre plataforma (comisión) y vendedor (aplica a pasarela; en cobro manual la comisión se calcula/cobra por acuerdo de plataforma)
  - Registro de transacciones y estados (pagado, pendiente, rechazado, reembolsado)
  - Soporte para métodos de pago comunes en la región (tarjeta, transferencia, Bre-B, efectivo/contraentrega si aplica)
  - Conciliación de pagos con pedidos

### 10.1 Método de pago manual (transferencia bancaria / Bre-B)

Además de la pasarela automatizada, la plataforma debe soportar cobro manual por vendedor: el comprador transfiere directamente a una cuenta/llave del vendedor y sube un comprobante que el vendedor valida. Transferencia bancaria y Bre-B comparten el mismo flujo operativo.

#### Gestión de cuentas de cobro del vendedor

- El vendedor configura, desde su panel, uno o más medios de cobro manual:
  - **Cuenta bancaria**: banco, tipo de cuenta, número de cuenta, titular, documento del titular
  - **Bre-B**: llave (celular, cédula, correo o llave alfanumérica), nombre del titular
- Un vendedor puede tener múltiples cuentas bancarias activas; el comprador elige una al pagar
- Activar/desactivar cada cuenta sin eliminarla (los pedidos históricos conservan la referencia)
- Solo se muestran al comprador las cuentas marcadas como activas
- Recomendación de modelo: una sola entidad `cuentas_cobro_vendedor` con campo `tipo` (`bancaria` / `bre_b`)

#### Selección del método en checkout

- El comprador ve las opciones habilitadas por el vendedor:
  - Pasarela de pago (Mercado Pago, tarjeta, etc.)
  - Transferencia bancaria → selección entre cuentas activas del vendedor
  - Bre-B
  - Efectivo (tienda física / contraentrega) — fuera del alcance de este submódulo, pero comparte confirmación manual
- Si el pedido incluye productos de varios vendedores, el pago manual debe resolverse por vendedor (sub-órdenes) o el carrito se restringe a un solo vendedor (regla pendiente de confirmar)

#### Flujo de pago manual

1. Comprador selecciona transferencia bancaria o Bre-B y elige la cuenta/llave
2. Sistema muestra datos de destino (cuenta o llave, titular, banco) y el monto exacto
3. Comprador realiza la transferencia fuera de la plataforma
4. Comprador sube el comprobante (imagen o PDF) desde el checkout o el detalle del pedido
5. El pago pasa a estado de verificación pendiente
6. El vendedor revisa el comprobante en su panel y confirma o rechaza:
   - **Confirma** → pago confirmado; el pedido sigue el flujo normal (descuento firme de stock, asignación de almacén, etc.)
   - **Rechaza** → pago rechazado; se libera el stock reservado y se notifica al comprador (motivo opcional)

#### Estados de pago (independientes del estado del pedido)

| Estado de pago       | Descripción                                                              |
| -------------------- | ------------------------------------------------------------------------ |
| `pendiente_pago`     | Pedido creado; el comprador aún no sube comprobante                      |
| `comprobante_subido` | Comprador subió el comprobante; esperando revisión del vendedor          |
| `pago_confirmado`    | Vendedor validó que el dinero llegó                                      |
| `pago_rechazado`     | Vendedor no encontró el pago o el comprobante es inválido                |

- El stock se reserva desde que se sube el comprobante
- Solo se descuenta de forma firme cuando el vendedor confirma
- Si se rechaza, se libera el stock reservado

#### Comprobante de pago

- Formatos: imagen (jpg/png) o PDF
- Almacenamiento en bucket S3-compatible, ruta separada (ej. `comprobantes/{tienda_id}/{pedido_id}/`)
- Asociado al pedido; visible para comprador y vendedor
- Opcional: permitir reemplazar el comprobante si el vendedor lo rechazó

#### Notificaciones

- Al comprador: confirmación al subir el comprobante; aviso cuando el vendedor confirma o rechaza
- Al vendedor: aviso cuando hay un comprobante pendiente de revisión

## 11. Gestión de pedidos

- Estados del pedido: pendiente, confirmado, en preparación, enviado, entregado, cancelado, devuelto
- Estado de **pago** independiente del estado del pedido (ver §10.1), especialmente relevante en cobro manual
- Campo de almacén asignado (nulo hasta que el vendedor lo defina, si la tienda tiene varios puntos)
- Notificaciones automáticas al comprador y vendedor en cada cambio de estado (incluye confirmación/rechazo de pago manual)
- Historial de pedidos por usuario y por tienda

## 12. Logística y envíos

- Cálculo de costo de envío según peso/ubicación
- Integración con transportadoras externas
- Registro de guía de envío
- Seguimiento (tracking) del pedido
- Gestión de devoluciones, con reingreso a inventario cuando aplica

## 13. Reputación y confianza

- Calificación y reseña de producto/vendedor tras la compra
- Reporte de problemas o disputas
- Moderación de reseñas por el administrador

## 14. Panel del vendedor

- Dashboard de ventas e inventario (consolidado y por almacén)
- Gestión de productos, categorías/subcategorías, precios y promociones
- Gestión de pedidos propios (incluye asignación de almacén de despacho)
- Gestión de cuentas de cobro manual (bancarias / Bre-B) y revisión de comprobantes de pago
- Módulo de venta rápida/POS
- **Ver ventas generadas** (histórico, por período, por canal)
- **Ver ganancias** (ingresos – costos de materiales – comisión de plataforma)
- Registro y edición de costos de materiales/producción por producto
- Reportes de productos más vendidos y rotación de stock

## 15. Panel de administración (plataforma)

- Gestión de usuarios y tiendas
- Configuración de comisiones y políticas
- Reportes globales de ventas e inventario (todas las tiendas)
- Moderación de contenido y disputas
- Configuración de la pasarela de pago

---

## Requerimientos no funcionales

- **Escalabilidad**: soportar crecimiento en número de productos, vendedores y transacciones concurrentes
- **Consistencia de inventario**: evitar sobreventa bajo alta concurrencia, incluyendo ventas simultáneas online y presenciales
- **Disponibilidad**: alta disponibilidad, especialmente en checkout, pagos y registro de venta presencial
- **Seguridad**: cifrado de datos sensibles, cumplimiento con normas de pago (PCI DSS si se maneja tarjetas directamente; mitigado si se usa Mercado Pago como intermediario)
- **Rendimiento**: tiempos de respuesta rápidos en búsqueda, catálogo y registro de venta rápida (POS)
- **Auditoría**: trazabilidad de cambios en inventario, precios, costos y pedidos
- **Usabilidad**: experiencia simple para vendedores no técnicos (carga de productos, POS, reportes)
- **Multi-tienda**: aislamiento de datos entre vendedores (cada uno ve solo su inventario, pedidos, costos y ganancias)

---

## Puntos abiertos / por definir

1. Pasarela de pago definitiva (Mercado Pago en evaluación) y sus implicaciones técnicas (webhooks, comisiones, tiempos de acreditación)
2. Política de comisión de la plataforma (porcentaje fijo, variable por categoría, etc.), incluyendo cómo se cobra cuando el pago es manual (sin intermediario)
3. Manejo de impuestos (¿aplica IVA/facturación electrónica según el país?)
4. Checkout multi-vendedor: ¿una orden con pago manual por vendedor (sub-órdenes) o carrito restringido a un solo vendedor?
5. Cobro manual — casos borde:
   - Tiempo límite de reserva de stock si el comprador nunca sube el comprobante (¿expiración automática del pedido?)
   - Recordatorio automático al vendedor si hay comprobante sin revisar tras X horas
   - Monto incorrecto (parcial o de más): ¿confirmación parcial o rechazo obligatorio si no coincide exactamente?

## Definiciones ya resueltas

- **Categorías/subcategorías**: cada vendedor las crea y escoge manualmente para sus propios productos; no son globales ni administradas por la plataforma
- **Volumen esperado**: escala media, hasta aproximadamente 30 peticiones (concurrentes) como referencia para dimensionar la arquitectura inicial
- **Cobro manual**: transferencia bancaria y Bre-B comparten el mismo flujo (transferencia directa + comprobante + validación del vendedor); las cuentas/llaves pertenecen al vendedor (`tienda_id`), no a la plataforma
- **Modelo de cuentas de cobro**: una sola entidad `cuentas_cobro_vendedor` con campo `tipo` (`bancaria` / `bre_b`)
