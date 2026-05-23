"""LegoRegistry — catálogo dos Legos externos OMNIS.

Permite registrar implementações de Protocol, inspecionar saúde de todos
e servir como ponto de descoberta único para o runtime.
"""
from __future__ import annotations

import logging
from typing import Any

_logger = logging.getLogger("omnis.legos.registry")

_KNOWN_LEGO_NAMES = frozenset({
    "browser_executor",
    "code_executor",
    "video_processor",
    "research_conductor",
    "channel_messenger",
})


class LegoRegistry:
    """Catálogo em memória dos Legos OMNIS.

    Uso:
        reg = LegoRegistry()
        reg.register("browser_executor", BrowserExecutorLego())
        reg.health_check_all()  # → {"browser_executor": True, ...}
    """

    def __init__(self) -> None:
        self._legos: dict[str, Any] = {}

    def register(self, name: str, lego: Any) -> None:
        """Registra um lego pelo nome canônico."""
        if name not in _KNOWN_LEGO_NAMES:
            _logger.warning("[registry] Unknown lego name: %s — registering anyway", name)
        self._legos[name] = lego
        _logger.info("[registry] Registered lego: %s", name)

    def get(self, name: str) -> Any:
        """Retorna lego registrado ou None se não encontrado."""
        lego = self._legos.get(name)
        if lego is None:
            _logger.warning("[registry] Lego not found: %s", name)
        return lego

    def list_available(self) -> list[str]:
        """Lista nomes dos legos registrados, em ordem."""
        return sorted(self._legos.keys())

    def health_check_all(self) -> dict[str, bool]:
        """Executa health_check() em cada lego registrado.

        Se um lego lançar exceção, registra False sem propagar.
        """
        results: dict[str, bool] = {}
        for name, lego in self._legos.items():
            try:
                results[name] = bool(lego.health_check())
            except Exception as exc:
                _logger.error("[registry] health_check failed for %s: %s", name, exc)
                results[name] = False
        return results

    def __len__(self) -> int:
        return len(self._legos)

    def __contains__(self, name: object) -> bool:
        return name in self._legos


def default_registry() -> LegoRegistry:
    """Cria o registry padrão com os 5 legos instanciados com defaults.

    Legos são criados sem credenciais reais — health_check() refletirá
    quais canais estão configurados via variáveis de ambiente.
    """
    from src.legos.browser_executor_lego import BrowserExecutorLego
    from src.legos.code_executor_lego import CodeExecutorLego
    from src.legos.video_processor_lego import VideoProcessorLego
    from src.legos.research_conductor_lego import ResearchConductorLego
    from src.legos.channel_messenger_lego import ChannelMessengerLego

    reg = LegoRegistry()
    reg.register("browser_executor", BrowserExecutorLego())
    reg.register("code_executor", CodeExecutorLego())
    reg.register("video_processor", VideoProcessorLego())
    reg.register("research_conductor", ResearchConductorLego())
    reg.register("channel_messenger", ChannelMessengerLego())
    return reg
