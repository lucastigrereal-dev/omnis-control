"""P9 Commercial SDR service — planner, scoring, sequences, messages."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.commercial_sdr.models import (
    ProspectProfile,
    LeadSource,
    OutreachChannel,
    StepAction,
    ScoreTier,
    SDRMessage,
    OutreachStep,
    OutreachSequence,
    OpportunityScore,
    SDRPlan,
)
from src.commercial_sdr.errors import (
    EmptyProspectListError,
    InvalidScoreParameterError,
    InvalidChannelError,
    MessageTemplateError,
    ValidationError,
    PlanFinalizedError,
)


# ── Scoring ──────────────────────────────────────────────────────────────────

def score_prospect(prospect: ProspectProfile) -> OpportunityScore:
    """Calcula score deterministico de oportunidade para um prospect.

    Heuristicas:
    - segment_fit: baseado no segmento do prospect
    - engagement_signal: presenca de instagram/email/phone
    - budget_indicator: baseado na source do lead
    - urgency: baseado em sinais de engajamento
    """
    reasoning: list[str] = []

    # segment_fit — segmentos de viagem/gastronomia tem fit maximo
    high_fit_segments = {"hotel", "resort", "pousada", "restaurante", "gastronomia",
                         "turismo", "viagem", "agencia"}
    medium_fit_segments = {"evento", "experiencia", "guia", "transporte"}
    seg = prospect.segment.lower()
    if seg in high_fit_segments:
        segment_fit = 0.90
        reasoning.append(f"Segmento '{prospect.segment}' — alto fit com midia de viagem")
    elif seg in medium_fit_segments:
        segment_fit = 0.55
        reasoning.append(f"Segmento '{prospect.segment}' — fit medio")
    else:
        segment_fit = 0.25
        reasoning.append(f"Segmento '{prospect.segment}' — fit baixo, requer analise")

    # engagement_signal — quantos canais de contato existem
    signals = sum([bool(prospect.instagram_handle), bool(prospect.email),
                   bool(prospect.phone), bool(prospect.website)])
    if signals >= 3:
        engagement_signal = 0.85
        reasoning.append(f"Multi-canal ({signals} canais) — forte sinal de presenca")
    elif signals == 2:
        engagement_signal = 0.55
        reasoning.append(f"Bi-canal ({signals} canais) — engajamento medio")
    elif signals == 1:
        engagement_signal = 0.30
        reasoning.append(f"Mono-canal ({signals} canais) — engajamento baixo")
    else:
        engagement_signal = 0.05
        reasoning.append("Zero canais — prospect sem presenca digital detectavel")

    # budget_indicator — baseado na source do lead
    source_budget_map = {
        LeadSource.REFERRAL: 0.80,
        LeadSource.INBOUND: 0.75,
        LeadSource.PARTNERSHIP: 0.65,
        LeadSource.INSTAGRAM: 0.50,
        LeadSource.EVENT: 0.45,
        LeadSource.MANUAL_RESEARCH: 0.30,
    }
    budget_indicator = source_budget_map.get(prospect.source, 0.30)
    reasoning.append(f"Source '{prospect.source.value}' — budget indicator {budget_indicator:.2f}")

    # urgency — baseado em sinais indiretos (tags, notes, website)
    urgency = 0.30
    urgency_keywords = ["urgente", "agora", "quente", "hoje", "rapido", "procura", "busca"]
    combined_text = f"{' '.join(prospect.tags)} {prospect.notes}".lower()
    if any(kw in combined_text for kw in urgency_keywords):
        urgency = 0.75
        reasoning.append("Tags/notes indicam urgencia — prospect ativo")
    elif prospect.website:
        urgency = 0.45
        reasoning.append("Website presente — urgencia moderada")
    else:
        reasoning.append("Sem sinais de urgencia detectados")

    return OpportunityScore.new(
        profile_id=prospect.profile_id,
        segment_fit=segment_fit,
        engagement_signal=engagement_signal,
        budget_indicator=budget_indicator,
        urgency=urgency,
        reasoning=reasoning,
    )


# ── Message Generation ───────────────────────────────────────────────────────

_SIGNATURE = "Lucas Tigre | @lucastigrereal | JARVIS Commercial SDR"


def generate_sdr_message(
    profile: ProspectProfile,
    channel: OutreachChannel,
    step_action: StepAction,
) -> SDRMessage:
    """Gera mensagem SDR deterministica baseada no canal e acao.

    Canais de alto risco (instagram_dm, whatsapp, phone) sempre requerem aprovacao.
    Nenhuma mensagem e enviada — apenas template gerado.
    """
    company = profile.company_name
    contact = profile.contact_name
    segment = profile.segment

    templates: dict[tuple[OutreachChannel, StepAction], tuple[str, str, str]] = {
        (OutreachChannel.EMAIL, StepAction.INTRO_MESSAGE): (
            f"{company} x @lucastigrereal — parceria de midia",
            (
                f"Ola {contact},\n\n"
                f"Sou o Lucas Tigre, criador de conteudo de viagem e gastronomia "
                f"com 690K seguidores no Instagram.\n\n"
                f"Conheco o {company} e acredito que podemos criar uma parceria "
                f"incrivel no segmento de {segment}.\n\n"
                f"Tem interesse em conversar?\n\n"
                f"Abraco,\n{_SIGNATURE}"
            ),
            "Responder este email para agendar call de 15min",
        ),
        (OutreachChannel.EMAIL, StepAction.VALUE_OFFER): (
            f"Oportunidade para {company} — 690K seguidores qualificados",
            (
                f"Ola {contact},\n\n"
                f"Enviei uma mensagem anterior sobre parceria. Queria reforcar "
                f"que nosso publico e altamente qualificado para {segment} — "
                f"alcance organico de 2M+ mensais com CPM 98%% menor que Meta Ads.\n\n"
                f"Posso enviar um media kit e cases de resultados?\n\n"
                f"Abraco,\n{_SIGNATURE}"
            ),
            "Solicitar media kit para envio",
        ),
        (OutreachChannel.EMAIL, StepAction.FOLLOW_UP): (
            f"Re: {company} — ultima tentativa de contato",
            (
                f"Ola {contact},\n\n"
                f"Sei que a rotina e corrida. Esta e minha ultima mensagem sobre "
                f"parceria de midia com o perfil @lucastigrereal.\n\n"
                f"Se fizer sentido, so responder este email. Se nao, obrigado "
                f"pela atencao e sigo acompanhando o trabalho de voces.\n\n"
                f"Abraco,\n{_SIGNATURE}"
            ),
            "Responder com 'tenho interesse' para follow-up prioritario",
        ),
        (OutreachChannel.EMAIL, StepAction.PROPOSAL): (
            f"Proposta comercial — {company} x Lucas Tigre",
            (
                f"Ola {contact},\n\n"
                f"Conforme conversamos, segue proposta para parceria:\n\n"
                f"Pacote Growth — R$990/mes\n"
                f"- 3 collabs mensais\n"
                f"- 3 paginas Instagram (690K+450K+320K)\n"
                f"- SEO organico incluso\n\n"
                f"Contrato de 3 meses com resultado garantido ou reembolso.\n\n"
                f"Abraco,\n{_SIGNATURE}"
            ),
            "Assinar contrato digital — link enviado separadamente",
        ),
        (OutreachChannel.INSTAGRAM_DM, StepAction.INTRO_MESSAGE): (
            f"Parceria {company}",
            (
                f"Ola {contact}! Sou o Lucas Tigre (@lucastigrereal). Acompanho o {company} e "
                f"adoraria conversar sobre parceria. Meu perfil tem 690K seguidores "
                f"no nicho de {segment}. Bora trocar ideia?"
            ),
            "Responder DM ou chamar no direct",
        ),
        (OutreachChannel.INSTAGRAM_DM, StepAction.FOLLOW_UP): (
            f"Re: parceria",
            (
                f"Ola {contact}! So reforcando a mensagem anterior. "
                f"Se tiver interesse, me chama aqui. Abraco!"
            ),
            "Responder DM",
        ),
    }

    key = (channel, step_action)
    if key not in templates:
        subject = f"Contato {company} — @lucastigrereal"
        body = (
            f"Ola {contact},\n\n"
            f"Entro em contato para apresentar oportunidades de parceria "
            f"de midia no segmento de {segment}.\n\n"
            f"Abraco,\n{_SIGNATURE}"
        )
        cta = "Responder para agendar conversa"

        high_risk_channels = {OutreachChannel.INSTAGRAM_DM, OutreachChannel.WHATSAPP,
                              OutreachChannel.PHONE, OutreachChannel.LINKEDIN}
        if channel in high_risk_channels:
            body = (
                f"Ola {contact}! Sou o Lucas Tigre. Parceria {segment}? "
                f"Meu perfil: @lucastigrereal (690K). Chama ai!"
            )
            cta = "Responder direct"
    else:
        subject, body, cta = templates[key]

    high_risk_channels = {OutreachChannel.INSTAGRAM_DM, OutreachChannel.WHATSAPP,
                          OutreachChannel.PHONE, OutreachChannel.LINKEDIN}
    requires_approval = channel in high_risk_channels or step_action == StepAction.PROPOSAL

    return SDRMessage.new(
        profile_id=profile.profile_id,
        channel=channel,
        subject=subject,
        body=body,
        call_to_action=cta,
        approval_required=requires_approval,
    )


# ── Sequence Building ────────────────────────────────────────────────────────

_DEFAULT_CADENCE: list[tuple[StepAction, OutreachChannel, int]] = [
    (StepAction.RESEARCH, OutreachChannel.EMAIL, 0),
    (StepAction.CONNECT, OutreachChannel.EMAIL, 0),
    (StepAction.INTRO_MESSAGE, OutreachChannel.EMAIL, 0),
    (StepAction.VALUE_OFFER, OutreachChannel.EMAIL, 3),
    (StepAction.FOLLOW_UP, OutreachChannel.EMAIL, 5),
    (StepAction.PROPOSAL, OutreachChannel.EMAIL, 7),
    (StepAction.CLOSE_ASK, OutreachChannel.EMAIL, 10),
]


def build_outreach_sequence(profile: ProspectProfile) -> OutreachSequence:
    """Constroi sequencia completa de outreach para um prospect.

    Gera 7 passos deterministicos com intervalo total de ~25 dias.
    Todos os passos sao dry-run — nenhum envio real.
    """
    seq = OutreachSequence.new(profile.profile_id)

    steps: list[OutreachStep] = []
    for i, (action, channel, delay) in enumerate(_DEFAULT_CADENCE, start=1):
        msg = generate_sdr_message(profile, channel, action)
        step = OutreachStep.new(
            sequence_id=seq.sequence_id,
            step_number=i,
            action=action,
            channel=channel,
            message=msg,
            delay_days=delay,
            requires_approval=msg.approval_required,
            notes=f"Passo {i}/7 — {action.value} via {channel.value}",
        )
        steps.append(step)

    seq.steps = steps
    seq.status = "ready"
    return seq


def validate_sequence(sequence: OutreachSequence) -> list[str]:
    """Valida sequencia de outreach e retorna lista de warnings.

    Regras:
    - Nenhum step pode ter SDRMessage.sent = True (violaria dry-run)
    - Passos de alto risco precisam de approval_required = True
    - Sequencia nao pode ter passos com delay negativo
    - Sequencia nao pode exceder 30 dias total
    """
    warnings: list[str] = []

    if sequence.dry_run:
        for step in sequence.steps:
            if step.message and step.message.sent:
                warnings.append(
                    f"Step {step.step_number}: mensagem marcada como enviada "
                    f"em modo dry-run — isso e bloqueado"
                )

    high_risk_channels = {OutreachChannel.INSTAGRAM_DM, OutreachChannel.WHATSAPP,
                          OutreachChannel.PHONE}
    for step in sequence.steps:
        if step.channel in high_risk_channels and not step.requires_approval:
            warnings.append(
                f"Step {step.step_number}: canal {step.channel.value} de alto risco "
                f"sem flag de aprovacao"
            )

    for step in sequence.steps:
        if step.delay_days < 0:
            warnings.append(f"Step {step.step_number}: delay negativo ({step.delay_days}d)")

    total_days = sequence.total_delay_days
    if total_days > 30:
        warnings.append(f"Sequencia excede 30 dias (total={total_days}d)")

    return warnings


# ── SDR Planner ──────────────────────────────────────────────────────────────

@dataclass
class CommercialSDRPlanner:
    """Planejador deterministico de operacoes SDR — read-only, dry-run."""

    dry_run: bool = True
    risk_flags: list[str] = field(default_factory=lambda: [
        "no_real_delivery",
        "approval_required_for_external_send",
        "mass_outreach_flagged",
    ])

    def build_sdr_plan(
        self,
        title: str,
        description: str,
        prospects: list[ProspectProfile],
    ) -> SDRPlan:
        """Constroi plano SDR completo: scoring → sequence → validacao.

        Args:
            title: Titulo do plano
            description: Descricao do plano
            prospects: Lista de prospects (min 1)

        Returns:
            SDRPlan com scores, sequencias e flags de seguranca

        Raises:
            EmptyProspectListError: se lista de prospects vazia
        """
        if not prospects:
            raise EmptyProspectListError("Lista de prospects nao pode ser vazia")

        plan = SDRPlan.new(title, description)

        for prospect in prospects:
            plan.add_prospect(prospect)

            score = score_prospect(prospect)
            plan.add_score(score)

            if score.is_pursuable:
                sequence = build_outreach_sequence(prospect)
                plan.add_sequence(sequence)

        plan.finalize()
        return plan


# ── Convenience functions ────────────────────────────────────────────────────

def build_batch_plan(
    title: str,
    description: str,
    prospects: list[ProspectProfile],
) -> SDRPlan:
    """Funcao de conveniencia: constroi plano SDR para lote de prospects."""
    planner = CommercialSDRPlanner()
    return planner.build_sdr_plan(title, description, prospects)
