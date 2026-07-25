"""Generate docs/reference/api.md from the FastAPI OpenAPI schema.

Extracts the schema via create_app().openapi() without starting the server,
so the generated reference always matches the code.
"""

from pathlib import Path
from typing import Any

from taskdog_server.api.app import create_app

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "reference" / "api.md"

HEADER = """\
# API Reference

Auto-generated from the FastAPI OpenAPI schema. Do not edit by hand —
run `make docs-api` to regenerate. For usage examples and authentication
setup, see the [API Guide](api-guide.md).

A running server also exposes interactive docs at `/docs` (Swagger UI)
and `/redoc` (ReDoc).
"""


def _format_parameters(parameters: list[dict[str, Any]]) -> list[str]:
    lines = [
        "",
        "| Parameter | In | Type | Required | Description |",
        "| --- | --- | --- | --- | --- |",
    ]
    for param in parameters:
        schema = param.get("schema", {})
        param_type = schema.get("type", "any")
        if "anyOf" in schema:
            param_type = " \\| ".join(sub.get("type", "any") for sub in schema["anyOf"])
        required = "yes" if param.get("required") else "no"
        description = (param.get("description") or "").replace("\n", " ")
        lines.append(
            f"| `{param['name']}` | {param['in']} | {param_type} "
            f"| {required} | {description} |"
        )
    return lines


def _schema_name(operation: dict[str, Any]) -> str | None:
    try:
        ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    except KeyError:
        return None
    return str(ref).rsplit("/", maxsplit=1)[-1]


def _format_operation(path: str, method: str, operation: dict[str, Any]) -> list[str]:
    summary = operation.get("summary", "")
    lines = [f"### `{method.upper()} {path}`", ""]
    if summary:
        lines.append(f"**{summary}**")
        lines.append("")
    description = operation.get("description")
    if description:
        lines.append(description.strip())
        lines.append("")
    parameters = operation.get("parameters", [])
    if parameters:
        lines.extend(_format_parameters(parameters))
        lines.append("")
    body_schema = _schema_name(operation)
    if body_schema:
        lines.append(f"Request body: `{body_schema}`")
        lines.append("")
    responses = operation.get("responses", {})
    if responses:
        codes = ", ".join(f"`{code}`" for code in sorted(responses))
        lines.append(f"Responses: {codes}")
        lines.append("")
    return lines


def generate() -> str:
    schema = create_app().openapi()
    sections: dict[str, list[str]] = {}
    for path, methods in schema["paths"].items():
        for method, operation in methods.items():
            tag = (operation.get("tags") or ["Other"])[0]
            sections.setdefault(tag, []).extend(
                _format_operation(path, method, operation)
            )

    lines = [HEADER]
    for tag in sorted(sections):
        lines.append(f"## {tag}")
        lines.append("")
        lines.extend(sections[tag])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    OUTPUT_PATH.write_text(generate())
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
