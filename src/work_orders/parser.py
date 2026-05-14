import re
from src.work_orders.models import WorkOrder, WorkOrderStatus
from src.work_orders.errors import ParseError


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


class WorkOrderParser:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def parse(self, content: str) -> WorkOrder:
        if not content.strip():
            raise ParseError("Empty work order content")

        match = FRONTMATTER_RE.match(content)
        if not match:
            raise ParseError(
                "Work order must have YAML frontmatter delimited by '---'"
            )

        frontmatter_text = match.group(1)
        body = match.group(2).strip()

        fields = self._parse_frontmatter(frontmatter_text)

        status_raw = fields.get("status", "DRAFT").upper()
        try:
            status = WorkOrderStatus(status_raw)
        except ValueError:
            status = WorkOrderStatus.DRAFT

        allowed_paths_raw = fields.get("allowed_paths", "")
        allowed_paths = (
            [p.strip() for p in allowed_paths_raw.split(",") if p.strip()]
            if allowed_paths_raw else []
        )

        forbidden_paths_raw = fields.get("forbidden_paths", "")
        forbidden_paths = (
            [p.strip() for p in forbidden_paths_raw.split(",") if p.strip()]
            if forbidden_paths_raw else []
        )

        return WorkOrder(
            title=fields.get("title", ""),
            aba=fields.get("aba", ""),
            type=fields.get("type", ""),
            status=status,
            risk=fields.get("risk", "LOW"),
            project=fields.get("project", ""),
            allowed_paths=allowed_paths,
            forbidden_paths=forbidden_paths,
            requires_approval=fields.get("requires_approval", "false").lower()
            in ("true", "yes", "1"),
            dry_run=fields.get("dry_run", "true").lower() in ("true", "yes", "1"),
            description=fields.get("description", ""),
            body=body,
        )

    def _parse_frontmatter(self, text: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        current_key: str | None = None
        current_value: list[str] = []

        for line in text.split("\n"):
            key_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)", line)
            if key_match:
                if current_key is not None:
                    fields[current_key] = "\n".join(current_value).strip()
                current_key = key_match.group(1)
                current_value = [key_match.group(2)]
            elif current_key is not None:
                current_value.append(line)

        if current_key is not None:
            fields[current_key] = "\n".join(current_value).strip()

        return fields

    def parse_file(self, filepath: str) -> WorkOrder:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return self.parse(content)
