# Historias de Usuario — Marketplace de Productos Físicos (v3)

Formato: HU-[MÓDULO]-[NN] — Título / Como [rol], quiero [acción] para [objetivo] / Descripción / Criterios de aceptación (Dado que… cuando… entonces…) / Ejemplo.

Módulos: USR (Usuarios) · TDA (Tiendas) · CAT (Categorías) · PROD (Productos) · PROM (Precios y promociones) · INV (Inventario) · CANAL (Canal de venta) · BUS (Búsqueda) · CHK (Carrito y checkout) · PAG (Pagos) · FAC (Facturación al comprador) · PED (Pedidos) · ENV (Envíos y entregas) · REP (Reputación) · VEN (Panel vendedor) · ADM (Panel administración)

---

## Cambios respecto a la v1 (resumen de decisiones)

| Decisión | Impacto |
| --- | --- |
| El vendedor **no se autorregistra**. El administrador crea la cuenta y la tienda, y le entrega credenciales. | Se elimina la HU de registro + KYC de vendedor y la de creación de perfil de tienda. Se reemplazan por HU-ADM-01, HU-ADM-02 y HU-USR-02. |
| El vendedor **sí edita** la información de contacto pública de su tienda (redes sociales, teléfono, descripción). | Nueva HU-TDA-01. |
| **No hay cálculo automático de costo de envío por peso/ubicación ni integración con transportadoras.** El envío lo maneja el vendedor de forma personalizada. | Se elimina la HU-LOG-01 (v1) y la integración con transportadoras de la HU-LOG-02 (v1). Se reemplaza todo el módulo por ENV. |
| El vendedor elige por producto o por tienda: **envío con tarifas propias por lugar**, o **envío a convenir (contactar al vendedor)**. | HU-ENV-01, HU-ENV-02, HU-ENV-03. |
| El vendedor puede configurar **envío gratis** como promoción, incluso limitado a ciertos lugares. | HU-ENV-04. |
| El **seguimiento** del pedido lo actualiza manualmente el vendedor; el comprador solo lo consulta. | HU-ENV-05. |
| Las **reseñas requieren aprobación previa del vendedor** antes de publicarse. | HU-REP-01, HU-REP-02. El administrador conserva moderación posterior (HU-REP-04). |
| La **facturación de la plataforma hacia el vendedor** (lo que le cobramos) es **manual y fuera de la plataforma**: solo se registra en un formulario del panel de admin. | HU-ADM-03, HU-ADM-04. |
| La **facturación del comprador hacia el vendedor** sí ocurre dentro de la plataforma. | Módulo FAC. |
| Ante un **pago manual por monto incorrecto**, el vendedor puede notificar al comprador (perfil + correo) para que abone la diferencia, sin rechazar el pedido. | HU-PAG-07. |

## Cambios de la v3 (cierre de puntos abiertos)

| Punto abierto v2 | Decisión | Impacto |
| --- | --- | --- |
| Checkout multi-vendedor | La compra **se asigna a la tienda** y se gestiona desde **un único panel** por tienda. Internamente la tienda resuelve desde qué punto/almacén la atiende. | HU-CHK-05, HU-PED-01. |
| Expiración de reserva de stock | **No hay expiración automática.** El pedido puede quedar pendiente indefinidamente; el vendedor lo anula manualmente cuando quiera y eso libera el stock. | HU-PED-04 (nueva). Se elimina la idea de vencimiento automático de HU-PAG-05 y HU-PAG-07. |
| Plazo de revisión de reseñas | **Indefinido.** Una reseña puede quedar pendiente sin límite de tiempo; no hay publicación automática. | HU-REP-02. |
| Manejo de impuestos | No hay cálculo automático de impuestos. El **vendedor define sus propios cargos extra**, tantos como quiera, en un formulario de costos. | HU-PROM-04 (nueva), HU-CHK-02, HU-FAC-01. |
| Usuarios de equipo del vendedor | Los pedidos **no se asignan automáticamente** a nadie: cualquier usuario de la tienda puede tomarlos y se asigna manualmente quién los gestiona. | HU-PED-05 (nueva), HU-USR-05. |
| Monto de más / de menos en pago manual | Se registra la **novedad** en el panel. Si faltó dinero, el vendedor **reabre la carga de comprobante** para que el comprador suba uno nuevo. Si sobró, el vendedor **contacta directamente al comprador** y deja el registro del acuerdo en su panel. | HU-PAG-07. |

---

## Epica 01: Gestión de usuarios

### HU-USR-01 — Registro e inicio de sesión de comprador
Como comprador, quiero registrarme e iniciar sesión en la plataforma para poder comprar productos y hacer seguimiento de mis pedidos.

Descripción
El comprador es el único rol con autorregistro abierto. Crea su cuenta con correo y contraseña y posteriormente inicia sesión con esas credenciales. Los roles de vendedor y administrador se crean exclusivamente desde el panel de administración.

Criterios de aceptación
* Dado que ingreso un correo válido no registrado y una contraseña que cumple la política mínima, cuando confirmo el registro, entonces se crea mi cuenta con rol comprador y quedo autenticado.
* Dado que ingreso un correo ya registrado, cuando intento registrarme, entonces el sistema rechaza la operación con un mensaje descriptivo.
* Dado que intento registrarme como vendedor desde el formulario público, cuando busco esa opción, entonces no existe: el único rol autorregistrable es comprador.
* Dado que ingreso credenciales incorrectas, cuando intento iniciar sesión, entonces el sistema rechaza el acceso sin revelar cuál dato es incorrecto.

Ejemplo
Una persona entra por primera vez a la plataforma, crea su cuenta con su correo y queda lista para agregar productos al carrito.

### HU-USR-02 — Primer ingreso del vendedor con credenciales entregadas
Como vendedor, quiero ingresar con las credenciales que me entregó la plataforma y cambiar mi contraseña para operar mi tienda de forma segura.

Descripción
El vendedor recibe usuario y contraseña temporal creados por el administrador (ver HU-ADM-01). En su primer ingreso el sistema le exige cambiar la contraseña antes de darle acceso al panel.

Criterios de aceptación
* Dado que recibí credenciales temporales, cuando ingreso por primera vez, entonces el sistema me obliga a definir una contraseña nueva antes de continuar.
* Dado que defino una contraseña nueva que cumple la política mínima, cuando la guardo, entonces accedo al panel de mi tienda ya creada.
* Dado que intento omitir el cambio de contraseña, cuando navego a cualquier sección del panel, entonces el sistema me redirige al cambio obligatorio.
* Dado que mi contraseña temporal fue invalidada o expiró, cuando intento usarla, entonces el sistema me indica que contacte al administrador.

Ejemplo
El dueño de "Nova Ropa" recibe por correo su usuario y una contraseña temporal; al entrar, define su propia contraseña y ya encuentra su tienda creada con su catálogo listo para cargar.

### HU-USR-03 — Edición de perfil y datos de contacto/envío del comprador
Como comprador, quiero editar mi perfil y mis datos de contacto y envío para mantenerlos actualizados.

Descripción
El comprador puede modificar su información personal, de contacto y las direcciones de envío guardadas para usarlas en futuros pedidos.

Criterios de aceptación
* Dado que modifico mi nombre, teléfono o dirección, cuando guardo los cambios, entonces mi perfil refleja la información actualizada.
* Dado que agrego una nueva dirección de envío, cuando la guardo, entonces queda disponible para seleccionar en futuros checkouts.
* Dado que dejo un campo obligatorio vacío, cuando intento guardar, entonces el sistema no permite guardar y señala el campo.

Ejemplo
Un comprador se muda de ciudad y actualiza su dirección antes de hacer su próximo pedido.

### HU-USR-04 — Recuperación de contraseña
Como usuario registrado, quiero recuperar el acceso a mi cuenta si olvido mi contraseña para no perder el acceso a mi historial y mis datos.

Descripción
Flujo de recuperación por correo electrónico con enlace o código de un solo uso y expiración. Aplica tanto a compradores como a vendedores.

Criterios de aceptación
* Dado que solicito recuperar mi contraseña con un correo registrado, cuando confirmo la solicitud, entonces recibo un enlace o código para restablecerla.
* Dado que el enlace o código recibido está vigente, cuando lo utilizo con una nueva contraseña válida, entonces puedo iniciar sesión con la nueva contraseña.
* Dado que el enlace o código expiró, cuando intento usarlo, entonces el sistema lo rechaza y me permite solicitar uno nuevo.

Ejemplo
Un vendedor olvida su contraseña tras vacaciones; solicita el restablecimiento y define una nueva para volver a su panel.

### HU-USR-05 — Usuarios adicionales asociados a una tienda
Como administrador de la plataforma, quiero crear usuarios adicionales asociados a una tienda para que el equipo del vendedor opere el panel sin compartir la cuenta principal.

Descripción
Igual que la cuenta principal del vendedor, los usuarios de equipo son creados desde el panel de administración y quedan vinculados a una tienda existente. Todos los usuarios de una misma tienda comparten **un único panel** con la misma información: no hay paneles separados por usuario ni reparto automático de pedidos entre ellos (ver HU-PED-05). El vendedor puede ver la lista de usuarios de su tienda y solicitar altas o bajas.

Criterios de aceptación
* Dado que creo un usuario adicional y lo asocio a una tienda, cuando lo guardo, entonces ese usuario recibe credenciales y accede al panel de esa tienda.
* Dado que varios usuarios de una misma tienda ingresan al panel, cuando lo consultan, entonces todos ven los mismos pedidos, inventario y pendientes de la tienda.
* Dado que desactivo un usuario de equipo, cuando lo hago, entonces pierde acceso al panel de inmediato sin afectar los registros históricos que generó.
* Dado que soy vendedor, cuando consulto los usuarios de mi tienda, entonces veo la lista de activos e inactivos aunque no pueda crearlos yo mismo.

Ejemplo
Una tienda con dos empleados solicita al administrador dos usuarios adicionales para que gestionen pedidos sin usar la cuenta del dueño.

---

## Epica 02: Gestión de tiendas (vendedores)

### HU-TDA-01 — Edición de la información pública de la tienda
Como vendedor, quiero editar la información pública de mi tienda (contacto, redes sociales, descripción) para que los compradores me encuentren y me contacten.

Descripción
El perfil de la tienda es creado por el administrador (HU-ADM-02). El vendedor no puede crearlo ni eliminarlo, pero sí mantener actualizados los datos que se muestran a los compradores: descripción, logo, teléfono, WhatsApp, correo de contacto y enlaces a redes sociales.

Criterios de aceptación
* Dado que edito mi teléfono, correo o enlaces de redes sociales, cuando guardo los cambios, entonces la ficha pública de mi tienda los refleja de inmediato.
* Dado que actualizo el logo o la descripción de mi tienda, cuando guardo, entonces los compradores ven la versión actualizada en el catálogo.
* Dado que intento cambiar el nombre legal de la tienda o eliminarla, cuando lo intento, entonces el sistema no lo permite e indica que es una gestión del administrador.
* Dado que ingreso un enlace de red social con formato inválido, cuando intento guardar, entonces el sistema lo rechaza señalando el campo.

Ejemplo
Una tienda abre una cuenta nueva de Instagram y actualiza el enlace desde su panel para que aparezca en su perfil público.

### HU-TDA-02 — Registro de puntos/almacenes de la tienda
Como vendedor, quiero registrar uno o más puntos/almacenes de mi tienda para reflejar dónde tengo inventario disponible.

Descripción
Cada tienda puede operar con un único almacén o con varios; el registro de puntos habilita el manejo de inventario multi-almacén (módulo INV).

Criterios de aceptación
* Dado que registro un nuevo almacén con nombre y dirección, cuando lo guardo, entonces queda disponible para asociarle stock.
* Dado que mi tienda tiene un solo almacén, cuando reviso la configuración, entonces el sistema no me exige selección manual de almacén de despacho en los pedidos.
* Dado que desactivo un almacén, cuando lo hago, entonces deja de estar disponible para nuevas asignaciones de despacho, sin afectar pedidos históricos.

Ejemplo
Una tienda que abre una segunda bodega en otra ciudad la registra como nuevo punto para distribuir stock entre ambas.

### HU-TDA-03 — Configuración de métodos de pago aceptados por la tienda
Como vendedor, quiero definir qué métodos de pago acepta mi tienda para adaptarme a mi operación.

Descripción
El vendedor habilita, entre pasarela automatizada y/o cobro manual (transferencia bancaria, Bre-B), cuáles ofrecerá a sus compradores en el checkout.

Criterios de aceptación
* Dado que habilito la pasarela automatizada, cuando un comprador llega al checkout, entonces ve esa opción disponible.
* Dado que habilito cobro manual, cuando un comprador llega al checkout, entonces ve transferencia bancaria y/o Bre-B según las cuentas activas que tenga configuradas.
* Dado que deshabilito un método de pago, cuando un comprador entra al checkout, entonces ese método ya no aparece como opción.

Ejemplo
Una tienda pequeña habilita únicamente cobro manual mientras completa su proceso con la pasarela.

---

## Epica 03: Gestión de categorías y catálogo

### HU-CAT-01 — Creación de categorías y subcategorías propias de la tienda
Como vendedor, quiero crear mis propias categorías y subcategorías para organizar mi catálogo como mejor se adapte a mi negocio.

Descripción
Cada vendedor define manualmente su estructura de categorías; no existe una taxonomía global impuesta por la plataforma. Las categorías creadas son visibles únicamente dentro del catálogo de esa tienda.

Criterios de aceptación
* Dado que creo una categoría nueva, cuando la guardo, entonces queda disponible para asignarla a mis productos.
* Dado que creo una subcategoría dentro de una categoría existente, cuando la guardo, entonces se refleja la jerarquía categoría → subcategoría en mi catálogo.
* Dado que un comprador navega el catálogo de mi tienda, cuando explora las categorías, entonces solo ve las categorías que yo definí, no las de otras tiendas.

Ejemplo
La tienda "Nova Ropa" crea la categoría "Camisas" con subcategorías "Manga larga" y "Manga corta", exclusivas de su catálogo.

### HU-CAT-02 — Asignación de un producto a múltiples categorías
Como vendedor, quiero poder asignar un producto a más de una categoría o subcategoría cuando aplique para que sea más fácil de encontrar.

Descripción
Un producto puede pertenecer simultáneamente a varias categorías/subcategorías de la misma tienda.

Criterios de aceptación
* Dado que edito un producto, cuando le asigno dos o más categorías, entonces el producto aparece al navegar cualquiera de ellas.
* Dado que remuevo una de las categorías asignadas, cuando guardo el cambio, entonces el producto deja de aparecer en esa categoría específica.

Ejemplo
Una chaqueta se publica bajo "Abrigos" y también bajo "Novedades" para darle mayor visibilidad.

---

## Epica 04: Gestión de productos

### HU-PROD-01 — Alta y edición de productos
Como vendedor, quiero crear y editar productos en mi catálogo para mantenerlo actualizado.

Descripción
Alta manual de un producto con su información básica (nombre, descripción, categoría, precio, imágenes) y edición posterior de esos datos.

Criterios de aceptación
* Dado que completo los datos obligatorios de un producto nuevo, cuando lo guardo, entonces aparece en mi catálogo con el estado que definí.
* Dado que edito un producto existente, cuando guardo los cambios, entonces el catálogo público refleja la información actualizada.
* Dado que doy de baja un producto, cuando confirmo la baja, entonces deja de ser visible para los compradores.

Ejemplo
Un vendedor de accesorios sube un nuevo collar con fotos, precio y descripción, y una semana después ajusta el precio.

### HU-PROD-02 — Gestión de variantes de producto
Como vendedor, quiero definir variantes de un producto (talla, color, presentación) para vender sus distintas versiones bajo una sola ficha.

Descripción
Cada producto puede tener variantes con su propio precio, stock e imágenes cuando aplique.

Criterios de aceptación
* Dado que agrego variantes de talla y color a un producto, cuando las guardo, entonces cada combinación queda disponible como opción seleccionable.
* Dado que una variante específica está agotada, cuando un comprador visita la ficha, entonces esa combinación aparece como no disponible mientras las demás siguen disponibles.
* Dado que asigno un precio distinto a una variante, cuando el comprador la selecciona, entonces ve el precio correspondiente a esa variante.

Ejemplo
Una camisa se publica con variantes de talla S, M y L, cada una con su propio stock.

### HU-PROD-03 — Carga masiva de productos
Como vendedor, quiero cargar varios productos a la vez mediante un archivo para no tener que crearlos uno por uno.

Descripción
Carga de productos mediante archivo CSV/Excel con validación de formato y reporte de errores por fila.

Criterios de aceptación
* Dado que subo un archivo con el formato esperado, cuando lo proceso, entonces todos los productos válidos se crean en mi catálogo.
* Dado que algunas filas tienen datos inválidos o incompletos, cuando proceso el archivo, entonces el sistema crea los productos válidos y me informa qué filas fallaron y por qué.
* Dado que quiero conocer el formato esperado, cuando solicito la plantilla, entonces puedo descargar un archivo de ejemplo.

Ejemplo
Una tienda que migra desde otra plataforma carga 200 productos de una sola vez mediante un archivo Excel.

### HU-PROD-04 — Gestión de imágenes múltiples por producto/variante
Como vendedor, quiero subir varias imágenes por producto o variante para mostrarlo desde distintos ángulos.

Descripción
Soporte de galería de imágenes asociadas a un producto o a variantes específicas.

Criterios de aceptación
* Dado que subo varias imágenes a un producto, cuando las guardo, entonces el comprador puede navegar entre ellas en la ficha del producto.
* Dado que asigno imágenes específicas a una variante, cuando el comprador selecciona esa variante, entonces ve las imágenes correspondientes.
* Dado que elimino una imagen, cuando confirmo la eliminación, entonces deja de mostrarse en la ficha.

Ejemplo
Un zapato se publica con fotos frontal, lateral y de la suela, y con fotos distintas por color.

### HU-PROD-05 — Registro de costo de materiales o producción
Como vendedor, quiero registrar el costo de materiales o producción de cada producto para poder calcular mi margen de ganancia.

Descripción
Campo interno, no visible al comprador, usado para el cálculo automático de margen y para reportes de ganancias.

Criterios de aceptación
* Dado que registro el costo de materiales de un producto, cuando lo guardo, entonces el sistema lo usa para calcular el margen de ese producto.
* Dado que un comprador visita la ficha del producto, cuando la consulta, entonces no ve el costo de materiales registrado.
* Dado que actualizo el costo de materiales, cuando lo guardo, entonces el margen se recalcula con el nuevo valor.

Ejemplo
Un vendedor registra que una camisa le cuesta $30.000 producir, para compararlo con su precio de venta de $70.000.

### HU-PROD-06 — Gestión de estados del producto
Como vendedor, quiero cambiar el estado de un producto (activo, borrador, agotado, descontinuado) para controlar su visibilidad y disponibilidad.

Descripción
Cada producto tiene un estado que determina si es visible y comprable en el catálogo público.

Criterios de aceptación
* Dado que un producto está en estado "borrador", cuando un comprador navega el catálogo, entonces no lo ve.
* Dado que un producto está "agotado", cuando un comprador lo visita, entonces lo ve pero no puede agregarlo al carrito.
* Dado que cambio un producto a "descontinuado", cuando guardo el cambio, entonces deja de ser visible en el catálogo pero se conserva en el historial de pedidos pasados.

Ejemplo
Un vendedor deja un producto en "borrador" mientras completa sus fotos, antes de publicarlo como "activo".

---

## Epica 05: Gestión de precios y promociones

### HU-PROM-01 — Configuración de precio regular y precios especiales
Como vendedor, quiero definir el precio regular de un producto y precios especiales temporales para poder ofrecer ofertas.

Descripción
Un producto/variante tiene un precio regular y, opcionalmente, un precio especial vigente durante un período definido.

Criterios de aceptación
* Dado que defino un precio especial con fecha de inicio y fin, cuando el período está vigente, entonces el comprador ve el precio especial en lugar del regular.
* Dado que el período del precio especial termina, cuando un comprador visita el producto después, entonces ve el precio regular.
* Dado que no he definido precio especial, cuando un comprador visita el producto, entonces ve únicamente el precio regular.

Ejemplo
Una tienda pone un collar en oferta del 1 al 15 del mes, y a partir del 16 el precio vuelve automáticamente a su valor regular.

### HU-PROM-02 — Configuración de promociones (descuentos, cupones, volumen)
Como vendedor, quiero configurar promociones de distintos tipos (porcentaje, valor fijo, volumen, cupones) para incentivar la compra.

Descripción
Motor de promociones configurable por el vendedor, con vigencia definida, aplicable a productos o a toda la tienda. La promoción de envío gratis se configura en HU-ENV-04.

Criterios de aceptación
* Dado que configuro un cupón con código y vigencia, cuando un comprador lo ingresa dentro del período válido, entonces el descuento se aplica en el carrito.
* Dado que configuro una promoción de volumen (ej. compra 3 y lleva 4), cuando el comprador cumple la condición, entonces el sistema aplica el beneficio automáticamente.
* Dado que un cupón ya expiró, cuando un comprador intenta usarlo, entonces el sistema lo rechaza con un mensaje descriptivo.

Ejemplo
Una tienda lanza el cupón "VERANO10", válido todo enero, con 10% de descuento.

### HU-PROM-03 — Cálculo automático de margen de ganancia
Como vendedor, quiero ver el margen de ganancia calculado automáticamente para cada producto para tomar mejores decisiones de precio.

Descripción
El sistema calcula el margen como la diferencia entre precio de venta y costo de materiales registrado.

Criterios de aceptación
* Dado que un producto tiene precio de venta y costo de materiales registrados, cuando consulto su ficha en el panel, entonces veo el margen calculado.
* Dado que actualizo el precio de venta o el costo de materiales, cuando guardo el cambio, entonces el margen mostrado se actualiza de inmediato.
* Dado que un producto no tiene costo de materiales registrado, cuando consulto su margen, entonces el sistema indica que falta ese dato en lugar de mostrar un valor incorrecto.

Ejemplo
Un vendedor ve que un producto con precio $50.000 y costo $20.000 tiene un margen de $30.000 (60%).

### HU-PROM-04 — Formulario de costos y cargos extra definidos por el vendedor
Como vendedor, quiero definir en un formulario los cargos extra que aplico a mis ventas para que el total refleje mis costos reales sin depender de un cálculo impuesto por la plataforma.

Descripción
La plataforma **no calcula impuestos automáticamente**. Cada vendedor decide si aplica cargos extra y los registra él mismo en un formulario de costos. Puede agregar **tantos cargos como quiera**, cada uno con nombre visible al comprador, tipo (valor fijo o porcentaje sobre el subtotal), valor, y ámbito de aplicación (toda la tienda o productos específicos). Los cargos activos se muestran desglosados en el checkout (HU-CHK-02) y en el comprobante (HU-FAC-01).

Criterios de aceptación
* Dado que agrego un cargo extra con nombre, tipo y valor, cuando lo guardo, entonces aparece desglosado con ese nombre en el checkout de los pedidos nuevos que cumplen su ámbito.
* Dado que agrego varios cargos extra, cuando un comprador llega al checkout, entonces ve cada uno listado por separado con su valor, no agrupados en un único monto.
* Dado que no defino ningún cargo extra, cuando un comprador llega al checkout, entonces el total es únicamente subtotal más envío, sin líneas adicionales.
* Dado que desactivo o elimino un cargo extra, cuando lo hago, entonces deja de aplicarse a pedidos nuevos y los pedidos ya generados conservan los cargos con los que se crearon.
* Dado que edito el valor de un cargo existente, cuando lo guardo, entonces los pedidos nuevos usan el valor actualizado.

Ejemplo
Una tienda agrega un cargo de "Empaque para regalo" de $5.000 y otro de "IVA" del 19%, ambos definidos manualmente por ella; el comprador ve las dos líneas por separado en su checkout.

---

## Epica 06: Gestión de inventario

### HU-INV-01 — Registro de stock por SKU/variante en múltiples almacenes
Como vendedor, quiero registrar el stock de cada SKU en cada uno de mis almacenes para reflejar mi disponibilidad real.

Descripción
El stock se maneja por combinación de SKU/variante y almacén cuando la tienda tiene más de un punto.

Criterios de aceptación
* Dado que registro cantidades de un SKU en dos almacenes distintos, cuando las guardo, entonces el sistema suma ambas cantidades como stock agregado de la tienda.
* Dado que consulto el stock de un producto desde el panel, cuando lo hago, entonces veo el desglose por almacén.

Ejemplo
Una tienda con bodega en Bogotá y en Medellín registra 10 unidades en cada una, para un total de 20 disponibles.

### HU-INV-02 — Reserva de stock agregado al momento de la compra
Como plataforma, quiero reservar el stock agregado de la tienda cuando un comprador confirma su compra para evitar sobreventa.

Descripción
Al confirmarse una compra, el sistema reserva la cantidad comprada contra el stock agregado (suma de todos los almacenes), sin descontarlo aún de un almacén específico si la tienda tiene varios puntos.

Criterios de aceptación
* Dado que un comprador confirma una compra, cuando hay stock agregado suficiente, entonces el sistema reserva esa cantidad y la resta del disponible para otros compradores.
* Dado que dos compradores intentan comprar simultáneamente la última unidad, cuando ambos confirman, entonces solo uno logra reservarla y el otro recibe un mensaje de stock agotado.
* Dado que la tienda tiene un solo punto, cuando se confirma la compra, entonces el descuento de stock es inmediato y automático.

Ejemplo
Quedan 5 unidades repartidas en dos bodegas; un comprador compra 3 y el sistema reserva esas 3 del total agregado.

### HU-INV-03 — Asignación manual de almacén de despacho
Como vendedor con más de un punto, quiero asignar manualmente desde qué almacén se despacha cada pedido para controlar mi logística.

Descripción
Cuando la tienda tiene varios almacenes, el descuento firme de stock ocurre al asignar el almacén de despacho al pedido.

Criterios de aceptación
* Dado que tengo un pedido con stock reservado y más de un almacén, cuando asigno el almacén de despacho, entonces el stock se descuenta de forma firme en ese almacén.
* Dado que aún no he asignado almacén a un pedido, cuando lo consulto, entonces el campo aparece vacío/nulo.
* Dado que mi tienda tiene un único almacén, cuando se confirma un pedido, entonces no se me solicita esta asignación.

Ejemplo
Un pedido llega a una tienda con dos bodegas y el vendedor decide despachar desde la más cercana al comprador.

### HU-INV-04 — Reposición de stock ante cancelación o devolución
Como vendedor, quiero que el stock se repona cuando se cancela o devuelve un pedido para mantener mi inventario correcto.

Criterios de aceptación
* Dado que se cancela un pedido con stock ya descontado, cuando la cancelación se confirma, entonces el stock vuelve a estar disponible en el almacén de origen.
* Dado que se procesa una devolución aprobada, cuando se completa, entonces el stock devuelto se reintegra al inventario.
* Dado que reviso el historial de movimientos, cuando lo consulto, entonces veo registrado el movimiento de reposición con su motivo.

Ejemplo
Un comprador cancela antes del envío; las 2 unidades reservadas vuelven a estar disponibles.

### HU-INV-05 — Alertas de stock bajo o agotado
Como vendedor, quiero recibir alertas cuando el stock de un producto esté bajo o agotado para reabastecerlo a tiempo.

Criterios de aceptación
* Dado que el stock cae por debajo del umbral configurado, cuando ocurre, entonces recibo una alerta de stock bajo.
* Dado que el stock llega a cero, cuando ocurre, entonces recibo una alerta de stock agotado y el producto pasa a ese estado.

Ejemplo
Un vendedor recibe una notificación cuando le quedan 3 unidades de su producto más vendido.

### HU-INV-06 — Historial de movimientos de inventario (auditoría)
Como vendedor, quiero consultar el historial de movimientos de mi inventario para auditar entradas, salidas y ajustes.

Criterios de aceptación
* Dado que ocurre cualquier movimiento de stock, cuando sucede, entonces queda registrado con fecha, cantidad y tipo de movimiento.
* Dado que consulto el historial de un producto filtrado por fecha, cuando aplico el filtro, entonces veo únicamente los movimientos de ese rango.

Ejemplo
Un vendedor investiga una baja inesperada de stock y encuentra un ajuste manual de la semana anterior.

### HU-INV-07 — Visualización de stock en tiempo real para el comprador
Como comprador, quiero ver la disponibilidad real de un producto para saber si puedo comprarlo.

Criterios de aceptación
* Dado que un producto tiene stock disponible, cuando visito su ficha, entonces veo que puedo agregarlo al carrito.
* Dado que un producto se agota mientras lo estoy viendo, cuando intento agregarlo al carrito, entonces el sistema me informa que ya no hay disponibilidad.

Ejemplo
Un comprador ve "últimas 2 unidades disponibles" en un producto popular.

---

## Epica 07: Canal de venta (online / presencial)

### HU-CANAL-01 — Registro de canal de origen de la transacción
Como plataforma, quiero registrar si cada transacción se originó online o presencial para poder reportarlo.

Criterios de aceptación
* Dado que un comprador finaliza una compra desde la tienda online, cuando se genera el pedido, entonces queda registrado con canal `online`.
* Dado que un vendedor registra una venta desde el mini-POS, cuando se genera el pedido, entonces queda registrado con canal `presencial`.

Ejemplo
Una tienda con local físico distingue cuáles ventas del día fueron de mostrador y cuáles web.

### HU-CANAL-02 — Venta rápida / mini-POS
Como vendedor, quiero registrar ventas presenciales desde mi panel sin que el comprador necesite una cuenta para poder atender clientes en mi local.

Criterios de aceptación
* Dado que registro una venta presencial seleccionando productos y cantidades, cuando la confirmo, entonces se descuenta el inventario de inmediato.
* Dado que registro una venta presencial, cuando la confirmo, entonces no se requiere que el comprador tenga cuenta en la plataforma.
* Dado que intento vender más unidades de las disponibles, cuando confirmo, entonces el sistema rechaza la operación indicando la disponibilidad real.

Ejemplo
Un cliente compra un collar en el local y el vendedor lo registra desde el mini-POS; el stock se actualiza al instante.

### HU-CANAL-03 — Reportes comparativos de ventas online vs. presenciales
Como vendedor, quiero comparar mis ventas online contra mis ventas presenciales para entender mejor mi negocio.

Criterios de aceptación
* Dado que selecciono un rango de fechas, cuando genero el reporte, entonces veo el total de ventas online y presenciales por separado y su suma.
* Dado que no hay ventas de un canal en el período, cuando genero el reporte, entonces ese canal se muestra en cero sin generar error.

Ejemplo
Un vendedor descubre que el 70% de sus ventas de diciembre fueron presenciales.

---

## Epica 08: Búsqueda y navegación (comprador)

### HU-BUS-01 — Buscador de productos con filtros
Como comprador, quiero buscar productos con filtros de categoría, precio y disponibilidad para encontrar más rápido lo que busco.

Criterios de aceptación
* Dado que ingreso un término de búsqueda, cuando lo ejecuto, entonces veo los productos cuyo nombre o descripción coinciden.
* Dado que aplico un filtro de rango de precio, cuando lo confirmo, entonces los resultados se limitan a ese rango.
* Dado que combino varios filtros, cuando los aplico, entonces los resultados cumplen todos los filtros simultáneamente.
* Dado que no hay resultados, cuando ejecuto la búsqueda, entonces veo un estado vacío sin error.

Ejemplo
Un comprador busca "camisa" y filtra por precio menor a $80.000 y disponibilidad en stock.

### HU-BUS-02 — Ordenamiento de resultados de búsqueda
Como comprador, quiero ordenar los resultados por relevancia, precio o más vendidos para navegar el catálogo a mi manera.

Criterios de aceptación
* Dado que tengo una lista de resultados, cuando selecciono "precio: menor a mayor", entonces los productos se reordenan según ese criterio.
* Dado que selecciono "más vendidos", cuando aplico el criterio, entonces los productos se ordenan según su volumen de ventas.

Ejemplo
Un comprador ordena los resultados de "zapatos" de menor a mayor precio para ajustarse a su presupuesto.

### HU-BUS-03 — Página de detalle de producto con selección de variantes
Como comprador, quiero ver el detalle de un producto y elegir sus variantes para decidir mi compra.

Descripción
Ficha con imágenes, descripción, precio, selectores de variante y la modalidad de envío que aplica al producto (ver HU-ENV-03).

Criterios de aceptación
* Dado que visito la ficha de un producto con variantes, cuando selecciono una combinación, entonces veo el precio, stock e imágenes correspondientes.
* Dado que selecciono una variante sin stock, cuando lo hago, entonces el botón de agregar al carrito se deshabilita para esa combinación.
* Dado que el producto tiene envío a convenir, cuando visito la ficha, entonces veo esa indicación junto con los datos de contacto del vendedor.

Ejemplo
Un comprador entra a la ficha de una camisa, selecciona talla M y color azul, y ve el precio, las fotos y la modalidad de envío de esa tienda.

---

## Epica 09: Carrito y checkout

### HU-CHK-01 — Carrito de compras persistente
Como comprador, quiero que mi carrito se mantenga guardado entre sesiones para no perder los productos que ya había seleccionado.

Criterios de aceptación
* Dado que agrego productos a mi carrito y cierro sesión, cuando vuelvo a iniciar sesión, entonces mi carrito conserva esos productos.
* Dado que un producto de mi carrito se agota mientras estaba guardado, cuando reviso mi carrito, entonces el sistema me lo señala antes de continuar al checkout.

Ejemplo
Un comprador agrega productos desde su celular y al día siguiente los encuentra en su carrito desde su computador.

### HU-CHK-02 — Desglose del total con envío y cargos definidos por el vendedor
Como comprador, quiero ver el desglose de subtotal, envío y cargos extra antes de pagar para saber exactamente cuánto voy a pagar.

Descripción
El checkout muestra subtotal, el valor de envío según la modalidad configurada por el vendedor y cada cargo extra que este haya definido (HU-PROM-04), cada uno en su propia línea. Cuando la modalidad de envío es "a convenir", no se cobra envío en el checkout y se indica que se acordará directamente con el vendedor.

Criterios de aceptación
* Dado que el vendedor definió tarifas de envío por lugar y mi dirección corresponde a una zona configurada, cuando llego al checkout, entonces veo el valor de envío correspondiente sumado al total.
* Dado que el vendedor tiene cargos extra activos, cuando llego al checkout, entonces veo cada cargo con su nombre y valor en una línea independiente del subtotal y del envío.
* Dado que el vendedor definió el envío como "a convenir", cuando llego al checkout, entonces el total no incluye envío y veo el mensaje de que el costo se acuerda con el vendedor, junto con sus datos de contacto.
* Dado que aplica una promoción de envío gratis para mi lugar, cuando llego al checkout, entonces el envío aparece en cero y señalado como promoción.
* Dado que mi lugar no está entre las zonas configuradas por el vendedor, cuando llego al checkout, entonces el sistema me indica que debo contactar al vendedor para acordar el envío.

Ejemplo
Un comprador de otra ciudad ve que el envío para su zona cuesta $12.000, mientras que otro comprador de la misma ciudad de la tienda ve envío gratis por promoción.

### HU-CHK-03 — Validación de stock disponible antes de confirmar
Como plataforma, quiero validar la disponibilidad real de stock justo antes de confirmar el pedido para evitar vender lo que ya no existe.

Criterios de aceptación
* Dado que todos los productos de mi carrito tienen stock disponible, cuando confirmo el pedido, entonces la compra se procesa con normalidad.
* Dado que un producto de mi carrito se agotó justo antes de confirmar, cuando intento confirmar, entonces el sistema me lo informa y no permite continuar con ese producto hasta que lo ajuste.

Ejemplo
Dos compradores tienen el mismo producto en el carrito; el primero en confirmar se lleva la última unidad.

### HU-CHK-04 — Confirmación de pedido con resumen
Como comprador, quiero recibir un resumen de mi pedido al confirmarlo para tener constancia de lo que compré.

Criterios de aceptación
* Dado que confirmo mi pedido, cuando la confirmación se procesa, entonces veo un resumen completo en pantalla con productos, montos, dirección, método de pago y modalidad de envío.
* Dado que se confirma mi pedido, cuando esto ocurre, entonces recibo también una notificación por correo con el mismo resumen.
* Dado que mi pedido tiene envío a convenir, cuando reviso el resumen, entonces se indica explícitamente que el costo de envío no está incluido y debe acordarse con el vendedor.

Ejemplo
Tras confirmar, el comprador recibe por correo el número de pedido, los productos, el total y la nota de que el envío se coordina por WhatsApp con la tienda.

### HU-CHK-05 — Asignación de la compra a la tienda
Como plataforma, quiero asignar cada compra a la tienda que vende los productos para que esta la gestione desde su único panel.

Descripción
Toda compra queda asignada a una tienda. Si el carrito incluye productos de más de una tienda, la plataforma genera un pedido por tienda, y cada tienda ve únicamente el suyo en su panel. La tienda resuelve internamente desde qué punto o almacén lo atiende (HU-INV-03) y quién de su equipo lo gestiona (HU-PED-05). El comprador conserva una vista unificada de su compra.

Criterios de aceptación
* Dado que confirmo una compra de productos de una sola tienda, cuando se genera el pedido, entonces queda asignado a esa tienda y aparece en su panel.
* Dado que confirmo una compra con productos de varias tiendas, cuando se genera, entonces se crea un pedido por tienda y cada una ve solo el suyo, sin acceso a los datos de las otras tiendas.
* Dado que soy comprador con una compra repartida en varias tiendas, cuando consulto mi historial, entonces veo la compra agrupada con el estado de cada tienda por separado.
* Dado que la tienda tiene varios usuarios, cuando cualquiera de ellos entra al panel, entonces ve el pedido asignado a la tienda, no un panel distinto por usuario.

Ejemplo
Un comprador adquiere una camisa de "Nova Ropa" y un collar de otra tienda; cada tienda recibe su propio pedido en su panel, mientras el comprador ve una sola compra con dos entregas.

---

## Epica 10: Pagos

### HU-PAG-01 — Selección del método de pago en el checkout
Como comprador, quiero elegir entre los métodos de pago habilitados por la tienda para pagar de la forma que prefiera.

Criterios de aceptación
* Dado que la tienda tiene habilitada la pasarela y cobro manual, cuando llego al checkout, entonces veo ambas opciones.
* Dado que selecciono transferencia bancaria o Bre-B, cuando lo hago, entonces el sistema me pide elegir entre las cuentas activas del vendedor.
* Dado que la tienda solo tiene un método habilitado, cuando llego al checkout, entonces solo veo esa opción.

Ejemplo
Un comprador elige pagar por Bre-B en lugar de tarjeta.

### HU-PAG-02 — Pago mediante pasarela automatizada
Como comprador, quiero pagar mi pedido a través de la pasarela para completar mi compra de forma inmediata.

Criterios de aceptación
* Dado que completo el pago con datos válidos, cuando la pasarela confirma la transacción, entonces mi pedido queda con estado de pago confirmado.
* Dado que la pasarela rechaza mi pago, cuando esto ocurre, entonces veo el motivo y puedo intentar con otro método.
* Dado que se confirma un pago por pasarela, cuando esto ocurre, entonces el sistema registra la transacción asociada al pedido.

Ejemplo
Un comprador paga con tarjeta y recibe la confirmación de su pedido en segundos.

### HU-PAG-03 — Configuración de cuentas de cobro manual del vendedor
Como vendedor, quiero registrar mis cuentas bancarias y/o llaves Bre-B para poder recibir pagos manuales de mis compradores.

Descripción
Las cuentas de cobro pertenecen a la tienda, no a la plataforma. El dinero de las ventas llega directamente al vendedor.

Criterios de aceptación
* Dado que registro una cuenta bancaria con banco, tipo de cuenta, número y titular, cuando la guardo, entonces queda disponible como medio de cobro manual de mi tienda.
* Dado que registro una llave Bre-B con su titular, cuando la guardo, entonces queda disponible como medio de cobro manual.
* Dado que tengo varias cuentas activas, cuando un comprador llega al checkout, entonces puede elegir entre todas ellas.

Ejemplo
Una tienda registra su cuenta de ahorros y su llave Bre-B para dar más opciones a sus compradores.

### HU-PAG-04 — Activar o desactivar una cuenta de cobro manual
Como vendedor, quiero activar o desactivar mis cuentas de cobro sin eliminarlas para controlar cuáles ve el comprador sin perder el historial.

Criterios de aceptación
* Dado que desactivo una cuenta de cobro, cuando lo hago, entonces deja de aparecer en el checkout de nuevos pedidos.
* Dado que un pedido anterior usó esa cuenta, cuando lo consulto, entonces la referencia a la cuenta sigue visible.
* Dado que reactivo una cuenta, cuando lo hago, entonces vuelve a mostrarse como opción.

Ejemplo
Un vendedor cambia de banco y desactiva su cuenta antigua sin perder el registro de los pedidos pagados con ella.

### HU-PAG-05 — Flujo de pago manual: subir comprobante
Como comprador, quiero subir el comprobante de mi transferencia o pago Bre-B para que el vendedor confirme que recibió mi pago.

Criterios de aceptación
* Dado que selecciono transferencia bancaria y elijo una cuenta, cuando confirmo el pedido, entonces veo los datos de destino y el monto exacto a pagar.
* Dado que subo un comprobante en imagen o PDF, cuando lo confirmo, entonces el pedido pasa a estado `comprobante_subido` y el stock queda reservado.
* Dado que aún no he subido el comprobante, cuando reviso mi pedido, entonces veo el estado `pendiente_pago`.
* Dado que el vendedor rechazó un comprobante previamente, cuando lo permite el sistema, entonces puedo reemplazarlo por uno nuevo.

Ejemplo
Un comprador transfiere el valor exacto y sube la captura de la transferencia desde el detalle de su pedido.

### HU-PAG-06 — Revisión y confirmación/rechazo del comprobante por el vendedor
Como vendedor, quiero revisar los comprobantes de pago pendientes y confirmarlos o rechazarlos para liberar o descontar el stock correspondiente.

Criterios de aceptación
* Dado que confirmo un comprobante como válido, cuando lo hago, entonces el pedido pasa a `pago_confirmado`, el stock se descuenta de forma firme y el pedido sigue su flujo normal.
* Dado que rechazo un comprobante, cuando lo hago, entonces el pedido pasa a `pago_rechazado`, se libera el stock reservado y se notifica al comprador con el motivo si lo indico.
* Dado que tengo comprobantes pendientes, cuando entro a mi panel, entonces veo un listado claro de los que faltan por revisar.

Ejemplo
Un vendedor verifica en su banco que el dinero llegó y aprueba el comprobante, liberando el pedido para preparación.

### HU-PAG-07 — Registro de novedad y reapertura del pago por monto incorrecto
Como vendedor, quiero registrar la novedad cuando el monto transferido no coincide con el total y reabrir la carga del comprobante para resolver el caso sin rechazar todo el pedido.

Descripción
Al revisar un comprobante, el vendedor registra el **ingreso realmente recibido** junto con una descripción o novedad del caso. Si faltó dinero, **reabre la carga de comprobante** para que el comprador suba uno nuevo por el saldo; el pedido pasa a `pago_incompleto`, el stock sigue reservado y el comprador recibe el aviso en su perfil y por correo. Si el comprador pagó de más, la devolución **no se procesa por la plataforma**: el vendedor contacta directamente al comprador con sus datos de contacto y deja registrada en su panel la novedad y el acuerdo al que llegaron.

Criterios de aceptación
* Dado que reviso un comprobante cuyo monto no coincide con el total, cuando registro el monto recibido junto con la descripción de la novedad, entonces queda asociada al pedido y visible en su historial.
* Dado que faltó dinero y reabro la carga de comprobante, cuando lo hago, entonces el pedido pasa a `pago_incompleto` y el comprador recibe en su perfil y por correo el monto esperado, el recibido, la diferencia pendiente y los datos de la cuenta.
* Dado que reabrí la carga, cuando el comprador sube el comprobante del saldo faltante, entonces el pedido vuelve a `comprobante_subido` para mi revisión.
* Dado que el pedido está en `pago_incompleto`, cuando consulto el inventario, entonces el stock sigue reservado y no se ha descontado de forma firme.
* Dado que el comprador pagó de más, cuando registro la novedad, entonces el sistema me muestra sus datos de contacto para acordar la devolución por fuera y me permite dejar constancia del acuerdo, sin generar ningún movimiento de dinero en la plataforma.
* Dado que el caso nunca se resuelve, cuando decido no continuar, entonces anulo el pedido según HU-PED-04 y el stock reservado se libera.

Ejemplo
Un comprador transfiere $90.000 en lugar de $110.000; el vendedor registra "recibido $90.000, faltan $20.000", reabre la carga de comprobante y el comprador sube el soporte de la diferencia. En otro caso, un comprador transfiere $130.000 de más por error: el vendedor lo llama, acuerdan devolverle el excedente por transferencia y deja la novedad registrada en el panel.

### HU-PAG-08 — Notificaciones del estado de pago manual
Como comprador y como vendedor, quiero recibir notificaciones sobre el estado del pago manual para estar al tanto sin tener que revisar manualmente.

Criterios de aceptación
* Dado que subo un comprobante, cuando lo hago, entonces recibo una notificación de confirmación de la subida.
* Dado que el vendedor confirma, rechaza o marca mi pago como incompleto, cuando esto ocurre, entonces recibo una notificación con el resultado.
* Dado que hay un comprobante pendiente de revisión, cuando esto ocurre, entonces el vendedor recibe una notificación.

Ejemplo
Un comprador recibe una notificación apenas su comprobante es aprobado.

### HU-PAG-09 — Registro y conciliación de transacciones
Como administrador de la plataforma, quiero que todas las transacciones queden registradas con su estado para poder conciliar los pagos con los pedidos.

Descripción
Toda transacción (pasarela o manual) queda registrada con su estado (`pendiente_pago`, `comprobante_subido`, `pago_incompleto`, `pago_confirmado`, `pago_rechazado`, `reembolsado`) y con trazabilidad hacia el pedido correspondiente.

Criterios de aceptación
* Dado que se genera cualquier transacción, cuando esto ocurre, entonces queda registrada con su estado y asociada al pedido.
* Dado que el estado de una transacción cambia, cuando esto ocurre, entonces el historial conserva los estados anteriores.
* Dado que consulto una transacción, cuando lo hago, entonces veo a qué pedido, tienda y método de pago corresponde.

Ejemplo
El equipo de soporte concilia a fin de mes los pagos por pasarela contra los pedidos entregados.

---

## Epica 11: Facturación al comprador

### HU-FAC-01 — Emisión del comprobante/factura de venta al comprador
Como comprador, quiero recibir el comprobante o factura de mi compra para tener soporte de la transacción con el vendedor.

Descripción
La plataforma genera el documento de venta entre el vendedor y el comprador una vez confirmado el pago, con los datos de la tienda, los productos, los cargos extra que el vendedor haya definido (HU-PROM-04) desglosados uno a uno, y el valor de envío cuando corresponda. La plataforma no calcula impuestos por su cuenta. Este documento es independiente del cobro que la plataforma le hace al vendedor (ver HU-ADM-03), que se gestiona por fuera.

Criterios de aceptación
* Dado que mi pago queda confirmado, cuando esto ocurre, entonces el sistema genera el comprobante de venta asociado al pedido y me lo hace disponible para descarga.
* Dado que consulto un pedido pasado, cuando entro a su detalle, entonces puedo descargar nuevamente el comprobante.
* Dado que el pedido tiene envío a convenir, cuando reviso el comprobante, entonces el valor de envío no aparece facturado y se señala como acordado por fuera.
* Dado que el pedido fue cancelado o devuelto, cuando consulto el comprobante, entonces refleja esa condición.

Ejemplo
Un comprador descarga en PDF el comprobante de su compra de $110.000 a la tienda "Nova Ropa" para su registro personal.

### HU-FAC-02 — Datos de facturación del vendedor en el comprobante
Como vendedor, quiero que mis datos aparezcan correctamente en los comprobantes de venta emitidos a mis compradores para que el documento sea válido para mi operación.

Descripción
El administrador registra los datos fiscales/comerciales de la tienda al crearla; el vendedor puede consultarlos y solicitar corrección.

Criterios de aceptación
* Dado que se emite un comprobante de una venta de mi tienda, cuando el comprador lo descarga, entonces incluye el nombre, identificación y datos de contacto registrados para mi tienda.
* Dado que detecto un dato incorrecto, cuando lo reporto al administrador, entonces puede corregirlo desde el panel de administración.
* Dado que el administrador corrige un dato, cuando lo guarda, entonces los comprobantes emitidos a partir de ese momento usan el dato corregido.

Ejemplo
Un vendedor nota que su número de identificación quedó mal digitado, lo reporta y el administrador lo corrige.

### HU-FAC-03 — Consulta de comprobantes emitidos por la tienda
Como vendedor, quiero consultar todos los comprobantes de venta emitidos por mi tienda para llevar el control de mis ventas.

Criterios de aceptación
* Dado que entro a la sección de facturación de mi panel, cuando la consulto, entonces veo el listado de comprobantes emitidos con fecha, comprador, pedido y monto.
* Dado que filtro por rango de fechas o estado del pedido, cuando aplico el filtro, entonces el listado se ajusta al criterio.
* Dado que selecciono un comprobante, cuando lo abro, entonces puedo descargarlo en el mismo formato que lo recibió el comprador.

Ejemplo
Un vendedor descarga todos los comprobantes del mes para entregarlos a su contador.

---

## Epica 12: Gestión de pedidos

### HU-PED-01 — Seguimiento de estados del pedido
Como comprador y como vendedor, quiero ver en qué estado está un pedido para saber qué sigue en el proceso.

Descripción
Cada pedido transita por estados (pendiente, confirmado, en preparación, enviado, entregado, cancelado, devuelto), independientes del estado de pago.

Criterios de aceptación
* Dado que consulto un pedido, cuando lo hago, entonces veo su estado actual y el estado de pago por separado.
* Dado que el vendedor actualiza el estado de un pedido, cuando lo hace, entonces el nuevo estado se refleja de inmediato para el comprador.

Ejemplo
Un comprador ve que su pedido pasó de "en preparación" a "enviado".

### HU-PED-02 — Notificaciones automáticas de cambio de estado
Como comprador y como vendedor, quiero recibir una notificación cada vez que cambia el estado de un pedido para no tener que estar consultando manualmente.

Criterios de aceptación
* Dado que el estado de mi pedido cambia, cuando esto ocurre, entonces recibo una notificación describiendo el nuevo estado.
* Dado que un pedido pasa a "enviado", cuando esto ocurre, entonces comprador y vendedor reciben la notificación correspondiente a su rol.

Ejemplo
Un comprador recibe una notificación tan pronto su pedido es marcado como "entregado".

### HU-PED-03 — Historial de pedidos por usuario y por tienda
Como comprador, quiero ver el historial de todos mis pedidos, y como vendedor, quiero ver el de mi tienda para tener trazabilidad.

Criterios de aceptación
* Dado que soy comprador, cuando consulto mi historial, entonces veo todos mis pedidos pasados con su estado.
* Dado que soy vendedor, cuando consulto el historial de mi tienda, entonces veo únicamente los pedidos de mi tienda.
* Dado que filtro por rango de fechas o estado, cuando aplico el filtro, entonces la lista se ajusta al criterio.

Ejemplo
Un comprador busca en su historial un pedido de hace dos meses para volver a comprar el mismo producto.

### HU-PED-04 — Anulación de un pedido por el vendedor
Como vendedor, quiero anular un pedido desde mi panel para liberar el stock reservado cuando el comprador nunca completa el pago o la venta no se concreta.

Descripción
No existe expiración automática: un pedido puede permanecer pendiente de pago de forma indefinida sin que el sistema lo cancele. La decisión de anularlo es siempre manual del vendedor. Al anular, el stock reservado se libera y el pedido queda registrado como cancelado con su motivo.

Criterios de aceptación
* Dado que un pedido lleva tiempo pendiente de pago, cuando no lo anulo, entonces permanece pendiente indefinidamente con su stock reservado, sin cancelarse solo.
* Dado que anulo un pedido indicando el motivo, cuando confirmo la anulación, entonces el stock reservado se libera y vuelve a estar disponible para otros compradores.
* Dado que anulo un pedido, cuando lo hago, entonces el comprador recibe una notificación con el motivo y el pedido queda en estado "cancelado" en su historial.
* Dado que un pedido ya fue despachado o entregado, cuando intento anularlo, entonces el sistema me indica que debe tratarse como devolución (HU-ENV-06) y no como anulación.
* Dado que consulto el historial de movimientos de inventario, cuando reviso una anulación, entonces veo registrada la liberación de stock con el pedido de origen.

Ejemplo
Un comprador nunca subió el comprobante de su transferencia; tras dos semanas el vendedor anula el pedido indicando "sin pago" y las unidades reservadas vuelven al inventario disponible.

### HU-PED-05 — Asignación manual del responsable de un pedido
Como usuario de una tienda, quiero asignar manualmente quién gestiona cada pedido para que el equipo se reparta el trabajo sin duplicar esfuerzos.

Descripción
Los pedidos llegan a la tienda sin responsable asignado. Cualquier usuario del panel puede tomarlos o asignarlos a otro usuario de la misma tienda, y el responsable puede cambiarse en cualquier momento. La asignación es organizativa: no restringe que otros usuarios de la tienda vean o intervengan en el pedido.

Criterios de aceptación
* Dado que llega un pedido nuevo, cuando lo consulto en el panel, entonces aparece sin responsable asignado.
* Dado que me asigno un pedido o se lo asigno a otro usuario de mi tienda, cuando guardo la asignación, entonces el pedido muestra ese responsable para todo el equipo.
* Dado que un pedido ya tiene responsable, cuando lo reasigno a otro usuario, entonces el cambio queda registrado con su fecha y usuario anterior.
* Dado que filtro los pedidos por responsable, cuando aplico el filtro, entonces veo únicamente los asignados a ese usuario, incluida la opción "sin asignar".
* Dado que un pedido tiene un responsable distinto a mí, cuando lo abro, entonces igual puedo consultarlo y actuar sobre él.

Ejemplo
Una tienda con dos empleados recibe cinco pedidos en la mañana; cada uno se asigna tres y dos respectivamente para no procesar el mismo pedido dos veces.

---

## Epica 13: Envíos y entregas

> Nota de alcance: no hay cálculo automático de tarifas por peso/ubicación ni integración con transportadoras. Cada vendedor define y opera su envío de forma personalizada.

### HU-ENV-01 — Configuración de la modalidad de envío de la tienda
Como vendedor, quiero elegir cómo manejo el envío en mi tienda para adaptarlo a mi operación real.

Descripción
El vendedor selecciona entre dos modalidades: (a) **envío con tarifas propias**, definiendo lugares y precios; o (b) **envío a convenir**, donde no se cobra envío en la plataforma y el comprador debe contactarlo para acordarlo. La modalidad se define a nivel de tienda y puede sobrescribirse por producto.

Criterios de aceptación
* Dado que selecciono la modalidad "tarifas propias", cuando la guardo, entonces el sistema me exige configurar al menos un lugar con su precio antes de activarla.
* Dado que selecciono la modalidad "a convenir", cuando la guardo, entonces mis productos muestran esa indicación y el checkout no cobra envío.
* Dado que cambio de modalidad, cuando guardo el cambio, entonces aplica a los pedidos nuevos y no altera los pedidos ya generados.
* Dado que defino una modalidad distinta para un producto específico, cuando un comprador lo agrega al carrito, entonces prevalece la modalidad del producto sobre la de la tienda.

Ejemplo
Una tienda de joyería define envío a convenir porque despacha por mensajería propia, mientras que una tienda de ropa define tarifas fijas por ciudad.

### HU-ENV-02 — Definición de lugares y precios de envío
Como vendedor, quiero definir yo mismo los lugares que atiendo y el precio de envío de cada uno para cobrar lo que realmente me cuesta.

Descripción
El vendedor crea una lista de lugares (ciudad, municipio, zona o el nombre que él defina) con un precio de envío asociado a cada uno. No hay cálculo automático: el precio es el que el vendedor escribe.

Criterios de aceptación
* Dado que agrego un lugar con su precio de envío, cuando lo guardo, entonces los compradores de ese lugar ven ese valor en el checkout.
* Dado que edito el precio de un lugar existente, cuando lo guardo, entonces los pedidos nuevos usan la tarifa actualizada y los pedidos ya generados conservan la tarifa con la que se crearon.
* Dado que elimino o desactivo un lugar, cuando lo hago, entonces los compradores de ese lugar pasan a ver la indicación de contactar al vendedor.
* Dado que un comprador está en un lugar que no configuré, cuando llega al checkout, entonces ve el mensaje de contactar al vendedor para acordar el envío.

Ejemplo
Una tienda de Popayán define envío de $8.000 dentro de la ciudad, $15.000 a Cali y $20.000 al resto del Cauca.

### HU-ENV-03 — Envío a convenir con contacto directo al vendedor
Como comprador, quiero saber cuándo el envío se acuerda directamente con el vendedor y cómo contactarlo para poder coordinar la entrega.

Descripción
Cuando el producto o la tienda tienen modalidad "a convenir", la ficha del producto, el checkout y el detalle del pedido muestran la indicación correspondiente junto con los datos de contacto públicos de la tienda (teléfono, WhatsApp, correo, redes).

Criterios de aceptación
* Dado que un producto tiene envío a convenir, cuando visito su ficha, entonces veo la leyenda de envío a convenir y los datos de contacto del vendedor.
* Dado que confirmo un pedido con envío a convenir, cuando reviso el resumen, entonces el total no incluye envío y se indica que debo coordinarlo con el vendedor.
* Dado que consulto el detalle de ese pedido más adelante, cuando lo abro, entonces sigo teniendo visibles los datos de contacto del vendedor.

Ejemplo
Un comprador de una vereda compra un producto con envío a convenir y escribe por WhatsApp a la tienda para acordar el valor y el punto de entrega.

### HU-ENV-04 — Promoción de envío gratis por lugar
Como vendedor, quiero configurar envío gratis, total o limitado a ciertos lugares, para usarlo como promoción.

Descripción
Promoción específica de envío que anula el valor configurado en HU-ENV-02 para los lugares seleccionados, con vigencia opcional y condiciones opcionales (por ejemplo, monto mínimo de compra).

Criterios de aceptación
* Dado que activo envío gratis para un lugar específico, cuando un comprador de ese lugar llega al checkout, entonces el envío aparece en cero y marcado como promoción.
* Dado que activo envío gratis con monto mínimo de compra, cuando el comprador no alcanza ese monto, entonces se le cobra la tarifa normal y se le indica cuánto le falta para el envío gratis.
* Dado que la promoción tiene fecha de fin, cuando esta se cumple, entonces los pedidos posteriores vuelven a cobrar la tarifa configurada.
* Dado que activo envío gratis para toda mi tienda, cuando cualquier comprador con lugar configurado llega al checkout, entonces no se le cobra envío.

Ejemplo
Una tienda ofrece envío gratis dentro de su ciudad durante diciembre para compras superiores a $150.000.

### HU-ENV-05 — Actualización manual del estado de envío y seguimiento
Como vendedor, quiero actualizar manualmente el estado del envío de cada pedido para que el comprador pueda seguirlo sin depender de una transportadora integrada.

Descripción
No hay integración con transportadoras ni número de guía automático. El vendedor cambia el estado del envío desde su panel (por ejemplo: preparando, despachado, en camino, entregado) y puede agregar una nota o referencia libre (número de guía externo, nombre del mensajero, hora estimada). El comprador solo consulta.

Criterios de aceptación
* Dado que actualizo el estado del envío de un pedido, cuando guardo el cambio, entonces el comprador ve el nuevo estado y recibe una notificación.
* Dado que agrego una nota o referencia de envío, cuando la guardo, entonces el comprador la ve en el detalle de su pedido.
* Dado que soy comprador, cuando consulto el seguimiento de mi pedido, entonces veo la línea de tiempo de estados con su fecha y hora, sin poder modificarla.
* Dado que un pedido no ha tenido actualizaciones de envío, cuando lo consulto, entonces veo el estado inicial sin error ni información falsa de tracking.

Ejemplo
Un vendedor marca el pedido como "despachado" y agrega la nota "entregado a mensajero, llega mañana en la tarde"; el comprador recibe la notificación y ve esa nota en su pedido.

### HU-ENV-06 — Gestión de devoluciones con reingreso a inventario
Como vendedor, quiero gestionar las devoluciones y que el stock se reintegre cuando corresponda para mantener mi inventario correcto.

Criterios de aceptación
* Dado que se aprueba la devolución de un pedido, cuando se completa el proceso, entonces el producto devuelto se reintegra al inventario del almacén correspondiente.
* Dado que la devolución no aplica reingreso (ej. producto dañado), cuando lo marco así, entonces el stock no se reintegra y queda registrado el motivo.
* Dado que se registra una devolución, cuando el comprador consulta su pedido, entonces ve el estado "devuelto" y el resultado del proceso.

Ejemplo
Un comprador devuelve una camisa que no le quedó bien; el vendedor la recibe en buen estado y el stock vuelve a estar disponible.

---

## Epica 14: Reputación y confianza

### HU-REP-01 — Envío de reseña por el comprador tras la compra
Como comprador, quiero calificar y reseñar el producto y el vendedor después de mi compra para compartir mi experiencia.

Descripción
Habilitado únicamente tras un pedido entregado. La reseña **no se publica de inmediato**: queda en estado pendiente de aprobación del vendedor (HU-REP-02).

Criterios de aceptación
* Dado que mi pedido está entregado, cuando accedo a él, entonces puedo calificar el producto y la tienda.
* Dado que envío mi reseña, cuando la confirmo, entonces el sistema me informa que quedará visible una vez el vendedor la revise.
* Dado que ya envié una reseña de ese pedido, cuando intento enviar otra, entonces el sistema no lo permite.
* Dado que mi pedido aún no está entregado, cuando intento reseñar, entonces el sistema no lo permite.

Ejemplo
Tras recibir su collar, un comprador escribe una reseña de 5 estrellas y ve el aviso de que será publicada tras la revisión de la tienda.

### HU-REP-02 — Aprobación o rechazo de reseñas por el vendedor
Como vendedor, quiero revisar las reseñas antes de que se publiquen para evitar que se muestren comentarios que violan las políticas.

Descripción
Toda reseña entra en estado `pendiente` y solo se hace pública cuando el vendedor la aprueba. **No hay plazo límite ni publicación automática**: una reseña puede permanecer pendiente de forma indefinida. Si el vendedor la rechaza, debe indicar el motivo y la reseña no se muestra en el catálogo, pero queda registrada para auditoría y revisión del administrador.

Criterios de aceptación
* Dado que un comprador envía una reseña, cuando entro a mi panel, entonces la veo en el listado de reseñas pendientes con su contenido y calificación.
* Dado que apruebo una reseña, cuando lo hago, entonces se publica en la ficha del producto y de la tienda, y se incluye en el promedio de calificación.
* Dado que rechazo una reseña indicando el motivo, cuando lo hago, entonces no se publica, no afecta el promedio de calificación y el comprador es notificado del rechazo.
* Dado que no reviso una reseña pendiente, cuando pasa el tiempo, entonces permanece pendiente indefinidamente sin publicarse por sí sola, y el panel me sigue mostrando el pendiente acumulado.
* Dado que rechacé una reseña, cuando el administrador la consulta, entonces puede verla junto con el motivo del rechazo.

Ejemplo
Un vendedor recibe una reseña con insultos hacia su equipo, la rechaza indicando "lenguaje ofensivo", y esta no se publica; otra reseña crítica pero respetuosa sobre demoras en el envío la aprueba y se publica.

### HU-REP-03 — Reporte de problemas o disputas
Como comprador, quiero reportar un problema con mi pedido para que la plataforma o el vendedor lo revisen.

Criterios de aceptación
* Dado que tengo un pedido con un problema, cuando lo reporto indicando el motivo, entonces se genera un caso de disputa asociado a ese pedido.
* Dado que reporto una disputa, cuando lo hago, entonces tanto el vendedor como el administrador pueden verla.

Ejemplo
Un comprador reporta que el producto llegó dañado y adjunta fotos como evidencia.

### HU-REP-04 — Supervisión de moderación de reseñas por el administrador
Como administrador de la plataforma, quiero supervisar las reseñas aprobadas y rechazadas por los vendedores para evitar que se oculten críticas legítimas o se publique contenido inapropiado.

Descripción
El administrador tiene visibilidad de todas las reseñas, incluidas las rechazadas por el vendedor y su motivo, y puede revertir decisiones o retirar reseñas ya publicadas.

Criterios de aceptación
* Dado que consulto las reseñas de una tienda, cuando lo hago, entonces veo las publicadas, las pendientes y las rechazadas con su motivo.
* Dado que identifico una reseña legítima rechazada sin justificación, cuando la restituyo, entonces se publica en la ficha del producto.
* Dado que una reseña publicada incumple las políticas, cuando la retiro, entonces deja de ser visible pero queda registrada para auditoría.

Ejemplo
El administrador detecta que una tienda rechaza sistemáticamente todas las reseñas de 1 y 2 estrellas y restituye las que eran legítimas.

---

## Epica 15: Panel del vendedor

### HU-VEN-01 — Dashboard de ventas e inventario
Como vendedor, quiero ver un dashboard consolidado de mis ventas e inventario para tener una visión rápida de mi negocio.

Criterios de aceptación
* Dado que entro a mi panel, cuando cargo el dashboard, entonces veo un resumen de ventas recientes y el estado general de mi inventario.
* Dado que tengo varios almacenes, cuando reviso el dashboard, entonces puedo ver el desglose por almacén además del consolidado.
* Dado que tengo pendientes operativos (comprobantes por revisar, reseñas por aprobar, pedidos sin despachar), cuando entro al dashboard, entonces los veo destacados.

Ejemplo
Un vendedor abre su panel y ve que tiene 3 comprobantes por revisar y 2 reseñas pendientes de aprobación.

### HU-VEN-02 — Ver ganancias (ingresos y costos)
Como vendedor, quiero ver mis ganancias reales descontando costos de materiales para conocer mi rentabilidad.

Descripción
Reporte de ganancias que resta del ingreso bruto el costo de materiales registrado. La comisión que la plataforma cobra al vendedor se gestiona por fuera (HU-ADM-03) y puede mostrarse como referencia informativa si el administrador la registró.

Criterios de aceptación
* Dado que selecciono un período, cuando genero el reporte, entonces veo ingresos, costos de materiales y la ganancia bruta resultante.
* Dado que un pedido incluye productos sin costo de materiales registrado, cuando genero el reporte, entonces el sistema señala esos productos como incompletos para el cálculo.
* Dado que el administrador registró un cobro de plataforma para el período, cuando reviso el reporte, entonces lo veo como referencia informativa, no como descuento automático.

Ejemplo
Un vendedor revisa que su ganancia bruta del mes, tras descontar materiales, fue de $1.400.000.

### HU-VEN-03 — Reportes de productos más vendidos y rotación de stock
Como vendedor, quiero ver cuáles son mis productos más vendidos y su rotación para tomar decisiones de reabastecimiento.

Criterios de aceptación
* Dado que selecciono un período, cuando genero el reporte, entonces veo el ranking de productos más vendidos de mi tienda.
* Dado que consulto la rotación de un producto, cuando lo hago, entonces veo qué tan rápido se está vendiendo respecto a su stock disponible.

Ejemplo
Un vendedor descubre que un modelo de zapato se agota cada dos semanas y aumenta la frecuencia de reabastecimiento.

---

## Epica 16: Panel de administración (plataforma)

### HU-ADM-01 — Creación de cuentas de vendedor y entrega de credenciales
Como administrador de la plataforma, quiero crear las cuentas de los vendedores y entregarles sus credenciales para controlar quién opera en la plataforma.

Descripción
El alta de vendedores es exclusiva del administrador. El administrador registra los datos del vendedor, genera la cuenta con contraseña temporal y la envía al correo del vendedor (o la entrega por el canal acordado). No existe autorregistro ni proceso de KYC autoservicio.

Criterios de aceptación
* Dado que registro los datos de un nuevo vendedor y confirmo la creación, cuando lo hago, entonces se genera su cuenta con contraseña temporal y se envía al correo registrado.
* Dado que el correo indicado ya pertenece a otra cuenta, cuando intento crear el vendedor, entonces el sistema rechaza la operación con un mensaje descriptivo.
* Dado que un vendedor perdió el acceso, cuando regenero sus credenciales, entonces la contraseña anterior queda invalidada y se le envía una nueva temporal.
* Dado que suspendo una cuenta de vendedor, cuando lo hago, entonces pierde acceso al panel de inmediato y su tienda deja de ser visible.

Ejemplo
El administrador cierra el acuerdo con una tienda de joyería, crea su cuenta desde el panel y le envía por correo el usuario y la contraseña temporal.

### HU-ADM-02 — Creación y configuración del perfil de tienda
Como administrador de la plataforma, quiero crear el perfil de la tienda de cada vendedor para que reciba su cuenta con todo listo para operar.

Descripción
El administrador crea la tienda con su nombre, identificación, datos fiscales/comerciales y configuración inicial, y la asocia a la cuenta del vendedor. El vendedor luego solo edita la información pública de contacto (HU-TDA-01).

Criterios de aceptación
* Dado que creo una tienda y la asocio a una cuenta de vendedor, cuando la guardo, entonces el vendedor encuentra su tienda ya creada al ingresar al panel.
* Dado que el nombre de tienda ya existe, cuando intento guardarlo, entonces el sistema lo rechaza.
* Dado que edito el nombre o los datos fiscales de una tienda, cuando guardo, entonces los cambios se reflejan en el catálogo público y en los comprobantes emitidos a partir de ese momento.
* Dado que desactivo una tienda, cuando lo hago, entonces deja de ser visible en el catálogo pero conserva su historial de pedidos.

Ejemplo
El administrador crea la tienda "Nova Ropa", carga su nombre legal y su identificación, y la asocia a la cuenta del dueño para que este solo tenga que subir productos.

### HU-ADM-03 — Registro manual del cobro de la plataforma al vendedor
Como administrador de la plataforma, quiero registrar manualmente lo que le cobramos a cada vendedor para llevar el control aunque el pago ocurra fuera de la plataforma.

Descripción
La plataforma **no procesa** el pago que el vendedor le hace a Morfeo. El administrador registra en un formulario el concepto, el período, el monto acordado y el estado del cobro (pendiente, pagado, vencido, condonado), con notas y fecha de pago. Es un registro administrativo, sin cálculo ni descuento automático sobre las ventas.

Criterios de aceptación
* Dado que registro un cobro con tienda, concepto, período, monto y estado, cuando lo guardo, entonces queda asociado a esa tienda en el histórico de cobros.
* Dado que el vendedor paga por fuera de la plataforma, cuando actualizo el registro a "pagado" con su fecha, entonces el histórico refleja ese cambio y conserva el estado anterior.
* Dado que un cobro registrado está pendiente y vencido, cuando consulto el listado, entonces aparece señalado como vencido.
* Dado que consulto una tienda, cuando abro su ficha, entonces veo todos sus cobros registrados con su estado.
* Dado que reviso el sistema, cuando busco un flujo de pago del vendedor a la plataforma, entonces no existe: la plataforma solo registra, no cobra.

Ejemplo
El administrador registra el cobro mensual de $220.000 a la tienda "Nova Ropa" por el paquete contratado en agosto y, cuando le confirman la transferencia, lo marca como pagado con la fecha correspondiente.

### HU-ADM-04 — Reporte de cobros a vendedores
Como administrador de la plataforma, quiero ver el consolidado de los cobros registrados a los vendedores para saber cuánto está pendiente y cuánto se ha recaudado.

Criterios de aceptación
* Dado que selecciono un período, cuando genero el reporte, entonces veo el total registrado, el total pagado y el total pendiente por tienda.
* Dado que filtro por estado, cuando aplico el filtro, entonces veo solo los cobros en ese estado.
* Dado que no hay cobros registrados en el período, cuando genero el reporte, entonces veo un estado vacío sin error.

Ejemplo
El administrador revisa a fin de mes que quedan tres tiendas con cobros pendientes y les hace seguimiento por fuera de la plataforma.

### HU-ADM-05 — Reportes globales de ventas e inventario
Como administrador de la plataforma, quiero ver reportes globales de todas las tiendas para monitorear la salud general de la plataforma.

Criterios de aceptación
* Dado que selecciono un período, cuando genero el reporte global, entonces veo el total de ventas de todas las tiendas.
* Dado que filtro por tienda o categoría, cuando lo hago, entonces los datos se ajustan al filtro.

Ejemplo
El administrador revisa el crecimiento mensual de ventas de toda la plataforma.

### HU-ADM-06 — Moderación de contenido y disputas
Como administrador de la plataforma, quiero moderar el contenido publicado y las disputas reportadas para mantener la calidad y la confianza de la plataforma.

Criterios de aceptación
* Dado que se reporta un producto por contenido inapropiado, cuando lo reviso, entonces puedo ocultarlo o solicitar su corrección al vendedor.
* Dado que reviso una disputa reportada por un comprador, cuando la resuelvo, entonces puedo dejar un registro visible para ambas partes.

Ejemplo
El administrador media en una disputa por un producto no entregado y documenta la resolución.

### HU-ADM-07 — Configuración de la pasarela de pago
Como administrador de la plataforma, quiero configurar la pasarela de pago automatizada a nivel de plataforma para habilitar los pagos en línea de todas las tiendas.

Criterios de aceptación
* Dado que configuro las credenciales de la pasarela, cuando las guardo, entonces las tiendas pueden habilitar ese método de pago para sus compradores.
* Dado que la pasarela reporta una falla de conexión, cuando esto ocurre, entonces el sistema deja de ofrecer ese método hasta que se resuelva.

Ejemplo
El administrador configura las credenciales de Mercado Pago para que las tiendas empiecen a recibir pagos por esa vía.

---

## Puntos abiertos pendientes de definir

Los seis puntos abiertos de la v2 quedaron cerrados (ver tabla "Cambios de la v3"). Quedan estas preguntas menores, derivadas de esas mismas decisiones:

1. **Pedidos pendientes indefinidos**: al no existir expiración automática, el stock de un pedido nunca pagado queda reservado hasta que el vendedor lo anule. Conviene definir si el panel muestra una alerta de pedidos pendientes antiguos para que el vendedor no pierda inventario reservado sin darse cuenta. Afecta HU-PED-04 y HU-VEN-01.
2. **Cargos extra y devoluciones**: si un pedido se devuelve parcialmente, definir si los cargos extra de valor fijo (empaque, manejo) se devuelven, se prorratean o se retienen. Afecta HU-PROM-04 y HU-ENV-06.
3. **Cargos extra en compras multi-tienda**: confirmar que cada pedido aplica únicamente los cargos de su propia tienda y que el comprador entiende el desglose por tienda en la vista unificada. Afecta HU-CHK-02 y HU-CHK-05.
4. **Registro de excedentes devueltos**: definir si el registro de la devolución acordada por fuera es solo una nota libre o un campo estructurado (monto devuelto, fecha, medio) para poder reportarlo después. Afecta HU-PAG-07.