### Estructura estándar

`app/modules/{modulo}/` con `router.py`, `service.py`, `schemas.py` y `models.py`.
Separación de capas: todo módulo nuevo sigue model → schemas → repository → service → router. 

### Registro y auditoría

- Registrar routers en `app/main.py` al final de la lista.
- Toda operación de escritura (POST, PUT, DELETE) debe registrarse usando `app/common/audit.py`.

En español la documentacion

## Terminal y entorno virtual

- La terminal siempre opera dentro del entorno virtual.
- Verificar que esté activo antes de ejecutar cualquier comando.
- Para activarlo: `.venv\Scripts\activate` (Windows).

## Seguridad y multi-tenancy

- Nunca exponer datos fuera del scope del tenant del usuario autenticado.
- Siempre validar que el usuario autenticado tiene permiso sobre el recurso solicitado.

## Estándares de documentación Swagger en código

Todo endpoint nuevo debe cumplir estos estándares sin excepción.
El Swagger (`/docs`) es la fuente de verdad técnica — lo que está en el código es lo que se exporta.
Ambos deben estar siempre sincronizados.

## Checklist por endpoint

Antes de ejecutar `sync_docs.py`, verificar que cada endpoint cumple:

- [ ] `summary` en una línea, verbo en infinitivo ("Crear alerta", "Listar vehículos")
- [ ] `description` con rol permitido, HU relacionada y comportamiento especial
- [ ] `response_description` describiendo qué retorna en éxito
- [ ] `response_model` tipado en el decorador
- [ ] `status_code` explícito
- [ ] `responses` con todos los códigos de error posibles (400, 401, 403, 404, 409, 502 según aplique)
- [ ] Schema de request con `Field(description=..., example=...)` en cada campo
- [ ] Schema de response con `Field(description=..., example=...)` en cada campo
- [ ] `model_config` con `json_schema_extra.example` completo y realista en el schema de request

# 5. Documentación de épica — Registro acumulativo por módulo

### 5.1 Propósito

El documento de épica es el único registro técnico y funcional de todo lo que se desarrolló en un módulo. Cumple dos funciones a la vez:

- **Registro funcional:** qué se implementó, cuándo, cómo se cumplieron los criterios de aceptación.
- **Contrato de API:** descripción completa de endpoints para que frontend los integre sin necesidad de abrir el Swagger.

No es un documento puntual. Es un historial vivo que crece con cada HU implementada. No se elimina ni se reescribe — solo se agrega al final.

### 5.2 Ubicación y nombre

```
docs/docs_plan/{Modulo}/epica_{Modulo}.md
```

Ejemplo: `docs/docs_plan/Alertas/epica_Alertas.md`

Un solo archivo por módulo. Nunca crear un archivo por HU ni por sprint.

### 5.3 Cuándo actualizar

Cada vez que se implementa una HU, agregar su bloque al final del documento y actualizar el índice.
No reescribir secciones anteriores salvo que una HU posterior corrija explícitamente algo anterior
(en ese caso anotar la corrección con fecha, no borrar el registro original).

### 5.4 Estructura del documento de épica

```markdown
# Épica {ID} — {Nombre del Módulo}

**Módulo:** {nombre}
**Épica ID:** {ej. 08}
**Swagger tag:** `{Modulo}`
**Prefijo de rutas:** `/api/v1/{modulo}`
**Autenticación:** `Authorization: Bearer <JWT Supabase>` (requerido en todos los endpoints)
**Scope:** Multi-tenant — todos los recursos filtrados por el tenant del usuario autenticado.
**Última actualización:** {fecha}

---

## Resumen del módulo

Descripción general de qué resuelve este módulo, qué entidades maneja,
qué roles intervienen y cuál es su relación con Traccar (si aplica).

---

## Índice de HUs implementadas

| HU | Título | Fecha | Endpoints |
|---|---|---|---|
| HU-08-01 | Listar alertas | 2026-05-10 | `GET /api/v1/alertas` |
| HU-08-02 | Crear alerta | 2026-05-15 | `POST /api/v1/alertas/` |

---

<!-- Repetir este bloque por cada HU implementada, agregando al final -->

## HU-{ID} · {Título}

**Fecha de implementación:** {fecha}
**Fecha HU en docs_plan:** {fecha extraída del archivo HU_{Modulo}.md}
**Estado:** Implementada

### Descripción funcional

Qué resuelve esta HU desde el punto de vista del usuario o del sistema.
Contexto de negocio relevante para entender los endpoints.

### Criterios de aceptación

| # | Criterio | Cumplido | Cómo se cumplió |
|---|---|---|---|
| 1 | {criterio} | ✅ | {explicación técnica de cómo lo cumple la implementación} |
| 2 | {criterio} | ✅ | {explicación} |

### Flujo implementado

Descripción del flujo completo en orden de ejecución.
Si involucra varios endpoints o una saga Kronox ↔ Traccar, describirlo paso a paso.

```
1. Frontend llama POST /api/v1/alertas/ con body {…}
2. Service valida que el tenant tenga permiso
3. Se crea el registro en kronox.fleet_alerts
4. Se replica en Traccar vía client.py → POST /api/notifications
5. Si Traccar falla → rollback en Kronox (DELETE fleet_alerts)
6. Retorna el objeto creado con su ID
```

### Endpoints implementados en esta HU

<!-- Repetir por cada endpoint de la HU -->

#### {MÉTODO} `/api/v1/{ruta}` → {código HTTP exitoso}

**Descripción:** Qué hace, para qué rol aplica, comportamiento especial.
**Roles permitidos:** `admin_cliente`, `usuario_final`
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
  "nombre": "Alerta velocidad",
  "tipo": "speed",
  "limite_velocidad": 80,
  "vehiculo_ids": [1, 2, 3]
}
```

| Campo | Tipo | Req/Opt | Descripción |
|---|---|---|---|
| `nombre` | `string` | requerido | Nombre descriptivo de la alerta. Único por tenant. |
| `tipo` | `enum` | requerido | Valores: `speed`, `geofence`, `ignition` |
| `limite_velocidad` | `int` | opcional | Solo si `tipo = speed`. En km/h. |
| `vehiculo_ids` | `int[]` | requerido | IDs de vehículos Kronox a asociar. |

**Response exitosa:**
```json
{
  "id": 42,
  "nombre": "Alerta velocidad",
  "tipo": "speed",
  "limite_velocidad": 80,
  "vehiculos": [
    { "id": 1, "placa": "ABC-123" }
  ],
  "creado_en": "2026-05-15T10:32:00Z"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | ID interno Kronox |
| `nombre` | `string` | Nombre de la alerta |
| `vehiculos` | `object[]` | Lista de vehículos asociados |
| `creado_en` | `datetime` | ISO 8601 UTC |

**Errores posibles:**
| Código | Situación | Mensaje típico |
|---|---|---|
| 400 | Datos inválidos o regla de negocio violada | `"limite_velocidad requerido cuando tipo es speed"` |
| 401 | Sin autenticación | `"Token inválido o expirado"` |
| 403 | Rol no permitido | `"El rol del usuario no tiene acceso a esta operación"` |
| 404 | Recurso no encontrado | `"Vehículo 99 no encontrado en este tenant"` |
| 409 | Conflicto | `"Ya existe una alerta con ese nombre en este tenant"` |
| 422 | Validación Pydantic | Array `detail` estándar de FastAPI |
| 502 | Fallo Traccar | `"No se pudo crear la notificación en Traccar"` |

### Notas y advertencias para frontend

Lista de aspectos críticos que frontend debe conocer para esta HU:
- Enums aceptados, formatos de fecha, tipos de ID.
- Campos que cambiaron respecto a Traccar (si aplica).
- Comportamientos condicionales o efectos secundarios.

---
<!-- fin del bloque HU — agregar el siguiente al final del archivo -->
```

### 5.5 Orden de cierre obligatorio al terminar una HU

Al terminar de implementar una HU, ejecutar estos tres pasos en orden. No cerrar la tarea sin haberlos completado todos.

**Paso 1 — Verificar el checklist de §6.3**
Cada endpoint de la HU debe cumplir todos los ítems antes de continuar.

**Paso 2 — Sincronizar documentación técnica**
```bash
python scripts/sync_docs.py