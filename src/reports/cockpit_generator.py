"""CockpitGenerator — regenera HTML estático do painel de missões.

Fase F do OMNIS Supreme: cockpit HTML local sem servidor.
Gera: index.html, mission.html, approvals.html, outputs.html, missions_data.js
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


BASE = Path(__file__).resolve().parent.parent.parent
COCKPIT_DIR = BASE / "cockpit"
MISSIONS_ROOT = BASE / "missions"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(path: Path, root: Path = BASE) -> str:
    """Caminho relativo para uso em links HTML."""
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


@dataclass
class MissionMeta:
    """Metadados agregados de uma missão para o cockpit."""
    mission_id: str
    status: str = "unknown"
    setor: str = "general"
    objetivo: str = ""
    criado_por: str = "OMNIS"
    timestamp: str = ""
    closed_at: Optional[str] = None
    outputs_count: int = 0
    exports_count: int = 0
    has_approval_pending: bool = False
    has_report: bool = False
    logs_count: int = 0
    path: str = ""

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "status": self.status,
            "setor": self.setor,
            "objetivo": self.objetivo,
            "criado_por": self.criado_por,
            "timestamp": self.timestamp,
            "closed_at": self.closed_at,
            "outputs_count": self.outputs_count,
            "exports_count": self.exports_count,
            "has_approval_pending": self.has_approval_pending,
            "has_report": self.has_report,
            "logs_count": self.logs_count,
            "path": self.path,
        }


class CockpitGenerator:
    """Gera HTML estático do cockpit a partir do filesystem."""

    def __init__(
        self,
        missions_root: Optional[Path] = None,
        cockpit_dir: Optional[Path] = None,
    ) -> None:
        self.missions_root = Path(missions_root) if missions_root else MISSIONS_ROOT
        self.cockpit_dir = Path(cockpit_dir) if cockpit_dir else COCKPIT_DIR

    def generate_all(self) -> list[Path]:
        """Regenera todos os arquivos do cockpit. Retorna paths gerados."""
        self.cockpit_dir.mkdir(parents=True, exist_ok=True)
        missions = self._scan_missions()
        data_js = self._generate_missions_data_js(missions)
        index_html = self._generate_index_html(missions)
        mission_html = self._generate_mission_html()
        approvals_html = self._generate_approvals_html(missions)
        outputs_html = self._generate_outputs_html(missions)
        css = self._generate_styles_css()

        files: list[Path] = []
        files.append(self._write(self.cockpit_dir / "missions_data.js", data_js))
        files.append(self._write(self.cockpit_dir / "index.html", index_html))
        files.append(self._write(self.cockpit_dir / "mission.html", mission_html))
        files.append(self._write(self.cockpit_dir / "approvals.html", approvals_html))
        files.append(self._write(self.cockpit_dir / "outputs.html", outputs_html))
        files.append(self._write(self.cockpit_dir / "styles.css", css))
        return files

    def _scan_missions(self) -> list[MissionMeta]:
        """Escaneia missions/ e extrai metadados."""
        missions: list[MissionMeta] = []
        if not self.missions_root.exists():
            return missions

        for mission_dir in sorted(self.missions_root.iterdir()):
            if not mission_dir.is_dir():
                continue
            contract_path = mission_dir / "mission_contract.json"
            meta = MissionMeta(mission_id=mission_dir.name, path=_rel(mission_dir))

            if contract_path.exists():
                try:
                    data = json.loads(contract_path.read_text(encoding="utf-8"))
                    meta.status = data.get("status", "unknown")
                    meta.setor = data.get("setor", "general")
                    meta.objetivo = data.get("objetivo", "")
                    meta.criado_por = data.get("criado_por", "OMNIS")
                    meta.timestamp = data.get("timestamp", "")
                    meta.closed_at = data.get("closed_at")
                except (json.JSONDecodeError, KeyError):
                    pass

            outputs_dir = mission_dir / "05_outputs"
            exports_dir = mission_dir / "06_exports"
            approval_dir = mission_dir / "07_approval"
            logs_dir = mission_dir / "08_logs"

            if outputs_dir.exists():
                meta.outputs_count = len(list(f for f in outputs_dir.iterdir() if f.is_file()))
            if exports_dir.exists():
                meta.exports_count = len(list(f for f in exports_dir.iterdir() if f.is_file()))
            if approval_dir.exists():
                approval_files = list(approval_dir.glob("approval_request.md"))
                meta.has_approval_pending = len(approval_files) > 0
            if logs_dir.exists():
                meta.logs_count = len(list(f for f in logs_dir.iterdir() if f.is_file()))

            report_path = mission_dir / "relatorio_final.md"
            meta.has_report = report_path.exists()

            missions.append(meta)

        # Ordenar: abertas primeiro, depois por timestamp decrescente
        missions.sort(
            key=lambda m: (
                m.status != "open",
                m.timestamp or "",
            ),
            reverse=False,
        )
        return missions

    def _generate_missions_data_js(self, missions: list[MissionMeta]) -> str:
        """Gera arquivo JS com todos os dados das missões."""
        data = {
            "generated_at": _now_iso(),
            "missions": [m.to_dict() for m in missions],
        }
        return f"window.MISSIONS_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n"

    # ── Templates HTML ──────────────────────────────────────────────────────

    def _html_head(self, title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — OMNIS Cockpit</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<nav class="topnav">
  <a href="index.html">Missões</a>
  <a href="approvals.html">Aprovações</a>
  <a href="outputs.html">Outputs</a>
  <span class="brand">OMNIS Cockpit</span>
</nav>
<main class="container">
"""

    def _html_foot(self, extra_script: str = "") -> str:
        script_block = f"<script src=\"missions_data.js\"></script>\n{extra_script}" if extra_script else "<script src=\"missions_data.js\"></script>"
        return f"""</main>
<footer class="footer">
  <span>OMNIS Control</span>
  <span id="gen-time">—</span>
</footer>
{script_block}
</body>
</html>
"""

    def _generate_index_html(self, missions: list[MissionMeta]) -> str:
        lines = [
            self._html_head("Missões"),
            "<h1>Missões</h1>",
            "<div class=\"stats\">",
            f"  <div class=\"stat\"><span class=\"stat-num\">{len(missions)}</span><span class=\"stat-label\">Total</span></div>",
            f"  <div class=\"stat\"><span class=\"stat-num\">{sum(1 for m in missions if m.status == 'open')}</span><span class=\"stat-label\">Abertas</span></div>",
            f"  <div class=\"stat\"><span class=\"stat-num\">{sum(1 for m in missions if m.status == 'closed')}</span><span class=\"stat-label\">Fechadas</span></div>",
            f"  <div class=\"stat\"><span class=\"stat-num\">{sum(1 for m in missions if m.has_approval_pending)}</span><span class=\"stat-label\">Pendentes</span></div>",
            "</div>",
            "<table class=\"mission-table\">",
            "  <thead>",
            "    <tr><th>ID</th><th>Status</th><th>Setor</th><th>Objetivo</th><th>Outputs</th><th>Exports</th><th>Aprov.</th><th>Relatório</th></tr>",
            "  </thead>",
            "  <tbody>",
        ]
        for m in missions:
            status_cls = "status-open" if m.status == "open" else "status-closed"
            appr_icon = "&#9888;" if m.has_approval_pending else "&#10003;" if not m.has_approval_pending and m.status == "closed" else "—"
            report_link = f'<a href="../{m.path}/relatorio_final.md" target="_blank">&#128196;</a>' if m.has_report else "—"
            lines.append(
                f'    <tr>'
                f'<td><a href="mission.html?mission={m.mission_id}">{m.mission_id}</a></td>'
                f'<td><span class="badge {status_cls}">{m.status}</span></td>'
                f'<td>{m.setor}</td>'
                f'<td class="objetivo">{self._escape_html(m.objetivo[:80])}{"…" if len(m.objetivo) > 80 else ""}</td>'
                f'<td>{m.outputs_count}</td>'
                f'<td>{m.exports_count}</td>'
                f'<td>{appr_icon}</td>'
                f'<td>{report_link}</td>'
                f'</tr>'
            )
        if not missions:
            lines.append('    <tr><td colspan="8" class="empty">Nenhuma missão encontrada. Execute <code>omnis mission "objetivo"</code> para criar uma.</td></tr>')
        lines.extend([
            "  </tbody>",
            "</table>",
            self._html_foot(),
        ])
        return "\n".join(lines)

    def _generate_mission_html(self) -> str:
        content = self._html_head("Detalhes da Missão") + """
<h1 id="m-title">Missão</h1>
<div class="mission-card" id="m-card">
  <div class="grid-2">
    <div><strong>ID:</strong> <span id="m-id">—</span></div>
    <div><strong>Status:</strong> <span id="m-status">—</span></div>
    <div><strong>Setor:</strong> <span id="m-setor">—</span></div>
    <div><strong>Criado por:</strong> <span id="m-criado">—</span></div>
    <div><strong>Aberto:</strong> <span id="m-aberto">—</span></div>
    <div><strong>Fechado:</strong> <span id="m-fechado">—</span></div>
  </div>
  <div class="block"><strong>Objetivo:</strong> <span id="m-objetivo">—</span></div>
</div>

<h2>Arquivos</h2>
<ul id="m-files" class="file-list"><li>Carregando…</li></ul>
""" + self._html_foot("""
<script>
(function(){
  const params = new URLSearchParams(window.location.search);
  const id = params.get('mission');
  if (!id) { document.getElementById('m-title').textContent = 'Nenhuma missão especificada'; return; }
  document.getElementById('m-title').textContent = id;
  const data = window.MISSIONS_DATA || {missions:[]};
  const m = data.missions.find(x => x.mission_id === id);
  if (!m) { document.getElementById('m-title').textContent = 'Missão não encontrada: ' + id; return; }
  document.getElementById('m-id').textContent = m.mission_id;
  document.getElementById('m-status').textContent = m.status;
  document.getElementById('m-status').className = 'badge ' + (m.status === 'open' ? 'status-open' : 'status-closed');
  document.getElementById('m-setor').textContent = m.setor;
  document.getElementById('m-criado').textContent = m.criado_por;
  document.getElementById('m-aberto').textContent = m.timestamp || '—';
  document.getElementById('m-fechado').textContent = m.closed_at || '—';
  document.getElementById('m-objetivo').textContent = m.objetivo;
  const filesUl = document.getElementById('m-files');
  filesUl.innerHTML = '';
  const base = '../' + m.path + '/';
  const entries = [
    ['mission_contract.json', base + 'mission_contract.json'],
    ['01_mission_brief.md', base + '01_mission_brief.md'],
    ['02_context_used.md', base + '02_context_used.md'],
    ['03_execution_plan.md', base + '03_execution_plan.md'],
    ['04_squad_assigned.md', base + '04_squad_assigned.md'],
    ['09_next_action.md', base + '09_next_action.md'],
    ['10_learnings.md', base + '10_learnings.md'],
    ['relatorio_final.md', base + 'relatorio_final.md'],
  ];
  entries.forEach(([label, url]) => {
    const li = document.createElement('li');
    li.innerHTML = '<a href="' + url + '" target="_blank">' + label + '</a>';
    filesUl.appendChild(li);
  });
  ['05_outputs','06_exports','07_approval','08_logs'].forEach(dir => {
    const li = document.createElement('li');
    li.innerHTML = '<strong>' + dir + '/</strong> — ' + (m[dir.replace('0','').replace('_count','').replace('5','outputs').replace('6','exports').replace('7','').replace('8','logs')] || '0') + ' arquivos';
    filesUl.appendChild(li);
  });
})();
</script>
""")
        return content

    def _generate_approvals_html(self, missions: list[MissionMeta]) -> str:
        pending = [m for m in missions if m.has_approval_pending]
        lines = [
            self._html_head("Aprovações"),
            "<h1>Aprovações Pendentes</h1>",
            f"<p>{len(pending)} missão(ões) aguardando aprovação.</p>",
            "<table class=\"mission-table\">",
            "  <thead>",
            "    <tr><th>Missão</th><th>Setor</th><th>Objetivo</th><th>Ver</th></tr>",
            "  </thead>",
            "  <tbody>",
        ]
        for m in pending:
            lines.append(
                f'    <tr>'
                f'<td>{m.mission_id}</td>'
                f'<td>{m.setor}</td>'
                f'<td class="objetivo">{self._escape_html(m.objetivo[:80])}{"…" if len(m.objetivo) > 80 else ""}</td>'
                f'<td><a href="mission.html?mission={m.mission_id}">Ver</a></td>'
                f'</tr>'
            )
        if not pending:
            lines.append('    <tr><td colspan="4" class="empty">Nenhuma aprovação pendente.</td></tr>')
        lines.extend([
            "  </tbody>",
            "</table>",
            self._html_foot(),
        ])
        return "\n".join(lines)

    def _generate_outputs_html(self, missions: list[MissionMeta]) -> str:
        lines = [
            self._html_head("Outputs & Exports"),
            "<h1>Outputs & Exports</h1>",
            "<table class=\"mission-table\">",
            "  <thead>",
            "    <tr><th>Missão</th><th>Status</th><th>Outputs</th><th>Exports</th><th>Relatório</th></tr>",
            "  </thead>",
            "  <tbody>",
        ]
        has_any = False
        for m in missions:
            if m.outputs_count == 0 and m.exports_count == 0 and not m.has_report:
                continue
            has_any = True
            report_link = f'<a href="../{m.path}/relatorio_final.md" target="_blank">&#128196;</a>' if m.has_report else "—"
            lines.append(
                f'    <tr>'
                f'<td><a href="mission.html?mission={m.mission_id}">{m.mission_id}</a></td>'
                f'<td><span class="badge {"status-open" if m.status == "open" else "status-closed"}">{m.status}</span></td>'
                f'<td>{m.outputs_count}</td>'
                f'<td>{m.exports_count}</td>'
                f'<td>{report_link}</td>'
                f'</tr>'
            )
        if not has_any:
            lines.append('    <tr><td colspan="5" class="empty">Nenhum output ou export encontrado.</td></tr>')
        lines.extend([
            "  </tbody>",
            "</table>",
            self._html_foot(),
        ])
        return "\n".join(lines)

    def _generate_styles_css(self) -> str:
        return """/* OMNIS Cockpit Styles */
:root {
  --bg: #0b0f19;
  --surface: #111827;
  --surface-2: #1f2937;
  --text: #e5e7eb;
  --text-dim: #9ca3af;
  --accent: #22d3ee;
  --accent-2: #a78bfa;
  --success: #34d399;
  --warning: #fbbf24;
  --danger: #f87171;
  --border: #374151;
}
* { box-sizing: border-box; }
body {
  margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg); color: var(--text);
}
.topnav {
  position: sticky; top: 0; z-index: 10;
  display: flex; gap: 1.2rem; align-items: center;
  padding: .6rem 1.2rem;
  background: linear-gradient(90deg, var(--surface), var(--surface-2));
  border-bottom: 1px solid var(--border);
}
.topnav a {
  color: var(--text-dim); text-decoration: none; font-weight: 600; font-size: .9rem;
}
.topnav a:hover { color: var(--accent); }
.brand { margin-left: auto; font-weight: 800; color: var(--accent); letter-spacing: .05em; }
.container { max-width: 1100px; margin: 1.5rem auto; padding: 0 1rem; }
h1 { font-size: 1.6rem; margin: 0 0 1rem; }
.stats {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; margin-bottom: 1.2rem;
}
.stat {
  background: var(--surface); border: 1px solid var(--border); border-radius: .5rem;
  padding: .8rem; text-align: center;
}
.stat-num { display: block; font-size: 1.6rem; font-weight: 800; color: var(--accent); }
.stat-label { font-size: .8rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: .05em; }
.mission-table {
  width: 100%; border-collapse: collapse; font-size: .9rem;
  background: var(--surface); border: 1px solid var(--border); border-radius: .5rem; overflow: hidden;
}
.mission-table thead { background: var(--surface-2); }
.mission-table th, .mission-table td { padding: .55rem .7rem; text-align: left; border-bottom: 1px solid var(--border); }
.mission-table th { color: var(--text-dim); font-weight: 600; font-size: .8rem; text-transform: uppercase; }
.mission-table tbody tr:hover { background: rgba(34,211,238,.06); }
.mission-table a { color: var(--accent); text-decoration: none; }
.mission-table a:hover { text-decoration: underline; }
.objetivo { max-width: 320px; }
.badge { display: inline-block; padding: .15rem .45rem; border-radius: .3rem; font-size: .75rem; font-weight: 700; text-transform: uppercase; }
.status-open { background: rgba(52,211,153,.15); color: var(--success); }
.status-closed { background: rgba(167,139,250,.15); color: var(--accent-2); }
.empty { text-align: center; color: var(--text-dim); padding: 2rem !important; }
.mission-card { background: var(--surface); border: 1px solid var(--border); border-radius: .5rem; padding: 1rem; margin-bottom: 1rem; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: .6rem; }
.block { margin-top: .8rem; }
.file-list { list-style: none; padding: 0; }
.file-list li { padding: .35rem 0; border-bottom: 1px solid var(--border); }
.file-list li:last-child { border-bottom: none; }
.footer { text-align: center; padding: 1.2rem; color: var(--text-dim); font-size: .8rem; border-top: 1px solid var(--border); margin-top: 2rem; }
code { background: var(--surface-2); padding: .15rem .35rem; border-radius: .25rem; font-size: .85rem; }
"""

    def _escape_html(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _write(self, path: Path, content: str) -> Path:
        path.write_text(content, encoding="utf-8")
        return path


def main() -> list[Path]:
    gen = CockpitGenerator()
    return gen.generate_all()


if __name__ == "__main__":
    for p in main():
        print(f"Generated: {p}")
