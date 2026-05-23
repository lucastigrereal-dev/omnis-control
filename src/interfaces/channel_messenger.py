"""ChannelMessenger — contrato Protocol para dispatch outbound multi-canal.

Foco: dado um conteúdo, enviar via WhatsApp e/ou Telegram.
Diferente dos adapters em remote_control/ (inbound commands), este Protocol
é sobre OUTBOUND — relatórios de pesquisa, notificações, alerts, conteúdo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class MessageSpec:
    """Especificação de uma mensagem outbound multi-canal."""

    content: str
    """Corpo da mensagem (texto)."""

    channels: list[str] = field(default_factory=lambda: ["all"])
    """Canais destino: ["whatsapp"], ["telegram"], ["all"], ou combinação."""

    recipient: str = ""
    """Destinatário: número de telefone (WhatsApp) ou chat_id (Telegram).
    Se vazio, usa variável de ambiente padrão do canal."""

    subject: str = ""
    """Título/assunto opcional — usado como preview em alguns canais."""

    parse_mode: str = "text"
    """Formato do conteúdo: "text" ou "markdown"."""

    dry_run: bool = True
    """Se True: simula o envio sem chamar a API real."""

    extra: dict = field(default_factory=dict)


@dataclass
class ChannelDelivery:
    """Resultado de entrega em um único canal."""

    channel: str
    success: bool
    message_id: str = ""
    error: str | None = None


@dataclass
class MessageResult:
    """Resultado agregado de um dispatch multi-canal."""

    success: bool
    """True se ao menos 1 canal foi entregue com sucesso."""

    deliveries: list[ChannelDelivery] = field(default_factory=list)
    dry_run: bool = True
    error: str | None = None
    artifacts: dict = field(default_factory=dict)

    @property
    def delivered_count(self) -> int:
        return sum(1 for d in self.deliveries if d.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for d in self.deliveries if not d.success)


@runtime_checkable
class ChannelMessenger(Protocol):
    """Contrato Protocol para dispatch outbound multi-canal."""

    def send(self, spec: MessageSpec) -> MessageResult:
        """Envia mensagem para os canais especificados em spec.channels."""
        ...

    def health_check(self) -> bool:
        """Retorna True se ao menos um canal está configurado."""
        ...
