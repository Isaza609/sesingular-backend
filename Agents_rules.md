# Reglas del agente — Singular Backend

Backend FastAPI del marketplace Singular (productos físicos).
Fuente de verdad funcional: `docs/Historias de usuario.md` (cada título `Epica:` define una épica y sus HUs).
Fuente de verdad técnica de la API: Swagger (`/docs`) — lo que está en el código es lo que se exporta con `sync_docs.py`.
Documentación siempre en español.
NO TOCAR SESINGULAR FRONTEND, TODO DESARROLLO VA A EN EL BACKEND

---

## Estructura estándar

`app/modules/{modulo}/` con `router.py`, `service.py`, `schemas.py` (y `models` en `app/models/` cuando aplique).
Separación de capas: todo módulo nuevo sigue model → schemas → service → router.

### Registro

- Registrar routers nuevos en `app/main.py`.
- Operaciones de escritura relevantes deben dejar trazabilidad cuando el dominio lo exija (p. ej. movimientos de inventario, cambios de estado de pedido/pago).

---

## Terminal y entorno virtual

- La terminal siempre opera dentro del entorno virtual.
- Verificar que esté activo antes de ejecutar cualquier comando.
- Para activarlo: `.venv\Scripts\activate` (Windows).
- Ejecutar comandos desde la raíz de `sesingular-backend/`.

---

## Seguridad y scope

- Autenticación: `Authorization: Bearer <JWT Supabase>`.
- Roles: `buyer`, `seller`, `admin`.
- Nunca exponer datos fuera del scope del usuario autenticado:
  - comprador → solo lo suyo;
  - vendedor / equipo → solo recursos de su tienda;
  - admin → alcance de plataforma.
- Siempre validar rol y pertenencia a la tienda (o recurso) antes de leer o escribir.
- Usar `app/modules/auth/deps.py` y `app/modules/common/permissions.py`.

---

## Estándares de documentación Swagger en código

Todo endpoint nuevo debe cumplir estos estándares sin excepción.
El Swagger (`/docs`) es la fuente de verdad técnica — lo que está en el código es lo que se exporta.
Ambos deben estar siempre sincronizados.

### Checklist por endpoint

Antes de ejecutar `sync_docs.py`, verificar que cada endpoint cumple:

- [ ] `summary` en una línea, verbo en infinitivo ("Crear producto", "Listar pedidos")
- [ ] `description` con rol permitido, HU relacionada (`HU-XXX-NN`) y comportamiento especial
- [ ] `response_description` describiendo qué retorna en éxito
- [ ] `response_model` tipado en el decorador
- [ ] `status_code` explícito
- [ ] `responses` con todos los códigos de error posibles (400, 401, 403, 404, 409, 422, 502 según aplique)
- [ ] Schema de request con `Field(description=..., example=...)` en cada campo
- [ ] Schema de response con `Field(description=..., example=...)` en cada campo
- [ ] `model_config` con `json_schema_extra.example` completo y realista en el schema de request

---

## Documentación de épica — Registro acumulativo

### Propósito

El documento de épica es el único registro técnico y funcional de todo lo que se desarrolló en esa épica. Cumple dos funciones a la vez:

- **Registro funcional:** qué se implementó, cuándo, cómo se cumplieron los criterios de aceptación.
- **Contrato de API:** descripción completa de endpoints para que frontend los integre sin necesidad de abrir el Swagger.

No es un documento puntual. Es un historial vivo que crece con cada HU implementada. No se elimina ni se reescribe — solo se agrega al final.

### Ubicación y nombre

Dentro de `docs/` se crea **una carpeta por épica**. Dentro, un único archivo de documentación completa:

```
docs/{Epica}/epica_{Epica}.md
```

Mapeo (título en `Historias de usuario.md` → carpeta):

| Epica (en HU) | Carpeta / archivo |
| --- | --- |
| Epica 01: Gestión de usuarios | `docs/Usuarios/epica_Usuarios.md` |
| Epica 02: Gestión de tiendas (vendedores) | `docs/Tiendas/epica_Tiendas.md` |
| Epica 03: Gestión de categorías y catálogo | `docs/Categorias/epica_Categorias.md` |
| Epica 04: Gestión de productos | `docs/Productos/epica_Productos.md` |
| Epica 05: Gestión de precios y promociones | `docs/PreciosPromociones/epica_PreciosPromociones.md` |
| Epica 06: Gestión de inventario | `docs/Inventario/epica_Inventario.md` |
| Epica 07: Canal de venta (online / presencial) | `docs/CanalVenta/epica_CanalVenta.md` |
| Epica 08: Búsqueda y navegación (comprador) | `docs/Busqueda/epica_Busqueda.md` |
| Epica 09: Carrito y checkout | `docs/CarritoCheckout/epica_CarritoCheckout.md` |
| Epica 10: Pagos | `docs/Pagos/epica_Pagos.md` |
| Epica 11: Facturación al comprador | `docs/Facturacion/epica_Facturacion.md` |
| Epica 12: Gestión de pedidos | `docs/Pedidos/epica_Pedidos.md` |
| Epica 13: Envíos y entregas | `docs/Envios/epica_Envios.md` |
| Epica 14: Reputación y confianza | `docs/Reputacion/epica_Reputacion.md` |
| Epica 15: Panel del vendedor | `docs/PanelVendedor/epica_PanelVendedor.md` |
| Epica 16: Panel de administración (plataforma) | `docs/PanelAdmin/epica_PanelAdmin.md` |

Un solo archivo por épica. Nunca crear un archivo por HU ni por sprint.
Si la carpeta no existe, crearla al documentar la primera HU de esa épica.

### Cuándo actualizar

Cada vez que se implementa una HU, agregar su bloque al final del documento y actualizar el índice.
No reescribir secciones anteriores salvo que una HU posterior corrija explícitamente algo anterior
(en ese caso anotar la corrección con fecha, no borrar el registro original).

### Validación por HU

Antes y al cerrar una implementación:

1. Ubicar la **Epica** y la HU en `docs/Historias de usuario.md`.
2. Cumplir **todos** los criterios de aceptación de esa HU.
3. Documentar en el archivo de la épica cómo se cumplió cada criterio (tabla del bloque HU).
4. Referenciar la HU (`HU-XXX-NN`) en la `description` de cada endpoint tocado.
5. No marcar la HU como implementada si falta un criterio o se inventó comportamiento no documentado.

### Estructura del documento de épica

````markdown
# Epica {NN}: {Nombre}

**Épica ID:** {ej. 10}
**Módulo / prefijo HU:** {ej. PAG}
**Swagger tag:** `{Tag}`
**Prefijo de rutas:** `/api/v1/{ruta}`
**Autenticación:** `Authorization: Bearer <JWT Supabase>` (según endpoint; indicar si es público)
**Scope:** comprador / tienda del vendedor / plataforma (admin)
**Última actualización:** {fecha}

---

## Resumen del módulo

Descripción general de qué resuelve esta épica, qué entidades maneja
y qué roles intervienen.

---

## Índice de HUs implementadas

| HU | Título | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-PAG-01 | Selección del método de pago | 2026-08-05 | `GET /api/v1/...` | `tests/test_pag_01.py` |

---

<!-- Repetir este bloque por cada HU implementada, agregando al final -->

## HU-{ID} · {Título}

**Fecha de implementación:** {fecha}
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/...` (obligatorio)

### Descripción funcional

Qué resuelve esta HU desde el punto de vista del usuario o del sistema.
Contexto de negocio relevante para entender los endpoints.

### Criterios de aceptación

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | {criterio tomado de la HU} | ✅ | {explicación técnica de cómo lo cumple la implementación} |
| 2 | {criterio} | ✅ | {explicación} |

### Flujo implementado

Descripción del flujo completo en orden de ejecución.
Si involucra varios endpoints o servicios externos (pasarela, correo, storage), describirlo paso a paso.

```
1. Frontend llama POST /api/v1/... con body {…}
2. Service valida rol y scope (tienda / comprador)
3. Se persiste en marketplace.{tabla}
4. Efectos colaterales (reserva de stock, notificación, etc.)
5. Retorna el objeto creado con su ID
```

### Endpoints implementados en esta HU

<!-- Repetir por cada endpoint de la HU -->

#### {MÉTODO} `/api/v1/{ruta}` → {código HTTP exitoso}

**Descripción:** Qué hace, para qué rol aplica, comportamiento especial.
**Roles permitidos:** `buyer`, `seller`, `admin` (los que apliquen)
**Archivo:** `app/modules/{modulo}/router.py`

**Headers requeridos:**
| Header | Valor |
|---|---|
| `Authorization` | `Bearer <JWT>` |

**Path params / Query params:** *(omitir si no aplica)*
| Param | Tipo | Req/Opt | Descripción |
|---|---|---|---|
| `page` | `int` | opcional | Página (default: 1) |
| `limit` | `int` | opcional | Resultados por página (default: 20) |

**Request body:** *(omitir si no aplica)*
```json
{
  "campo": "ejemplo realista del dominio"
}
```

| Campo | Tipo | Req/Opt | Descripción |
|---|---|---|---|
| `campo` | `string` | requerido | Descripción del campo |

**Response exitosa:**
```json
{
  "id": "...",
  "campo": "valor"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` / `uuid` | Identificador |
| `campo` | `string` | Descripción |

**Errores posibles:**
| Código | Situación | Mensaje típico |
|---|---|---|
| 400 | Datos inválidos o regla de negocio violada | `"…"` |
| 401 | Sin autenticación | `"Token inválido o expirado"` |
| 403 | Rol o tienda no permitidos | `"…"` |
| 404 | Recurso no encontrado | `"…"` |
| 409 | Conflicto | `"…"` |
| 422 | Validación Pydantic | Array `detail` estándar de FastAPI |

### Tests de esta HU

- Archivo(s): `tests/...`
- Qué cubren: criterios / endpoints / casos de error relevantes.
- Cómo ejecutarlos: `pytest tests/... -v`

### Notas y advertencias para frontend

Lista de aspectos críticos que frontend debe conocer para esta HU:
- Enums aceptados, formatos de fecha, tipos de ID.
- Comportamientos condicionales o efectos secundarios.
- Campos que solo aplican según rol o modalidad (pago manual, envío a convenir, etc.).

---
<!-- fin del bloque HU — agregar el siguiente al final del archivo -->
````

---

## Tests obligatorios por HU / épica

Toda HU o épica desarrollada **debe** incluir tests. No se cierra la tarea sin ellos.

- Ubicación: `tests/` (pytest).
- Nombrar de forma trazable a la HU cuando sea posible (`test_hu_pag_01_...`, o módulo claro + comentario/docstring con la HU).
- Cubrir al menos:
  - camino feliz de los endpoints de la HU;
  - validaciones / errores de negocio relevantes de los criterios de aceptación;
  - control de acceso (rol o scope de tienda) cuando aplique.
- Ejecutar los tests de la HU antes del cierre:
  ```bash
  pytest tests/ -v -k "{filtro_de_la_hu_o_modulo}"
  ```
- Registrar la ruta de los tests en el índice y en el bloque de la HU del documento de épica.
- Si ya existen tests del módulo, extenderlos; no dejar la HU sin cobertura nueva o actualizada.

---

## Orden de cierre obligatorio al terminar una HU

Al terminar de implementar una HU, ejecutar estos pasos en orden. No cerrar la tarea sin haberlos completado todos.

**Paso 1 — Validar criterios de aceptación**
Contra `docs/Historias de usuario.md`, en la Epica correspondiente. Documentar el cumplimiento en el bloque HU.

**Paso 2 — Verificar el checklist Swagger**
Cada endpoint de la HU debe cumplir todos los ítems del checklist.

**Paso 3 — Tests**
Escribir/actualizar tests de la HU y ejecutarlos hasta que pasen.

**Paso 4 — Sincronizar documentación técnica**
```bash
python scripts/sync_docs.py
```

**Paso 5 — Actualizar documento de épica**
Crear la carpeta `docs/{Epica}/` si no existe. Agregar el bloque de la HU al final de `epica_{Epica}.md` y actualizar el índice (incluidos tests).

---

## Qué no hacer

- No inventar HUs, roles ni flujos fuera de `docs/Historias de usuario.md`.
- No copiar patrones ajenos al marketplace Singular.
- No exponer secretos, credenciales de pasarela ni claves de Supabase en docs ni en respuestas.
- No dar por cerrada una HU sin tests, sin sync de docs y sin bloque en la carpeta de la épica.
