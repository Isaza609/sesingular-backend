# Epica 01: Gestion de usuarios

**Epica ID:** 01
**Modulo / prefijo HU:** USR
**Swagger tag:** `auth`, `admin`, `seller`, `buyer`
**Prefijo de rutas:** `/api/v1/auth`, `/api/v1/admin`, `/api/v1/seller`, `/api/v1/addresses`
**Autenticacion:** `Authorization: Bearer <JWT Supabase>` en rutas privadas; registro, login y recuperacion son publicos.
**Scope:** comprador autenticado / tienda del vendedor / plataforma admin
**Ultima actualizacion:** 2026-08-05

---

## Resumen del modulo

Esta epica implementa la gestion de usuarios del marketplace Singular segun `docs/Historias de usuario.md`. El comprador es el unico rol con autorregistro publico. Vendedores, administradores y usuarios adicionales de tienda son creados desde administracion con credenciales temporales y cambio obligatorio de contrasena. El comprador gestiona su perfil y direcciones de envio, y todos los usuarios registrados pueden recuperar contrasena por correo mediante Supabase Auth.

---

## Indice de HUs implementadas

| HU | Titulo | Fecha | Endpoints | Tests |
|---|---|---|---|---|
| HU-USR-01 | Registro e inicio de sesion de comprador | 2026-08-05 | `POST /api/v1/auth/register`, `POST /api/v1/auth/login` | `tests/test_hu_usr_01_auth_buyer.py` |
| HU-USR-02 | Primer ingreso del vendedor con credenciales entregadas | 2026-08-05 | `POST /api/v1/auth/login`, `POST /api/v1/auth/change-password`, `POST /api/v1/admin/users`, `POST /api/v1/admin/users/{user_id}/temporary-password` | `tests/test_hu_usr_02_seller_first_login.py` |
| HU-USR-03 | Edicion de perfil y datos de contacto/envio del comprador | 2026-08-05 | `GET /api/v1/auth/me`, `PATCH /api/v1/auth/me`, CRUD `/api/v1/addresses` | `tests/test_hu_usr_03_profile_addresses.py` |
| HU-USR-04 | Recuperacion de contrasena | 2026-08-05 | `POST /api/v1/auth/password-recovery/request`, `POST /api/v1/auth/password-recovery/confirm` | `tests/test_hu_usr_04_password_recovery.py` |
| HU-USR-05 | Usuarios adicionales asociados a una tienda | 2026-08-05 | `POST/GET/PATCH /api/v1/admin/stores/{store_id}/members`, `GET /api/v1/seller/store/members` | `tests/test_hu_usr_05_store_members.py` |

---

## HU-USR-01 · Registro e inicio de sesion de comprador

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_usr_01_auth_buyer.py`

### Descripcion funcional

El comprador se registra publicamente con correo, contrasena, nombre y telefono opcional. El backend crea o vincula la identidad en Supabase Auth y persiste el perfil local con rol `buyer`. El login valida credenciales contra Supabase Auth y retorna una sesion sin revelar si fallo el correo o la contrasena.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Dado que ingreso un correo valido no registrado y una contrasena que cumple la politica minima, cuando confirmo el registro, entonces se crea mi cuenta con rol comprador y quedo autenticado. | Si | `POST /api/v1/auth/register` crea el usuario local `buyer` y retorna sesion o estado de confirmacion segun Supabase. |
| 2 | Dado que ingreso un correo ya registrado, cuando intento registrarme, entonces el sistema rechaza la operacion con un mensaje descriptivo. | Si | Se valida email local antes de llamar Supabase y se responde `409`. |
| 3 | Dado que intento registrarme como vendedor desde el formulario publico, cuando busco esa opcion, entonces no existe: el unico rol autorregistrable es comprador. | Si | El schema publico no admite `role` y rechaza campos extra. |
| 4 | Dado que ingreso credenciales incorrectas, cuando intento iniciar sesion, entonces el sistema rechaza el acceso sin revelar cual dato es incorrecto. | Si | `POST /api/v1/auth/login` normaliza el error a `401 Credenciales invalidas`. |

### Flujo implementado

```text
1. Frontend llama POST /api/v1/auth/register o POST /api/v1/auth/login.
2. Auth service encapsula Supabase Auth.
3. Se crea/consulta marketplace.users con rol buyer.
4. Se retorna SessionOut con perfil local y tokens si Supabase los entrega.
```

### Endpoints implementados en esta HU

#### POST `/api/v1/auth/register` -> 201

**Roles permitidos:** publico
**Archivo:** `app/modules/auth/router.py`
**Request body:** `email`, `password`, `name`, `phone`.
**Response exitosa:** `SessionOut` con `user`, `access_token`, `refresh_token`, `status`, `must_change_password`.
**Errores posibles:** `400`, `409`, `422`, `502`.

#### POST `/api/v1/auth/login` -> 200

**Roles permitidos:** publico
**Archivo:** `app/modules/auth/router.py`
**Request body:** `email`, `password`.
**Response exitosa:** `SessionOut`.
**Errores posibles:** `401`, `403`, `422`, `502`.

### Tests de esta HU

- Archivo: `tests/test_hu_usr_01_auth_buyer.py`
- Cobertura: registro exitoso, email duplicado, intento de rol vendedor desde registro publico y login invalido.
- Ejecucion: `pytest tests/test_hu_usr_01_auth_buyer.py -v`

### Notas para frontend

- No enviar `role` en registro publico.
- Login puede retornar `must_change_password=true` para usuarios provisionados por administracion.

---

## HU-USR-02 · Primer ingreso del vendedor con credenciales entregadas

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_usr_02_seller_first_login.py`

### Descripcion funcional

Administracion crea vendedores y usuarios de equipo con credencial temporal. El perfil local queda marcado con `must_change_password=true` y vencimiento opcional. Al iniciar sesion, el backend informa el cambio obligatorio; las rutas privadas de panel se bloquean hasta que el usuario ejecute `POST /api/v1/auth/change-password`.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Dado que recibi credenciales temporales, cuando ingreso por primera vez, entonces el sistema me obliga a definir una contrasena nueva antes de continuar. | Si | Login retorna `must_change_password=true` y las dependencias de rol bloquean panel. |
| 2 | Dado que defino una contrasena nueva que cumple la politica minima, cuando la guardo, entonces accedo al panel de mi tienda ya creada. | Si | `POST /auth/change-password` actualiza Supabase, limpia el bloqueo y mantiene `StoreMember`. |
| 3 | Dado que intento omitir el cambio de contrasena, cuando navego a cualquier seccion del panel, entonces el sistema me redirige al cambio obligatorio. | Si | Las rutas privadas responden `403` con codigo funcional `password_change_required`. |
| 4 | Dado que mi contrasena temporal fue invalidada o expiro, cuando intento usarla, entonces el sistema me indica que contacte al administrador. | Si | Login valida `temporary_password_expires_at` y responde `403` con mensaje de contacto admin. |

### Flujo implementado

```text
1. Admin crea o regenera credencial temporal.
2. Usuario inicia sesion por POST /api/v1/auth/login.
3. Si must_change_password=true, frontend debe mostrar cambio obligatorio.
4. Usuario llama POST /api/v1/auth/change-password.
5. El backend actualiza Supabase y habilita el acceso al panel de su tienda.
```

### Endpoints implementados en esta HU

#### POST `/api/v1/auth/change-password` -> 200

**Roles permitidos:** buyer, seller, admin autenticado
**Archivo:** `app/modules/auth/router.py`
**Headers requeridos:** `Authorization: Bearer <JWT>`
**Request body:** `new_password`.
**Response exitosa:** perfil sin cambio obligatorio pendiente.
**Errores posibles:** `401`, `403`, `422`, `502`.

#### POST `/api/v1/admin/users` -> 201

**Roles permitidos:** admin
**Archivo:** `app/modules/admin/router.py`
**Headers requeridos:** `Authorization: Bearer <JWT>`
**Request body:** datos de usuario, rol y vigencia de credencial temporal.
**Response exitosa:** usuario creado y `temporary_password` visible una sola vez si aplica.
**Errores posibles:** `400`, `401`, `403`, `409`, `422`, `502`.

#### POST `/api/v1/admin/users/{user_id}/temporary-password` -> 200

**Roles permitidos:** admin
**Archivo:** `app/modules/admin/router.py`
**Response exitosa:** nueva credencial temporal visible una sola vez.
**Errores posibles:** `401`, `403`, `404`, `422`, `502`.

### Tests de esta HU

- Archivo: `tests/test_hu_usr_02_seller_first_login.py`
- Cobertura: primer login, cambio valido, bloqueo por omitir cambio y credencial vencida.
- Ejecucion: `pytest tests/test_hu_usr_02_seller_first_login.py -v`

### Notas para frontend

- Si cualquier ruta privada responde `403` con `detail.code=password_change_required`, dirigir a la pantalla de cambio obligatorio.
- Si login responde credencial temporal expirada, indicar contactar al administrador.

---

## HU-USR-03 · Edicion de perfil y datos de contacto/envio del comprador

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_usr_03_profile_addresses.py`

### Descripcion funcional

El comprador autenticado puede consultar y actualizar su perfil basico, y administrar direcciones de envio propias. Las direcciones quedan vinculadas a `marketplace.addresses.user_id`; no se exponen ni mutan direcciones de otros compradores.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Dado que modifico mi nombre, telefono o direccion, cuando guardo los cambios, entonces mi perfil refleja la informacion actualizada. | Si | `PATCH /auth/me` actualiza perfil y CRUD `/addresses` actualiza direcciones. |
| 2 | Dado que agrego una nueva direccion de envio, cuando la guardo, entonces queda disponible para seleccionar en futuros checkouts. | Si | `POST /addresses` persiste direccion del comprador autenticado. |
| 3 | Dado que dejo un campo obligatorio vacio, cuando intento guardar, entonces el sistema no permite guardar y senala el campo. | Si | Schemas Pydantic usan `min_length` y devuelven `422`. |

### Flujo implementado

```text
1. Comprador usa GET/PATCH /api/v1/auth/me para perfil.
2. Comprador usa GET/POST/PATCH/DELETE /api/v1/addresses para direcciones.
3. Cada operacion usa require_buyer y filtra por user_id.
4. Si una direccion se marca por defecto, las anteriores del mismo comprador se desmarcan.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/auth/me` -> 200

**Roles permitidos:** buyer, seller, admin
**Archivo:** `app/modules/auth/router.py`
**Response exitosa:** perfil autenticado.

#### PATCH `/api/v1/auth/me` -> 200

**Roles permitidos:** buyer, seller, admin
**Archivo:** `app/modules/auth/router.py`
**Request body:** `name`, `phone`.
**Response exitosa:** perfil actualizado.

#### GET/POST/PATCH/DELETE `/api/v1/addresses` -> 200/201/204

**Roles permitidos:** buyer
**Archivo:** `app/modules/orders/router.py`
**Request body:** datos de direccion para `POST` y campos parciales para `PATCH`.
**Response exitosa:** direccion o lista de direcciones; `DELETE` no retorna contenido.
**Errores posibles:** `401`, `403`, `404`, `422`.

### Tests de esta HU

- Archivo: `tests/test_hu_usr_03_profile_addresses.py`
- Cobertura: perfil, CRUD de direcciones, default unico, validacion de campos obligatorios y aislamiento de direcciones ajenas.
- Ejecucion: `pytest tests/test_hu_usr_03_profile_addresses.py -v`

### Notas para frontend

- `is_default=true` en una direccion nueva o editada desplaza la direccion por defecto anterior del mismo comprador.
- Una direccion ajena responde como no encontrada para no filtrar datos.

---

## HU-USR-04 · Recuperacion de contrasena

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_usr_04_password_recovery.py`

### Descripcion funcional

El usuario solicita recuperacion por correo. El backend delega el envio y validacion del enlace/codigo a Supabase Auth mediante una fachada interna. La confirmacion con token vigente actualiza la contrasena y limpia estados locales de cambio obligatorio cuando corresponde.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Dado que solicito recuperar mi contrasena con un correo registrado, cuando confirmo la solicitud, entonces recibo un enlace o codigo para restablecerla. | Si | `POST /auth/password-recovery/request` llama Supabase recover y no retorna secretos. |
| 2 | Dado que el enlace o codigo recibido esta vigente, cuando lo utilizo con una nueva contrasena valida, entonces puedo iniciar sesion con la nueva contrasena. | Si | `POST /auth/password-recovery/confirm` actualiza la contrasena mediante el token de recuperacion. |
| 3 | Dado que el enlace o codigo expiro, cuando intento usarlo, entonces el sistema lo rechaza y me permite solicitar uno nuevo. | Si | Errores de token invalido/expirado se retornan como rechazo; el request puede ejecutarse de nuevo. |

### Flujo implementado

```text
1. Usuario llama POST /api/v1/auth/password-recovery/request con su email.
2. Supabase Auth envia enlace/codigo al correo.
3. Usuario llama POST /api/v1/auth/password-recovery/confirm con token y nueva contrasena.
4. Backend actualiza contrasena y marca password_changed_at si puede asociar el email local.
```

### Endpoints implementados en esta HU

#### POST `/api/v1/auth/password-recovery/request` -> 202

**Roles permitidos:** publico
**Archivo:** `app/modules/auth/router.py`
**Request body:** `email`.
**Response exitosa:** mensaje de recepcion.

#### POST `/api/v1/auth/password-recovery/confirm` -> 200

**Roles permitidos:** publico
**Archivo:** `app/modules/auth/router.py`
**Request body:** `recovery_token`, `new_password`, `email` opcional.
**Response exitosa:** mensaje de contrasena restablecida.
**Errores posibles:** `401`, `422`, `502`.

### Tests de esta HU

- Archivo: `tests/test_hu_usr_04_password_recovery.py`
- Cobertura: solicitud, confirmacion valida y token expirado.
- Ejecucion: `pytest tests/test_hu_usr_04_password_recovery.py -v`

### Notas para frontend

- El request no devuelve token; el canal de correo lo gestiona Supabase.
- Si el token expiro, mostrar opcion de solicitar uno nuevo.

---

## HU-USR-05 · Usuarios adicionales asociados a una tienda

**Fecha de implementacion:** 2026-08-05
**HU en:** `docs/Historias de usuario.md`
**Estado:** Implementada
**Tests:** `tests/test_hu_usr_05_store_members.py`

### Descripcion funcional

El admin crea usuarios adicionales asociados a una tienda mediante `StoreMember`. Esos usuarios tienen rol de plataforma `seller`, credencial temporal y acceden al mismo panel de la tienda. El vendedor puede listar miembros activos e inactivos de su tienda, pero no crearlos ni desactivarlos.

### Criterios de aceptacion

| # | Criterio | Cumplido | Como se cumplio |
|---|---|---|---|
| 1 | Dado que creo un usuario adicional y lo asocio a una tienda, cuando lo guardo, entonces ese usuario recibe credenciales y accede al panel de esa tienda. | Si | `POST /admin/stores/{store_id}/members` crea usuario, credencial temporal y `StoreMember`. |
| 2 | Dado que varios usuarios de una misma tienda ingresan al panel, cuando lo consultan, entonces todos ven los mismos pedidos, inventario y pendientes de la tienda. | Si | `get_seller_store` resuelve scope por `StoreMember`, no por usuario propietario unico. |
| 3 | Dado que desactivo un usuario de equipo, cuando lo hago, entonces pierde acceso al panel de inmediato sin afectar los registros historicos que genero. | Si | `PATCH /admin/stores/{store_id}/members/{user_id}` cambia `user.active`; no borra membresia ni historico. |
| 4 | Dado que soy vendedor, cuando consulto los usuarios de mi tienda, entonces veo la lista de activos e inactivos aunque no pueda crearlos yo mismo. | Si | `GET /seller/store/members` es solo lectura; no existe POST seller equivalente. |

### Flujo implementado

```text
1. Admin crea miembro por POST /api/v1/admin/stores/{store_id}/members.
2. Backend crea identidad Supabase, usuario local seller y StoreMember.
3. El usuario cambia contrasena en su primer ingreso.
4. Todas las rutas seller resuelven la tienda por StoreMember.
5. El vendedor consulta miembros por GET /api/v1/seller/store/members.
```

### Endpoints implementados en esta HU

#### GET `/api/v1/admin/stores/{store_id}/members` -> 200

**Roles permitidos:** admin
**Archivo:** `app/modules/admin/router.py`
**Response exitosa:** lista de miembros activos e inactivos.

#### POST `/api/v1/admin/stores/{store_id}/members` -> 201

**Roles permitidos:** admin
**Archivo:** `app/modules/admin/router.py`
**Request body:** email, nombre, telefono, rol interno y vigencia temporal.
**Response exitosa:** miembro creado con `temporary_password` visible una sola vez.

#### PATCH `/api/v1/admin/stores/{store_id}/members/{user_id}` -> 200

**Roles permitidos:** admin
**Archivo:** `app/modules/admin/router.py`
**Request body:** `active`, `member_role`.
**Response exitosa:** miembro actualizado.

#### GET `/api/v1/seller/store/members` -> 200

**Roles permitidos:** seller
**Archivo:** `app/modules/seller/router.py`
**Response exitosa:** miembros de la tienda del vendedor autenticado.

### Tests de esta HU

- Archivo: `tests/test_hu_usr_05_store_members.py`
- Cobertura: creacion con credencial temporal, scope compartido por tienda, desactivacion inmediata y vendedor solo lectura.
- Ejecucion: `pytest tests/test_hu_usr_05_store_members.py -v`

### Notas para frontend

- `temporary_password` solo se muestra al admin en la respuesta de creacion/regeneracion.
- Un usuario desactivado falla autenticacion privada aunque conserve membresias historicas.

---

## Validaciones ejecutadas

- `C:\Users\Personal\Documents\GitHub\Singular\sesingular-backend\.venv\Scripts\python.exe -m pytest tests -v -k "hu_usr or usr_openapi"` -> 21 passed.
- `C:\Users\Personal\Documents\GitHub\Singular\sesingular-backend\.venv\Scripts\python.exe -m pytest tests -q` -> 29 passed, 3 skipped.
- Sincronizacion backend-only de `scripts/sync_docs.py` -> `docs/openapi.json` y `docs/API_REFERENCE.md` actualizados.
