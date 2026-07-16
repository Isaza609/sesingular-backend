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
- Configuración de métodos de pago aceptados
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
- Selección de método de pago
- Confirmación de pedido con resumen

## 10. Pagos

- Módulo de pagos **por definir** — actualmente en evaluación **Mercado Pago** como pasarela principal
- Requisitos generales independientes de la pasarela final:
  - División de pago entre plataforma (comisión) y vendedor
  - Registro de transacciones y estados (pagado, pendiente, rechazado, reembolsado)
  - Soporte para métodos de pago comunes en la región (tarjeta, transferencia, efectivo/contraentrega si aplica)
  - Conciliación de pagos con pedidos

## 11. Gestión de pedidos

- Estados del pedido: pendiente, confirmado, en preparación, enviado, entregado, cancelado, devuelto
- Campo de almacén asignado (nulo hasta que el vendedor lo defina, si la tienda tiene varios puntos)
- Notificaciones automáticas al comprador y vendedor en cada cambio de estado
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
2. Política de comisión de la plataforma (porcentaje fijo, variable por categoría, etc.)
3. Manejo de impuestos (¿aplica IVA/facturación electrónica según el país?)

## Definiciones ya resueltas

- **Categorías/subcategorías**: cada vendedor las crea y escoge manualmente para sus propios productos; no son globales ni administradas por la plataforma
- **Volumen esperado**: escala media, hasta aproximadamente 30 peticiones (concurrentes) como referencia para dimensionar la arquitectura inicial