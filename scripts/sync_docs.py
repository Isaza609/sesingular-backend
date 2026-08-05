"""
sync_docs.py — Genera openapi.json y API_REFERENCE.md desde el spec en runtime.

Ejecutar desde la raíz de sesingular-backend/:
    python scripts/sync_docs.py

Escribe en:
  - sesingular-backend/docs/
  - sesingular-Frontend/docs/APIS/
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Encoding — fuerza UTF-8 en la salida para que los emojis (✅/❌/⚠️) no
# rompan en consolas Windows que usan cp1252 por defecto.
# ---------------------------------------------------------------------------
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        # Streams sin reconfigure (redirigidos/no-TextIOWrapper): se ignora.
        pass

# ---------------------------------------------------------------------------
# Rutas de destino
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
API_ROOT = SCRIPT_DIR.parent  # sesingular-backend/
REPO_ROOT = API_ROOT.parent  # Singular/
FRONTEND_DOCS = REPO_ROOT / "sesingular-Frontend" / "docs" / "APIS"

DEST_JSON = [
    API_ROOT / "docs" / "openapi.json",
    FRONTEND_DOCS / "openapi.json",
]
DEST_MD = [
    API_ROOT / "docs" / "API_REFERENCE.md",
    FRONTEND_DOCS / "API_REFERENCE.md",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def _fail(msg: str, exc: Exception) -> None:
    print(f"  ❌ {msg}: {exc}")


def _ensure_dirs(*paths: Path) -> None:
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Paso 1 — Obtener el spec OpenAPI desde la app en runtime
# ---------------------------------------------------------------------------

def _patch_create_engine() -> None:
    """
    Evita inicializar el driver de Postgres al importar la app.

    OpenAPI se genera solo desde routers/schemas de FastAPI (el contrato que
    se despliega). No se consulta la base de datos. create_engine se ejecuta
    al importar app.db.session y aquí puede fallar psycopg/libpq; devolvemos
    un engine SQLite local solo como stub de import — Settings/.env siguen
    siendo los de Singular y las rutas exportadas son las de app.main.
    """
    import sqlalchemy

    real_create_engine = sqlalchemy.create_engine

    def _stub_create_engine(_url, **kwargs):
        # Ignora la URL real; no se conecta a producción ni a local.
        kwargs.pop("pool_pre_ping", None)
        return real_create_engine("sqlite+pysqlite:///:memory:")

    sqlalchemy.create_engine = _stub_create_engine  # type: ignore[assignment]


def load_openapi_spec() -> dict | None:
    print("\n[1/4] Cargando spec OpenAPI desde app.main …")
    try:
        # CWD debe ser sesingular-backend/ para que Settings cargue .env real
        os.chdir(API_ROOT)

        api_root_str = str(API_ROOT)
        if api_root_str not in sys.path:
            sys.path.insert(0, api_root_str)

        _patch_create_engine()

        from app.main import app  # noqa: PLC0415
        from app.core.config import get_settings  # noqa: PLC0415

        settings = get_settings()
        _ok(
            f"App: {settings.app_name} v{app.version} — "
            f"prefix /{settings.api_prefix.strip('/')}"
        )

        spec = app.openapi()
        _ok(f"Spec cargado — {len(spec.get('paths', {}))} rutas (contrato desplegable)")
        return spec
    except Exception as exc:
        _fail("No se pudo cargar el spec", exc)
        return None


# ---------------------------------------------------------------------------
# Paso 2 — Escribir openapi.json en ambos destinos
# ---------------------------------------------------------------------------

def write_json(spec: dict) -> None:
    print("\n[2/4] Escribiendo openapi.json …")
    for dest in DEST_JSON:
        try:
            _ensure_dirs(dest)
            dest.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
            _ok(str(dest))
        except Exception as exc:
            _fail(str(dest), exc)


# ---------------------------------------------------------------------------
# Paso 3 — Generar Markdown
# ---------------------------------------------------------------------------

def _resolve_ref(ref: str, components: dict) -> dict:
    """Resuelve una $ref simple del tipo #/components/schemas/Foo."""
    parts = ref.lstrip("#/").split("/")
    node: dict = {"components": components}
    for part in parts[1:]:  # salta "components"
        node = node.get(part, {})
    return node


def _flatten_schema(schema: dict, components: dict, depth: int = 0) -> list[dict]:
    """
    Devuelve lista de filas {name, type, required, description} a partir de un schema.
    Resuelve $ref y allOf/anyOf/oneOf un nivel.
    """
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], components)

    # allOf / anyOf / oneOf — fusiona propiedades
    for combiner in ("allOf", "anyOf", "oneOf"):
        if combiner in schema:
            merged: dict = {}
            required_all: list = []
            for sub in schema[combiner]:
                resolved = _resolve_ref(sub["$ref"], components) if "$ref" in sub else sub
                merged.update(resolved.get("properties", {}))
                required_all.extend(resolved.get("required", []))
            schema = {**schema, "properties": merged, "required": required_all}

    rows: list[dict] = []
    props = schema.get("properties", {})
    required_fields = schema.get("required", [])
    for name, prop in props.items():
        if "$ref" in prop:
            prop = _resolve_ref(prop["$ref"], components)
        field_type = prop.get("type", "object")
        if "anyOf" in prop:
            types = [t.get("type", "$ref") for t in prop["anyOf"] if "type" in t or "$ref" in t]
            field_type = " | ".join(types) if types else "any"
        rows.append({
            "name": name,
            "type": field_type,
            "required": "✓" if name in required_fields else "",
            "description": prop.get("description", prop.get("title", "")),
        })
    return rows


def _example_from_schema(schema: dict, components: dict, depth: int = 0) -> object:
    """Genera un ejemplo JSON mínimo a partir de un schema."""
    if depth > 4:
        return "…"
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], components)

    if "example" in schema:
        return schema["example"]
    if "examples" in schema:
        return next(iter(schema["examples"].values()), {})

    for combiner in ("allOf", "anyOf", "oneOf"):
        if combiner in schema:
            merged: dict = {}
            for sub in schema[combiner]:
                resolved = _resolve_ref(sub["$ref"], components) if "$ref" in sub else sub
                example = _example_from_schema(resolved, components, depth + 1)
                if isinstance(example, dict):
                    merged.update(example)
            return merged if merged else {}

    kind = schema.get("type", "object")
    if kind == "object":
        result: dict = {}
        for name, prop in schema.get("properties", {}).items():
            result[name] = _example_from_schema(prop, components, depth + 1)
        return result
    if kind == "array":
        items = schema.get("items", {})
        return [_example_from_schema(items, components, depth + 1)]
    defaults = {
        "string": "string",
        "integer": 0,
        "number": 0.0,
        "boolean": True,
    }
    return defaults.get(kind, None)


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt_row(cells: list) -> str:
        return "| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells)) + " |"

    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    lines = [fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


def _json_block(obj: object) -> str:
    return "```json\n" + json.dumps(obj, indent=2, ensure_ascii=False) + "\n```"


def _collect_errors(operation: dict) -> list[list[str]]:
    rows: list[list[str]] = []
    for code, resp in operation.get("responses", {}).items():
        if str(code).startswith("2"):
            continue
        desc = resp.get("description", "")
        rows.append([str(code), desc, ""])
    return rows


def build_markdown(spec: dict) -> str:
    components = spec.get("components", {})
    info = spec.get("info", {})

    lines: list[str] = [
        f"# {info.get('title', 'API Reference')}",
        "",
        f"**Versión:** {info.get('version', '—')}",
        "",
        info.get("description", ""),
        "",
        "---",
        "",
        "## Índice de endpoints",
        "",
    ]

    paths = spec.get("paths", {})
    # Índice
    for path, methods in paths.items():
        for method in ("get", "post", "put", "patch", "delete"):
            if method in methods:
                op = methods[method]
                summary = op.get("summary", op.get("operationId", path))
                anchor = f"{method.upper()}-{path}".lower().replace("/", "").replace("{", "").replace("}", "").replace("_", "-")
                lines.append(f"- [{method.upper()} `{path}`](#{anchor}) — {summary}")

    lines += ["", "---", ""]

    # Detalle de cada endpoint
    for path, methods in paths.items():
        for method in ("get", "post", "put", "patch", "delete"):
            if method not in methods:
                continue
            op = methods[method]
            anchor = f"{method.upper()}-{path}".lower().replace("/", "").replace("{", "").replace("}", "").replace("_", "-")

            lines.append(f"## `{method.upper()}` `{path}`")
            lines.append("")

            summary = op.get("summary", "")
            description = op.get("description", "")
            if summary:
                lines.append(f"**{summary}**")
                lines.append("")
            if description:
                lines.append(description)
                lines.append("")

            tags = op.get("tags", [])
            if tags:
                lines.append(f"**Tags:** {', '.join(tags)}")
                lines.append("")

            # Parámetros (path + query)
            params = op.get("parameters", [])
            path_params = [p for p in params if p.get("in") == "path"]
            query_params = [p for p in params if p.get("in") == "query"]

            if path_params:
                lines.append("### Parámetros de ruta")
                lines.append("")
                rows = [
                    [p["name"], p.get("schema", {}).get("type", "string"), "✓" if p.get("required") else "", p.get("description", "")]
                    for p in path_params
                ]
                lines.append(_md_table(["Nombre", "Tipo", "Requerido", "Descripción"], rows))
                lines.append("")

            if query_params:
                lines.append("### Parámetros de query")
                lines.append("")
                rows = [
                    [p["name"], p.get("schema", {}).get("type", "string"), "✓" if p.get("required") else "", p.get("description", "")]
                    for p in query_params
                ]
                lines.append(_md_table(["Nombre", "Tipo", "Requerido", "Descripción"], rows))
                lines.append("")

            # Request body
            req_body = op.get("requestBody", {})
            if req_body:
                lines.append("### Request body")
                lines.append("")
                content = req_body.get("content", {})
                schema: dict = {}
                for mime, media in content.items():
                    schema = media.get("schema", {})
                    break

                if schema:
                    example = _example_from_schema(schema, components)
                    if example:
                        lines.append(_json_block(example))
                        lines.append("")

                    fields = _flatten_schema(schema, components)
                    if fields:
                        rows = [[f["name"], f["type"], f["required"], f["description"]] for f in fields]
                        lines.append(_md_table(["Campo", "Tipo", "Requerido", "Descripción"], rows))
                        lines.append("")

            # Respuesta exitosa
            responses = op.get("responses", {})
            success_code = next((c for c in responses if str(c).startswith("2")), None)
            if success_code:
                resp = responses[success_code]
                lines.append(f"### Respuesta `{success_code}`")
                lines.append("")
                resp_desc = resp.get("description", "")
                if resp_desc:
                    lines.append(resp_desc)
                    lines.append("")

                resp_content = resp.get("content", {})
                resp_schema: dict = {}
                for mime, media in resp_content.items():
                    resp_schema = media.get("schema", {})
                    break

                if resp_schema:
                    example = _example_from_schema(resp_schema, components)
                    if example:
                        lines.append(_json_block(example))
                        lines.append("")

                    fields = _flatten_schema(resp_schema, components)
                    if fields:
                        rows = [[f["name"], f["type"], f["required"], f["description"]] for f in fields]
                        lines.append(_md_table(["Campo", "Tipo", "Requerido", "Descripción"], rows))
                        lines.append("")

            # Errores
            error_rows = _collect_errors(op)
            if error_rows:
                lines.append("### Errores posibles")
                lines.append("")
                lines.append(_md_table(["Código", "Situación", "Mensaje típico"], error_rows))
                lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def write_markdown(spec: dict) -> None:
    print("\n[3/4] Generando API_REFERENCE.md …")
    try:
        md = build_markdown(spec)
        _ok(f"Markdown generado ({len(md):,} caracteres, {md.count(chr(10)):,} líneas)")
    except Exception as exc:
        _fail("Error generando Markdown", exc)
        return

    print("\n[4/4] Escribiendo API_REFERENCE.md …")
    for dest in DEST_MD:
        try:
            _ensure_dirs(dest)
            dest.write_text(md, encoding="utf-8")
            _ok(str(dest))
        except Exception as exc:
            _fail(str(dest), exc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  sync_docs.py — Singular API documentation sync")
    print("=" * 60)

    spec = load_openapi_spec()
    if spec is None:
        print("\n⚠️  No se pudo cargar el spec; abortando pasos 2-4.")
        sys.exit(1)

    write_json(spec)
    write_markdown(spec)

    print("\n" + "=" * 60)
    print("  Sincronización completada.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
