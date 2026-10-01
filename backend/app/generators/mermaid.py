"""DataModel -> Mermaid erDiagram 텍스트."""
import re

from app.schemas import Cardinality, DesignState

_CARDINALITY = {
    Cardinality.ONE_TO_ONE: "||--o|",
    Cardinality.ONE_TO_MANY: "||--o{",
    Cardinality.MANY_TO_MANY: "}o--o{",
}


def _safe(text: str) -> str:
    return text.replace('"', "'")


def _type(data_type: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", data_type.strip()) or "UNKNOWN"


def generate_mermaid(state: DesignState) -> str:
    lines = ["erDiagram"]
    fk_cols = {(r.from_table, r.fk_column) for r in state.relationships}
    for e in state.entities:
        lines.append(f"    {e.table_name} {{")
        for a in e.attributes:
            keys = []
            if a.is_pk:
                keys.append("PK")
            if (e.table_name, a.name) in fk_cols:
                keys.append("FK")
            if a.is_unique and not a.is_pk:
                keys.append("UK")
            key = f" {','.join(keys)}" if keys else ""
            comment = f' "{_safe(a.logical_name)}"' if a.logical_name else ""
            lines.append(f"        {_type(a.data_type)} {a.name}{key}{comment}")
        lines.append("    }")
    for r in state.relationships:
        lines.append(f'    {r.to_table} {_CARDINALITY[r.cardinality]} {r.from_table} : "{r.fk_column}"')
    return "\n".join(lines) + "\n"
