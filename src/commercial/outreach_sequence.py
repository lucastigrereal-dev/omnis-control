"""W123 — Outreach Sequencer for SDR hotel prospecting.

Cadence D+0, D+2, D+5 across 5 channels. All messages are template-generated,
never sent. Integrates with HotelLead and ProspectList.

Extends legacy src/commercial_sdr/service.py cadence patterns (7-step, ~25 day)
with a simplified 3-step cadence tuned for hotel outreach.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import json
from pathlib import Path

from src.commercial.hotel_lead import HotelLead
from src.commercial.prospect_list import ProspectEntry


# ── Enums ──────────────────────────────────────────────────────────────────

class OutreachChannel(str, Enum):
    WHATSAPP = "whatsapp"
    INSTAGRAM_DM = "instagram_dm"
    EMAIL = "email"
    CALL = "call"
    MANUAL = "manual"


class StepStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    COMPLETED = "completed"
    SKIPPED = "skipped"


CADENCE_DAYS = [0, 2, 5]
CADENCE_LABELS = ["D+0 — Abertura", "D+2 — Reforco", "D+5 — Ultimo contato"]

_SIGNATURE = "Lucas Tigre | @lucastigrereal | OMNIS Commercial SDR"


# ── Outreach Message ───────────────────────────────────────────────────────

@dataclass
class OutreachMessage:
    """Template outreach message — generated, never sent."""

    message_id: str
    step_label: str  # D+0, D+2, D+5
    channel: OutreachChannel
    body: str
    call_to_action: str = ""
    requires_approval: bool = True
    dry_run: bool = True
    sent: bool = False  # Always False — enforced by dry_run
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "step_label": self.step_label,
            "channel": self.channel.value,
            "body": self.body,
            "call_to_action": self.call_to_action,
            "requires_approval": self.requires_approval,
            "dry_run": self.dry_run,
            "sent": self.sent,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutreachMessage":
        return cls(
            message_id=d["message_id"],
            step_label=d.get("step_label", ""),
            channel=OutreachChannel(d.get("channel", "email")),
            body=d.get("body", ""),
            call_to_action=d.get("call_to_action", ""),
            requires_approval=d.get("requires_approval", True),
            dry_run=d.get("dry_run", True),
            sent=d.get("sent", False),
            generated_at=d.get("generated_at", ""),
        )


# ── Outreach Step ──────────────────────────────────────────────────────────

@dataclass
class OutreachStep:
    """Single step in an outreach sequence."""

    step_id: str
    sequence_id: str
    step_number: int  # 1-based
    delay_days: int
    label: str  # D+0, D+2, D+5
    channel: OutreachChannel
    message: OutreachMessage | None = None
    status: StepStatus = StepStatus.PENDING
    completed_at: str = ""
    notes: str = ""
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "sequence_id": self.sequence_id,
            "step_number": self.step_number,
            "delay_days": self.delay_days,
            "label": self.label,
            "channel": self.channel.value,
            "message": self.message.to_dict() if self.message else None,
            "status": self.status.value,
            "completed_at": self.completed_at,
            "notes": self.notes,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutreachStep":
        msg = None
        if d.get("message"):
            msg = OutreachMessage.from_dict(d["message"])
        return cls(
            step_id=d["step_id"],
            sequence_id=d.get("sequence_id", ""),
            step_number=d.get("step_number", 1),
            delay_days=d.get("delay_days", 0),
            label=d.get("label", ""),
            channel=OutreachChannel(d.get("channel", "email")),
            message=msg,
            status=StepStatus(d.get("status", "pending")),
            completed_at=d.get("completed_at", ""),
            notes=d.get("notes", ""),
            dry_run=d.get("dry_run", True),
        )


# ── Message Templates ─────────────────────────────────────────────────────

def _generate_message(
    hotel_lead: HotelLead, channel: OutreachChannel, step_label: str
) -> OutreachMessage:
    """Generate deterministic outreach message for a HotelLead.

    Templates vary by channel and step. All messages require approval.
    Never sent — dry_run enforced.
    """
    import uuid

    hotel = hotel_lead.hotel_name or hotel_lead.name
    city = hotel_lead.city
    state = hotel_lead.state
    niche = hotel_lead.niche
    tier = hotel_lead.hotel_tier

    location = f"{city}/{state}" if city and state else (city or state or "sua regiao")

    is_premium = hotel_lead.is_premium_candidate

    # Template selection by step
    if step_label.startswith("D+0"):
        if channel == OutreachChannel.EMAIL:
            body = (
                f"Ola, equipe do {hotel}!\n\n"
                f"Sou o Lucas Tigre, criador de conteudo de viagem e gastronomia "
                f"com 2.3M+ seguidores em 6 perfis no Instagram.\n\n"
                f"Conheco o {hotel} em {location} e acredito que podemos criar uma "
                f"parceria incrivel no segmento de {niche}.\n\n"
                f"Nossos pacotes comecam em R$350 (Starter) e nosso CPM e 98%% "
                f"menor que Meta Ads.\n\n"
                f"Tem interesse em conversar?\n\n"
                f"Abraco,\n{_SIGNATURE}"
            )
            cta = "Responder este email para agendar call de 15min"
        elif channel == OutreachChannel.INSTAGRAM_DM:
            body = (
                f"Ola! Sou o Lucas Tigre (@lucastigrereal, 690K). "
                f"Acompanho o {hotel} em {location} e adoraria conversar "
                f"sobre parceria de midia no nicho de {niche}. "
                f"Bora trocar ideia?"
            )
            cta = "Responder DM ou chamar no direct"
        elif channel == OutreachChannel.WHATSAPP:
            body = (
                f"Ola! Sou Lucas Tigre, criador de conteudo de viagem "
                f"com 2.3M+ seguidores. Vi o {hotel} em {location} e "
                f"queria apresentar uma proposta de parceria. "
                f"Tem 5min para conversar?"
            )
            cta = "Responder WhatsApp para agendar call"
        elif channel == OutreachChannel.CALL:
            body = (
                f"Roteiro de ligacao — {hotel}:\n"
                f"1. Apresentacao: Lucas Tigre, 2.3M+ seguidores, 6 perfis\n"
                f"2. Contexto: vi o {hotel} em {location}, nicho {niche}\n"
                f"3. Proposta: pacote {tier} — collab + SEO organico\n"
                f"4. CTA: agendar reuniao de 15min para detalhar"
            )
            cta = "Agendar call de follow-up"
        else:  # MANUAL
            body = (
                f"Contato manual — {hotel} ({location})\n"
                f"Segmento: {niche} | Tier: {tier}\n"
                f"Abordagem inicial — apresentar Lucas Tigre e proposta de parceria."
            )
            cta = "Definir proximo passo manualmente"
    elif step_label.startswith("D+2"):
        if channel == OutreachChannel.EMAIL:
            body = (
                f"Ola, equipe do {hotel}!\n\n"
                f"Enviei uma mensagem ha 2 dias sobre parceria de midia. "
                f"Queria reforcar que nosso alcance organico e de 2M+ mensais, "
                f"com audience altamente qualificada para {niche} em {location}.\n\n"
                + (
                    f"Como {hotel} e um parceiro Premium em potencial, "
                    f"preparei um pacote especial.\n\n"
                    if is_premium else ""
                ) +
                f"Posso enviar cases de resultados e um media kit?\n\n"
                f"Abraco,\n{_SIGNATURE}"
            )
            cta = "Solicitar media kit para envio"
        elif channel == OutreachChannel.INSTAGRAM_DM:
            body = (
                f"Ola! So reforcando a mensagem anterior sobre parceria "
                f"com o {hotel}. Nosso publico e super qualificado para "
                f"{niche}. Se tiver interesse, me chama aqui!"
            )
            cta = "Responder DM"
        elif channel == OutreachChannel.WHATSAPP:
            body = (
                f"Ola de novo! Vi que nao conseguiu ver minha mensagem "
                f"anterior sobre parceria com o {hotel}. "
                f"Tem 2min para eu explicar rapidinho?"
            )
            cta = "Responder WhatsApp"
        elif channel == OutreachChannel.CALL:
            body = (
                f"Roteiro 2a tentativa — {hotel}:\n"
                f"1. Referenciar contato anterior (D+0)\n"
                f"2. Reforcar numeros: 2M+ alcance, CPM 98%% menor\n"
                f"3. Mencionar fit com {niche} em {location}\n"
                f"4. CTA: agendar call de 15min"
            )
            cta = "Agendar call de follow-up"
        else:
            body = (
                f"Follow-up manual D+2 — {hotel} ({location})\n"
                f"Reforcar contato inicial, enviar material complementar."
            )
            cta = "Definir proximo passo manualmente"
    else:  # D+5
        if channel == OutreachChannel.EMAIL:
            body = (
                f"Ola, equipe do {hotel}!\n\n"
                f"Sei que a rotina e corrida. Esta e minha ultima mensagem sobre "
                f"parceria de midia com os perfis @lucastigrereal e afiliados.\n\n"
                f"Se fizer sentido, so responder este email. Se nao, obrigado "
                f"pela atencao e sigo acompanhando o trabalho de voces em {location}.\n\n"
                f"Abraco,\n{_SIGNATURE}"
            )
            cta = "Responder com 'tenho interesse' para follow-up prioritario"
        elif channel == OutreachChannel.INSTAGRAM_DM:
            body = (
                f"Ultima mensagem! Se algum dia fizer sentido parceria "
                f"entre o {hotel} e meus perfis (2.3M+ seguidores), "
                f"so chamar. Abraco!"
            )
            cta = "Porta sempre aberta — sem pressao"
        elif channel == OutreachChannel.WHATSAPP:
            body = (
                f"Ultima tentativa! Se o {hotel} tiver interesse em "
                f"parceria de midia no futuro, estou a disposicao. "
                f"Meus perfis tem 2.3M+ seguidores no nicho de viagem. Abraco!"
            )
            cta = "Salvar contato para futuro"
        elif channel == OutreachChannel.CALL:
            body = (
                f"Roteiro ultima tentativa — {hotel}:\n"
                f"1. Tom leve, sem pressao\n"
                f"2. Reforcar: porta aberta para parceria futura\n"
                f"3. Deixar contato: @lucastigrereal\n"
                f"4. Agradecer e encerrar ciclo"
            )
            cta = "Encerrar ciclo, manter no pipeline frio"
        else:
            body = (
                f"Ultimo contato manual D+5 — {hotel} ({location})\n"
                f"Encerrar ciclo. Manter no radar para futuro."
            )
            cta = "Mover para lista fria, revisitar em 90 dias"

    return OutreachMessage(
        message_id=str(uuid.uuid4())[:12],
        step_label=step_label,
        channel=channel,
        body=body,
        call_to_action=cta,
        requires_approval=True,
        dry_run=True,
    )


# ── Outreach Sequence ──────────────────────────────────────────────────────

@dataclass
class OutreachSequence:
    """Complete outreach sequence for a single HotelLead prospect.

    3-step cadence: D+0 (abertura), D+2 (reforco), D+5 (ultimo contato).
    All steps are dry-run — messages are generated but never sent.
    """

    sequence_id: str
    hotel_lead_id: str
    hotel_name: str = ""
    channel: OutreachChannel = OutreachChannel.EMAIL
    steps: list[OutreachStep] = field(default_factory=list)
    status: str = "draft"  # draft, active, completed, cancelled
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)

    @property
    def pending_steps(self) -> int:
        return sum(1 for s in self.steps if s.status in (StepStatus.PENDING, StepStatus.READY))

    @property
    def next_action(self) -> OutreachStep | None:
        """Return the next pending step, or None if all complete."""
        for step in self.steps:
            if step.status in (StepStatus.PENDING, StepStatus.READY):
                return step
        return None

    @property
    def next_action_date(self) -> str:
        """Estimated date for next action based on delay_days from creation."""
        step = self.next_action
        if not step:
            return ""
        base = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        target = base + timedelta(days=step.delay_days)
        return target.isoformat()

    def complete_step(self, step_number: int) -> bool:
        """Mark a step as completed by its 1-based step_number."""
        for step in self.steps:
            if step.step_number == step_number:
                if step.status == StepStatus.COMPLETED:
                    return False
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc).isoformat()
                self.updated_at = datetime.now(timezone.utc).isoformat()
                if self.pending_steps == 0:
                    self.status = "completed"
                return True
        return False

    def skip_step(self, step_number: int) -> bool:
        """Skip a step by its 1-based step_number."""
        for step in self.steps:
            if step.step_number == step_number:
                if step.status == StepStatus.COMPLETED:
                    return False
                step.status = StepStatus.SKIPPED
                self.updated_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def cancel(self) -> None:
        """Cancel the entire sequence."""
        self.status = "cancelled"
        for step in self.steps:
            if step.status not in (StepStatus.COMPLETED, StepStatus.SKIPPED):
                step.status = StepStatus.SKIPPED
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "sequence_id": self.sequence_id,
            "hotel_lead_id": self.hotel_lead_id,
            "hotel_name": self.hotel_name,
            "channel": self.channel.value,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutreachSequence":
        steps = [OutreachStep.from_dict(s) for s in d.get("steps", [])]
        return cls(
            sequence_id=d["sequence_id"],
            hotel_lead_id=d.get("hotel_lead_id", ""),
            hotel_name=d.get("hotel_name", ""),
            channel=OutreachChannel(d.get("channel", "email")),
            steps=steps,
            status=d.get("status", "draft"),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )

    def to_markdown(self) -> str:
        lines = [
            f"# Outreach Sequence: {self.hotel_name or self.hotel_lead_id}",
            f"**ID:** {self.sequence_id}",
            f"**Channel:** {self.channel.value}",
            f"**Status:** {self.status} | **Steps:** {self.completed_steps}/{self.total_steps} complete",
            f"**Next Action:** {self.next_action.label if self.next_action else '—'}",
            f"**Next Date:** {self.next_action_date or '—'}",
            f"**dry_run:** {self.dry_run}",
            "",
            "## Steps",
            "",
        ]
        for step in self.steps:
            status_icon = {StepStatus.PENDING: "○", StepStatus.READY: "◐",
                           StepStatus.COMPLETED: "●", StepStatus.SKIPPED: "✕"}.get(step.status, "?")
            lines.append(
                f"### {status_icon} Step {step.step_number}: {step.label}"
            )
            lines.append(f"**Channel:** {step.channel.value} | **Delay:** {step.delay_days}d | **Status:** {step.status.value}")
            if step.message:
                lines.append(f"**CTA:** {step.message.call_to_action}")
                lines.append("")
                lines.append(step.message.body.replace("\n", "\n> "))
                lines.append("")
        return "\n".join(lines)


# ── Outreach Sequencer ─────────────────────────────────────────────────────

class OutreachSequencer:
    """Generates and manages outreach sequences for HotelLead prospects.

    Integrates with ProspectList for batch operations.
    File-backed optional persistence.
    """

    def __init__(self, storage_dir: str | Path | None = None,
                 default_channel: OutreachChannel = OutreachChannel.EMAIL):
        self._sequences: dict[str, OutreachSequence] = {}
        self._storage_dir = Path(storage_dir) if storage_dir else None
        self.default_channel = default_channel

    @property
    def count(self) -> int:
        return len(self._sequences)

    @property
    def active_count(self) -> int:
        return sum(1 for s in self._sequences.values() if s.status == "active")

    @property
    def completed_count(self) -> int:
        return sum(1 for s in self._sequences.values() if s.status == "completed")

    # ── Sequence Generation ────────────────────────────────────────────────

    def generate_sequence(
        self, hotel_lead: HotelLead, channel: OutreachChannel | None = None
    ) -> OutreachSequence:
        """Build a 3-step outreach sequence (D+0, D+2, D+5) for a HotelLead.

        Args:
            hotel_lead: The HotelLead to build sequence for
            channel: Channel override (defaults to sequencer's default_channel)

        Returns:
            OutreachSequence with 3 generated steps, all dry_run
        """
        import uuid

        ch = channel or self.default_channel
        seq_id = str(uuid.uuid4())[:12]

        seq = OutreachSequence(
            sequence_id=seq_id,
            hotel_lead_id=hotel_lead.hotel_lead_id,
            hotel_name=hotel_lead.hotel_name or hotel_lead.name,
            channel=ch,
            status="active",
        )

        steps = []
        for i, (delay, label) in enumerate(zip(CADENCE_DAYS, CADENCE_LABELS), start=1):
            msg = _generate_message(hotel_lead, ch, label)
            step = OutreachStep(
                step_id=str(uuid.uuid4())[:12],
                sequence_id=seq_id,
                step_number=i,
                delay_days=delay,
                label=label,
                channel=ch,
                message=msg,
                status=StepStatus.READY if i == 1 else StepStatus.PENDING,
                dry_run=True,
            )
            steps.append(step)

        seq.steps = steps
        self._sequences[seq.sequence_id] = seq
        if self._storage_dir:
            self._flush()
        return seq

    def generate_for_prospect_list(
        self, prospect_list: "ProspectList", channel: OutreachChannel | None = None
    ) -> list[OutreachSequence]:
        """Generate sequences for all pursuable entries in a ProspectList."""
        results = []
        for entry in prospect_list.filter_pursuable():
            seq = self.generate_sequence(entry.hotel_lead, channel)
            results.append(seq)
        return results

    def generate_for_hot_list(
        self, prospect_list: "ProspectList", channel: OutreachChannel | None = None
    ) -> list[OutreachSequence]:
        """Generate sequences only for hot-priority entries."""
        results = []
        for entry in prospect_list.hot_list():
            seq = self.generate_sequence(entry.hotel_lead, channel)
            results.append(seq)
        return results

    # ── Sequence Management ────────────────────────────────────────────────

    def get(self, sequence_id: str) -> OutreachSequence | None:
        return self._sequences.get(sequence_id)

    def list_all(self) -> list[OutreachSequence]:
        return list(self._sequences.values())

    def list_active(self) -> list[OutreachSequence]:
        return [s for s in self._sequences.values() if s.status == "active"]

    def list_by_hotel_lead(self, hotel_lead_id: str) -> list[OutreachSequence]:
        return [s for s in self._sequences.values() if s.hotel_lead_id == hotel_lead_id]

    def list_due_actions(self) -> list[OutreachStep]:
        """Return all steps that are ready and should be actioned."""
        due = []
        for seq in self._sequences.values():
            if seq.status != "active":
                continue
            na = seq.next_action
            if na and na.status == StepStatus.READY:
                due.append(na)
        return due

    # ── Batch Operations ───────────────────────────────────────────────────

    def advance_all_ready(self) -> int:
        """Advance one step per active sequence: complete READY step, activate next PENDING.

        Returns count of sequences advanced.
        """
        count = 0
        for seq in self._sequences.values():
            if seq.status != "active":
                continue
            na = seq.next_action
            if na and na.status == StepStatus.READY:
                seq.complete_step(na.step_number)
                count += 1
                idx = na.step_number - 1
                if idx + 1 < len(seq.steps):
                    next_step = seq.steps[idx + 1]
                    if next_step.status == StepStatus.PENDING:
                        next_step.status = StepStatus.READY
        if self._storage_dir:
            self._flush()
        return count

    # ── Persistence ────────────────────────────────────────────────────────

    def to_jsonl(self) -> str:
        return "\n".join(
            json.dumps(s.to_dict(), ensure_ascii=False) for s in self._sequences.values()
        )

    def _flush(self) -> None:
        if not self._storage_dir:
            return
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        path = self._storage_dir / "outreach_sequences.jsonl"
        path.write_text(self.to_jsonl() + "\n", encoding="utf-8")

    @classmethod
    def load(cls, storage_dir: str | Path) -> "OutreachSequencer":
        seqr = cls(storage_dir)
        path = Path(storage_dir) / "outreach_sequences.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").strip().split("\n"):
                if line.strip():
                    d = json.loads(line)
                    seq = OutreachSequence.from_dict(d)
                    seqr._sequences[seq.sequence_id] = seq
        return seqr
