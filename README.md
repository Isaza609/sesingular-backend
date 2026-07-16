# Singular Backend

API del marketplace **Singular** — monolito modular en **Python (FastAPI)**, **PostgreSQL (SQLAlchemy + Alembic)** y Redis opcional.

Documentación de dominio: [`docs/requerimientos.md`](./docs/requerimientos.md)

> El código NestJS/Prisma bajo `apps/` y `packages/` está **obsoleto** y no forma parte del stack activo.

---

## Stack activo

| Capa | Tecnología |
|---|---|
| API | FastAPI (`app/`) |
| ORM | SQLAlchemy 2.0 |
| Migraciones | Alembic |
| Schema Postgres | **`marketplace`** (todas las tablas de la app + `alembic_version`) |
| DB | PostgreSQL 16 (Docker local o Supabase) |

---

## Estructura

```
sesingular-backend/
├── app/
│   ├── main.py              # FastAPI
│   ├── core/config.py       # settings (.env)
│   ├── db/                  # Base + session (schema marketplace)
│   ├── models/              # SQLAlchemy
│   └── api/                 # routers
├── alembic/
│   ├── env.py               # version_table_schema = marketplace
│   └── versions/            # migraciones
├── tests/
│   └── test_marketplace_schema.py
├── docker-compose.yml       # Postgres + Redis
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## Requisitos

- Python ≥ 3.11
- Docker (Postgres + Redis) **o** URI de Supabase Postgres

---

## Arranque rápido

```bash
# 1. Entorno virtual e dependencias
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt

# 2. Variables de entorno
copy .env.example .env
# Edita DATABASE_URL si usas Supabase (ver abajo)

# 3. Infra local
docker compose up -d

# 4. Migraciones (crea schema marketplace + tablas)
alembic upgrade head

# 5. API
uvicorn app.main:app --reload --port 3001
```

Health: `GET http://localhost:3001/api/v1/health`  
Ready: `GET http://localhost:3001/api/v1/health/ready`

---

## Base de datos y schema `marketplace`

Todas las migraciones y tablas de la aplicación viven **únicamente** en el schema PostgreSQL `marketplace` (minúsculas). No se crean tablas de dominio en `public`.

Variables relevantes en `.env`:

```env
DATABASE_URL=postgresql+psycopg://singular:singular@localhost:5432/singular
DB_SCHEMA=marketplace
```

### Supabase

1. Project Settings → Database → Connection string (URI).
2. Prefija el driver SQLAlchemy: `postgresql+psycopg://...`
3. Ejemplo pooler:

```env
DATABASE_URL=postgresql+psycopg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
DB_SCHEMA=marketplace
```

Luego: `alembic upgrade head`

---

## Tests de aislamiento de schema

```bash
# Siempre (offline): metadata ORM + migración apuntan a marketplace
pytest tests/test_models_schema.py -v

# Integración (requiere PostgreSQL con DATABASE_URL válido):
# docker compose up -d   # o URI de Supabase
# alembic upgrade head
pytest tests/test_marketplace_schema.py -v
```

Los tests de integración verifican que:

1. Las tablas de la app existen en `marketplace`.
2. Esas mismas tablas **no** existen en `public`.
3. `alembic_version` está en `marketplace`.
4. Un insert/select smoke funciona en ese schema.
5. No existe el schema `Marketplace` (mayúscula).

Si Postgres no está disponible, los tests de integración se **saltan** automáticamente.

---

## Comandos útiles

| Comando | Descripción |
|---|---|
| `alembic upgrade head` | Aplicar migraciones |
| `alembic downgrade -1` | Revertir última migración |
| `alembic revision --autogenerate -m "msg"` | Nueva revisión (revisar diff) |
| `pytest` | Suite de tests |
| `docker compose up -d` | Postgres + Redis |
