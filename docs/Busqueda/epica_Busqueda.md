# Epica 08: Busqueda y navegacion (comprador)

**Epica ID:** 08
**Modulo / prefijo HU:** BUS
**Swagger tag:** `catalog`
**Prefijo de rutas:** `/api/v1/catalog`
**Autenticacion:** endpoints publicos, sin `Authorization`
**Scope:** catalogo publico de tiendas activas
**Ultima actualizacion:** 2026-08-05

---

## Resumen del modulo

Esta epica permite que compradores busquen y naveguen productos visibles del catalogo, combinen filtros por categoria, precio y disponibilidad, ordenen por precio o ventas reales, y consulten una ficha publica con variantes, stock, imagenes, envio y contacto de tienda.

---

## Indice de HUs implementadas

| HU | Titulo | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-BUS-01 | Buscador de productos con filtros | 2026-08-05 | `GET /api/v1/catalog/products` | `tests/test_hu_bus_01_product_search_filters.py` |
| HU-BUS-02 | Ordenamiento de resultados de busqueda | 2026-08-05 | `GET /api/v1/catalog/products` | `tests/test_hu_bus_02_search_sorting.py` |
| HU-BUS-03 | Pagina de detalle de producto con seleccion de variantes | 2026-08-05 | `GET /api/v1/catalog/products/{slug}` | `tests/test_hu_bus_03_product_detail_variants.py` |

---

## HU-BUS-01 - Buscador de productos con filtros

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_bus_01_product_search_filters.py`

### Descripcion funcional

El comprador puede consultar el catalogo publico usando un termino de busqueda y filtros combinables. La busqueda compara sin distinguir mayusculas/minusculas contra nombre, resumen y descripcion. Los filtros de categoria, tienda, precio efectivo y disponibilidad se aplican simultaneamente. Si no hay coincidencias, el endpoint responde con estado vacio sin error.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | El termino de busqueda muestra productos cuyo nombre o descripcion coinciden. | Si | `q` filtra por `Product.name`, `Product.short_desc` y `Product.description` con `lower(...).like(...)`. |
| 2 | El rango de precio limita resultados. | Si | `min_price` y `max_price` se aplican sobre `ProductOut.price`, calculado desde el precio efectivo visible. |
| 3 | Filtros combinados cumplen todos los filtros simultaneamente. | Si | `store_id`, `category`, `q`, precio e `in_stock` se aplican con logica AND antes de devolver la pagina. |
| 4 | Sin resultados muestra estado vacio sin error. | Si | El endpoint retorna `200`, `total=0` e `items=[]`. |

### Flujo implementado

```text
1. Frontend llama GET /api/v1/catalog/products con query params opcionales.
2. Backend filtra tiendas activas y productos visibles active/out_of_stock.
3. Aplica q, store_id y category en consulta base.
4. Convierte candidatos a ProductOut para calcular precio efectivo y stock real.
5. Aplica rango de precio e in_stock.
6. Ordena y pagina.
7. Retorna ProductListOut.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/catalog/products` -> 200

**Descripcion:** Busca productos visibles para compradores.
**Roles permitidos:** publico
**Archivo:** `app/modules/catalog/router.py`

**Query params:**
| Param | Tipo | Req/Opt | Descripcion |
|---|---|---|---|
| `q` | `string` | opcional | Termino sobre nombre, resumen o descripcion. |
| `category` | `string` | opcional | Slug de categoria activa. |
| `store_id` | `string` | opcional | Tienda activa a consultar. |
| `min_price` | `int` | opcional | Precio efectivo minimo en COP. |
| `max_price` | `int` | opcional | Precio efectivo maximo en COP. |
| `in_stock` | `bool` | opcional | Solo productos con disponibilidad real. |
| `page` | `int` | opcional | Pagina, default `1`. |
| `page_size` | `int` | opcional | Tamano de pagina, default `24`. |

**Response exitosa:**
```json
{
  "total": 1,
  "page": 1,
  "page_size": 24,
  "items": [
    {
      "id": "prod-camisa",
      "slug": "camisa-blanca",
      "name": "Camisa Blanca",
      "price": 70000,
      "stock": 5,
      "variants": []
    }
  ]
}
```

**Errores posibles:**
| Codigo | Situacion | Mensaje tipico |
|---|---|---|
| 400 | Rango de precio incoherente | `"min_price no puede ser mayor que max_price"` |
| 422 | Parametro invalido | Array `detail` de FastAPI |

### Tests de esta HU

- Archivo: `tests/test_hu_bus_01_product_search_filters.py`
- Cubre: busqueda por nombre/descripcion, case-insensitive, filtros combinados, precio efectivo, disponibilidad, estado vacio y rango invalido.
- Ejecucion: `pytest tests/test_hu_bus_01_product_search_filters.py -v`

### Notas y advertencias para frontend

- `items=[]` con `total=0` es estado vacio normal.
- El filtro de precio usa el precio efectivo mostrado al comprador, no el precio regular.
- `in_stock=true` filtra por disponibilidad real agregada.

---

## HU-BUS-02 - Ordenamiento de resultados de busqueda

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_bus_02_search_sorting.py`

### Descripcion funcional

El comprador puede ordenar resultados por precio ascendente, precio descendente, destacados/nuevos/relevancia y mas vendidos. El orden `vendidos` usa unidades reales vendidas en pedidos no cancelados.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Precio menor a mayor reordena resultados. | Si | `sort=precio-asc` ordena por `ProductOut.price` ascendente. |
| 2 | Mas vendidos ordena por volumen de ventas. | Si | `sort=vendidos` suma `OrderItem.quantity` por producto y excluye `OrderStatus.cancelled`. |

### Flujo implementado

```text
1. Backend obtiene productos filtrados.
2. Calcula ProductOut para usar precio efectivo.
3. Si sort=precio-asc o precio-desc, ordena por precio efectivo.
4. Si sort=vendidos, calcula unidades vendidas por producto en pedidos no cancelados.
5. Aplica paginacion sobre la lista ordenada.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/catalog/products` -> 200

**Query params relevantes:**
| Param | Tipo | Req/Opt | Descripcion |
|---|---|---|---|
| `sort` | `string` | opcional | `relevancia`, `destacados`, `nuevos`, `precio-asc`, `precio-desc`, `vendidos`. |

**Errores posibles:**
| Codigo | Situacion | Mensaje tipico |
|---|---|---|
| 422 | `sort` no permitido | Array `detail` de FastAPI |

### Tests de esta HU

- Archivo: `tests/test_hu_bus_02_search_sorting.py`
- Cubre: `precio-asc`, `precio-desc`, `vendidos` y exclusion de pedidos cancelados.
- Ejecucion: `pytest tests/test_hu_bus_02_search_sorting.py -v`

### Notas y advertencias para frontend

- `vendidos` cuenta unidades, no cantidad de pedidos.
- Pedidos cancelados no suman.
- `relevancia` se acepta como valor publico y se comporta como orden destacado/relevante.

---

## HU-BUS-03 - Pagina de detalle de producto con seleccion de variantes

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_bus_03_product_detail_variants.py`

### Descripcion funcional

La ficha publica del producto muestra variantes activas con precio efectivo, precio regular, stock disponible, disponibilidad e imagenes por variante. Tambien expone datos de envio y contacto de la tienda para que frontend muestre envio a convenir cuando corresponda. Productos `draft` y `discontinued` se ocultan; `out_of_stock` se puede consultar, pero sus variantes no quedan disponibles para compra directa.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Al seleccionar variante se ve precio, stock e imagenes. | Si | `VariantPublicOut` incluye `price`, `regular_price`, `stock`, `available` e `images`. |
| 2 | Variante sin stock deshabilita agregar al carrito. | Si | La variante sin disponibilidad retorna `available=false` y `stock=0`. |
| 3 | Producto con envio a convenir muestra indicacion y contacto. | Si | `ProductOut.shipping.to_agree` y `ProductOut.store_contact` se exponen en detalle. |

### Flujo implementado

```text
1. Frontend llama GET /api/v1/catalog/products/{slug}.
2. Backend valida que la tienda este activa y el producto sea visible.
3. Construye ProductOut con variantes activas e imagenes.
4. Calcula stock/disponibilidad por variante.
5. Agrega datos publicos de contacto y configuracion de envio.
6. Retorna detalle publico sin costos internos.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/catalog/products/{slug}` -> 200

**Descripcion:** Consulta ficha publica de producto.
**Roles permitidos:** publico
**Archivo:** `app/modules/catalog/router.py`

**Path params / Query params:**
| Param | Tipo | Req/Opt | Descripcion |
|---|---|---|---|
| `slug` | `string` | requerido | Slug del producto. |
| `store_id` | `string` | opcional | Tienda activa para resolver slugs repetidos. |

**Response exitosa:**
```json
{
  "id": "prod-camisa",
  "slug": "camisa-blanca",
  "variants": [
    {
      "id": "variant-azul",
      "price": 80000,
      "stock": 3,
      "available": true,
      "images": []
    }
  ],
  "store_contact": {
    "email": "hola@tienda.example",
    "phone": "+573001112233",
    "whatsapp_phone": "+573009998888"
  },
  "shipping": {
    "flat_cost": 0,
    "free_threshold": 0,
    "zones": [],
    "to_agree": true
  }
}
```

**Errores posibles:**
| Codigo | Situacion | Mensaje tipico |
|---|---|---|
| 404 | Producto no visible o inexistente | `"Producto no encontrado"` |
| 422 | Parametro invalido | Array `detail` de FastAPI |

### Tests de esta HU

- Archivo: `tests/test_hu_bus_03_product_detail_variants.py`
- Cubre: precio/stock/imagenes por variante, variante sin stock, producto `out_of_stock`, ocultamiento `draft`/`discontinued`, envio y contacto.
- Ejecucion: `pytest tests/test_hu_bus_03_product_detail_variants.py -v`

### Notas y advertencias para frontend

- Usar `variant.available` para habilitar/deshabilitar agregar al carrito.
- `shipping.to_agree=true` indica mostrar contacto del vendedor.
- Los costos internos nunca se exponen en `ProductOut` publico.

---

## Tests y contrato OpenAPI de cierre

- Tests HU: `tests/test_hu_bus_01_product_search_filters.py`, `tests/test_hu_bus_02_search_sorting.py`, `tests/test_hu_bus_03_product_detail_variants.py`
- Contrato OpenAPI: `tests/test_bus_openapi_contract.py`
- Ejecucion focalizada: `pytest tests -v -k "hu_bus or bus_openapi"`
