# Epica 05 - Gestion de precios y promociones

Fuente funcional: `docs/Historias de usuario.md`, Epica 05.  
Alcance implementado: backend FastAPI para precio regular/especial, promociones, cupones, margen sobre precio efectivo y cargos extra desglosados en checkout.

## HU-PROM-01 - Precio regular y precios especiales

### Criterios cubiertos

- Cada variante conserva `price` como precio regular.
- El vendedor puede configurar `special_price`, `special_starts_at` y `special_ends_at`.
- El catalogo publico y carrito usan el precio especial solo si esta vigente.
- Las respuestas publicas exponen `regular_price`, `special_price`, `special_starts_at`, `special_ends_at` y `special_price_active`.
- El backend rechaza precio especial mayor al regular y ventanas de vigencia incoherentes.

### Endpoints

- `GET /api/v1/catalog/products`
- `GET /api/v1/catalog/products/{slug}`
- `GET /api/v1/seller/products`
- `POST /api/v1/seller/products`
- `POST /api/v1/seller/products/{product_id}/variants`
- `PATCH /api/v1/seller/variants/{variant_id}`
- `GET /api/v1/cart`
- `POST /api/v1/checkout/quote`
- `POST /api/v1/checkout`

### Tests

- `tests/test_hu_prom_pricing_promotions.py`
- `tests/test_prom_openapi_contract.py`

## HU-PROM-02 - Promociones y cupones

### Criterios cubiertos

- El vendedor crea, lista, actualiza y desactiva promociones de porcentaje, valor fijo y volumen.
- Las promociones tienen vigencia, estado activo y alcance `store` o `products`.
- Las promociones de volumen se aplican automaticamente en la cotizacion y checkout.
- El vendedor crea, lista, actualiza y desactiva cupones con codigo normalizado, vigencia y limite de usos.
- Un cupon vencido, inactivo, inexistente o sin usos disponibles se rechaza con `400`.
- Los descuentos se devuelven en desglose con origen `promotion` o `coupon`.

### Endpoints

- `GET /api/v1/seller/promotions`
- `POST /api/v1/seller/promotions`
- `PATCH /api/v1/seller/promotions/{promotion_id}`
- `DELETE /api/v1/seller/promotions/{promotion_id}`
- `GET /api/v1/seller/coupons`
- `POST /api/v1/seller/coupons`
- `PATCH /api/v1/seller/coupons/{coupon_id}`
- `DELETE /api/v1/seller/coupons/{coupon_id}`
- `POST /api/v1/checkout/quote`
- `POST /api/v1/checkout`

### Tests

- `tests/test_hu_prom_pricing_promotions.py`
- `tests/test_prom_openapi_contract.py`

## HU-PROM-03 - Margen automatico

### Criterios cubiertos

- El margen seller se calcula con el precio efectivo vigente.
- El catalogo publico no expone costo, margen ni porcentaje de margen.
- Si falta `cost`, el backend devuelve `margin=null`, `margin_pct=null` y `margin_missing_cost=true`.
- Al actualizar precio regular, precio especial o costo, la respuesta seller refleja el margen recalculado.

### Endpoints

- `GET /api/v1/seller/products`
- `POST /api/v1/seller/products`
- `PATCH /api/v1/seller/variants/{variant_id}`
- `GET /api/v1/catalog/products/{slug}`

### Tests

- `tests/test_hu_prom_pricing_promotions.py`
- `tests/test_hu_prod_05_cost_margin.py`
- `tests/test_prom_openapi_contract.py`

## HU-PROM-04 - Cargos extra manuales

### Criterios cubiertos

- El vendedor crea cargos extra con nombre visible, tipo `fixed` o `percent`, valor, estado y alcance.
- El checkout muestra cargos extra como lineas separadas y suma `extra_charge_total`.
- Los cargos desactivados dejan de aplicar a pedidos nuevos.
- Los pedidos guardan ajustes historicos en `order_adjustments`, por lo que editar o desactivar cargos no cambia pedidos ya creados.
- El backend valida porcentajes entre 1 y 100 y productos pertenecientes a la tienda cuando el alcance es `products`.

### Endpoints

- `GET /api/v1/seller/extra-charges`
- `POST /api/v1/seller/extra-charges`
- `PATCH /api/v1/seller/extra-charges/{charge_id}`
- `DELETE /api/v1/seller/extra-charges/{charge_id}`
- `POST /api/v1/checkout/quote`
- `POST /api/v1/checkout`
- `GET /api/v1/orders/{order_id}`

### Tests

- `tests/test_hu_prom_pricing_promotions.py`
- `tests/test_prom_openapi_contract.py`

## Modelos y persistencia

- `product_variants`: campos `special_price`, `special_starts_at`, `special_ends_at`.
- `promotions`: campos de vigencia, alcance, productos y volumen `pay_quantity`.
- `coupons`: campos de vigencia, usos, alcance y productos.
- `extra_charges`: configuracion de cargos extra para pedidos nuevos.
- `order_adjustments`: snapshot historico de descuentos y cargos aplicados a cada pedido.
- Migracion: `alembic/versions/0009_pricing_promotions.py`.

## Swagger y contrato API

Los endpoints de esta epica incluyen:

- `summary`
- `description` con referencia HU-PROM-01 a HU-PROM-04
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

- Mostrar `price` como precio efectivo y `regular_price` como precio tachado cuando `special_price_active=true`.
- En checkout, pintar `discounts` y `extra_charges` como lineas separadas antes del total.
- Para cupones rechazados, mostrar el mensaje de `400` y permitir ingresar otro codigo.
- En panel seller, si `margin_missing_cost=true`, pedir costo antes de mostrar una utilidad calculada.
- Desactivar promociones, cupones o cargos extra debe tratarse como baja logica.
