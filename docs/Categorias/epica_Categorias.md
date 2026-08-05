# Epica 03 - Gestion de categorias y catalogo

Fuente funcional: `docs/Historias de usuario.md`, Epica 03.  
Alcance implementado: backend FastAPI para categorias propias por tienda y asignacion multiple de productos a categorias.

## HU-CAT-01 - Creacion de categorias y subcategorias propias de la tienda

### Criterios cubiertos

- El vendedor crea categorias raiz propias de su tienda.
- El vendedor crea subcategorias usando `parent_id` de una categoria de la misma tienda.
- El catalogo publico, al navegar con `store_id`, muestra solo categorias activas definidas por esa tienda.
- El backend rechaza `parent_id` de otra tienda con `400`.
- El backend rechaza slug duplicado dentro de la misma tienda con `409`.
- El backend rechaza autociclos y ciclos de jerarquia al actualizar categorias con `400`.
- La eliminacion de categoria es baja logica (`active=false`) y la oculta del catalogo publico.

### Endpoints

- `GET /api/v1/catalog/categories?store_id={store_id}`
- `GET /api/v1/seller/categories`
- `POST /api/v1/seller/categories`
- `PATCH /api/v1/seller/categories/{category_id}`
- `DELETE /api/v1/seller/categories/{category_id}`

### Validaciones backend

- `store_id` de categoria siempre se deriva de la tienda autenticada del seller.
- `parent_id` debe ser `null` o pertenecer a la misma tienda.
- En `PATCH`, `parent_id` no puede ser la misma categoria ni un descendiente.
- `slug` se normaliza con la misma regla del catalogo y debe ser unico por tienda.
- Las categorias inactivas no aparecen en el catalogo publico.

### Tests

- `tests/test_hu_cat_01_categories.py`
- `tests/test_cat_openapi_contract.py`

## HU-CAT-02 - Asignacion de un producto a multiples categorias

### Criterios cubiertos

- Un producto puede crearse con dos o mas categorias/subcategorias de la misma tienda.
- El producto aparece al filtrar el catalogo publico por cualquiera de sus categorias asignadas.
- Al actualizar `category_ids`, el backend reemplaza las asociaciones del producto.
- Al remover una categoria, el producto deja de aparecer al navegar esa categoria y sigue apareciendo en las que conserva.
- El backend rechaza categorias duplicadas, ajenas a la tienda o inactivas con `400`.

### Endpoints

- `POST /api/v1/seller/products`
- `PATCH /api/v1/seller/products/{product_id}`
- `GET /api/v1/catalog/products?store_id={store_id}&category={slug}`

### Validaciones backend

- `category_ids` no puede contener ids duplicados.
- Cada categoria asignada debe estar activa y pertenecer a la tienda autenticada.
- La lista enviada en `PATCH` reemplaza la asignacion completa del producto.
- El filtro publico por categoria usa `category` como slug. Para navegacion de una tienda, frontend debe enviar tambien `store_id`.

### Tests

- `tests/test_hu_cat_02_product_categories.py`
- `tests/test_cat_openapi_contract.py`

## Swagger y contrato API

Los endpoints tocados incluyen:

- `summary`
- `description` con referencia HU-CAT-01 o HU-CAT-02
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

- Para armar la jerarquia visual, usar `parent_id` del listado de categorias.
- Para catalogo publico de tienda, consultar categorias con `store_id`.
- Para navegar productos por categoria, usar `GET /api/v1/catalog/products?store_id={store_id}&category={slug}`.
- Para editar categorias de producto, enviar `category_ids` completo; el backend reemplaza la asignacion anterior.
