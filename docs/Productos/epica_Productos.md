# Epica 04 - Gestion de productos

Fuente funcional: `docs/Historias de usuario.md`, Epica 04.  
Alcance implementado: backend FastAPI para alta, edicion, variantes, carga masiva, imagenes, costos internos, margen y estados de productos.

## HU-PROD-01 - Alta y edicion de productos

### Criterios cubiertos

- El vendedor crea productos propios de su tienda.
- El vendedor edita nombre, slug, descripcion, resumen, estado y categorias.
- El slug del producto es unico por tienda y duplicados retornan `409`.
- La baja de producto es logica y cambia el estado a `discontinued`.
- Los endpoints seller solo operan sobre productos de la tienda autenticada.
- El catalogo publico refleja productos `active` y oculta `draft`/`discontinued`.

### Endpoints

- `GET /api/v1/seller/products`
- `POST /api/v1/seller/products`
- `PATCH /api/v1/seller/products/{product_id}`
- `DELETE /api/v1/seller/products/{product_id}`
- `GET /api/v1/catalog/products`
- `GET /api/v1/catalog/products/{slug}`

### Tests

- `tests/test_hu_prod_01_products_crud.py`
- `tests/test_prod_openapi_contract.py`

## HU-PROD-02 - Gestion de variantes

### Criterios cubiertos

- Un producto puede tener multiples variantes con SKU, nombre, talla, color, precio y costo.
- El SKU de variante es unico dentro de la tienda y duplicados retornan `409`.
- El vendedor puede crear, editar y desactivar variantes.
- Las respuestas publicas exponen precio, stock y disponibilidad por variante.
- Las respuestas publicas no exponen costo interno ni margen.
- Los endpoints seller validan scope de tienda.

### Endpoints

- `POST /api/v1/seller/products/{product_id}/variants`
- `PATCH /api/v1/seller/variants/{variant_id}`
- `DELETE /api/v1/seller/variants/{variant_id}`
- `GET /api/v1/catalog/products/{slug}`

### Tests

- `tests/test_hu_prod_02_variants.py`
- `tests/test_prod_openapi_contract.py`

## HU-PROD-03 - Carga masiva

### Criterios cubiertos

- El vendedor descarga una plantilla CSV de ejemplo.
- El vendedor carga productos desde archivo CSV o XLSX.
- La carga acepta columnas `name`, `slug`, `description`, `short_desc`, `category_slug`, `sku`, `price`, `cost`, `stock`, `status` e `image_url`.
- `name`, `sku` y `price` son obligatorios.
- Las filas validas se crean aunque otras filas fallen.
- La respuesta informa `created_count`, `error_count`, productos creados y errores por fila.
- El stock inicial se registra en el almacen activo por defecto de la tienda.

### Endpoints

- `GET /api/v1/seller/products/import/template`
- `POST /api/v1/seller/products/import`

### Tests

- `tests/test_hu_prod_03_import.py`
- `tests/test_prod_openapi_contract.py`

## HU-PROD-04 - Imagenes multiples por producto y variante

### Criterios cubiertos

- Un producto puede tener galeria general.
- Una variante puede tener imagenes propias mediante `variant_id`.
- El backend valida que la imagen asociada a una variante pertenezca al mismo producto.
- El vendedor puede crear, editar y eliminar imagenes.
- El detalle publico separa imagenes generales del producto e imagenes de cada variante.

### Endpoints

- `POST /api/v1/seller/products/{product_id}/images`
- `PATCH /api/v1/seller/products/{product_id}/images/{image_id}`
- `DELETE /api/v1/seller/products/{product_id}/images/{image_id}`
- `GET /api/v1/catalog/products/{slug}`

### Tests

- `tests/test_hu_prod_04_images.py`
- `tests/test_prod_openapi_contract.py`

## HU-PROD-05 - Costo interno y margen

### Criterios cubiertos

- `ProductVariant.cost` representa el costo interno de materiales/produccion.
- Las respuestas seller incluyen `cost`, `margin` y `margin_pct` por variante.
- El margen se recalcula al actualizar precio o costo.
- El catalogo publico nunca incluye `cost`, `margin`, `margin_pct` ni `unit_cost`.

### Endpoints

- `GET /api/v1/seller/products`
- `POST /api/v1/seller/products`
- `PATCH /api/v1/seller/variants/{variant_id}`
- `GET /api/v1/catalog/products/{slug}`

### Tests

- `tests/test_hu_prod_05_cost_margin.py`
- `tests/test_prod_openapi_contract.py`

## HU-PROD-06 - Estados del producto

### Criterios cubiertos

- `draft` queda oculto del catalogo publico.
- `active` queda visible y comprable si hay stock suficiente.
- `out_of_stock` queda visible, pero no es comprable.
- `discontinued` queda oculto y no es comprable.
- El carrito rechaza variantes inactivas, sin stock suficiente o pertenecientes a productos no comprables.

### Endpoints

- `GET /api/v1/catalog/products`
- `GET /api/v1/catalog/products/{slug}`
- `POST /api/v1/cart/items`
- `GET /api/v1/seller/products`

### Tests

- `tests/test_hu_prod_06_product_status.py`
- `tests/test_prod_openapi_contract.py`

## Swagger y contrato API

Los endpoints de productos, variantes, imagenes e importacion incluyen:

- `summary`
- `description` con referencia HU-PROD-01 a HU-PROD-06
- `response_description`
- `response_model`
- `status_code`
- `responses` para errores funcionales y validacion
- Schemas con descripciones y ejemplos

La referencia tecnica exportada se sincroniza con:

```powershell
C:\Users\Personal\Documents\GitHub\Singular\sesingular-backend\.venv\Scripts\python.exe -c "from pathlib import Path; import scripts.sync_docs as s; s.DEST_JSON=[s.API_ROOT / 'docs' / 'openapi.json']; s.DEST_MD=[s.API_ROOT / 'docs' / 'API_REFERENCE.md']; s.main()"
```

## Notas para frontend

- Usar endpoints publicos para catalogo y detalle; estos no exponen costo ni margen.
- Usar endpoints seller para administracion, costo interno y margen.
- Para carga masiva, enviar `multipart/form-data` con el campo `file`.
- Para imagenes de variante, enviar `variant_id`; para galeria general, omitirlo o enviarlo como `null`.
- En el carrito, tratar `409` como producto no comprable, agotado o stock insuficiente.
