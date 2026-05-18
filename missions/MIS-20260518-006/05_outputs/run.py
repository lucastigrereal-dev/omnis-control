"""pricing-calculator — Calculadora de preço de publi Instagram (OMNIS Forge).

Deterministic pricing engine. Zero LLM. Zero network. Zero database. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

NICHE_MULTIPLIERS: dict[str, float] = {
    "turismo": 1.00,
    "gastronomia": 0.90,
    "familia": 0.85,
}

FORMAT_MULTIPLIERS: dict[str, float] = {
    "reel": 1.20,
    "carrossel": 1.15,
    "collab": 1.00,
    "story": 0.70,
}

PACKAGE_CONFIG: dict[str, dict[str, Any]] = {
    "starter": {"discount_multiplier": 1.00, "default_collabs": 1, "label": "Starter"},
    "growth": {"discount_multiplier": 0.85, "default_collabs": 3, "label": "Growth"},
    "premium": {"discount_multiplier": 0.75, "default_collabs": 4, "label": "Premium"},
}

BASE_ENGAGEMENT_RATE = 3.0  # reference engagement rate for multiplier = 1.0
ENGAGEMENT_FLOOR = 0.8
ENGAGEMENT_CEILING = 1.5
BASE_PRICE_SCALE = 20.0  # (alcance_medio / 1000) * eng_mult * SCALE = base_price
DEFAULT_META_CPM = 15.0  # R$ 15.00 CPM Meta Ads reference
MIN_PRICE_BRL = 150.0  # piso operacional

VALID_NICHES = set(NICHE_MULTIPLIERS.keys())
VALID_FORMATS = set(FORMAT_MULTIPLIERS.keys())
VALID_PACKAGES = set(PACKAGE_CONFIG.keys())


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _clamp(value: float, floor: float, ceiling: float) -> float:
    """Clamp value between floor and ceiling."""
    return max(floor, min(value, ceiling))


def _round_brl(value: float) -> float:
    """Round to nearest integer (R$)."""
    return round(value, 0)


def _validate_input(
    seguidores: int,
    alcance_medio: int,
    engagement_rate: float,
    nicho: str,
    formato: str,
    pacote: str,
) -> list[str]:
    """Validate input parameters. Returns list of error messages (empty = valid)."""
    errors: list[str] = []

    if seguidores < 1000:
        errors.append(f"seguidores ({seguidores}) must be >= 1000.")
    if alcance_medio < 100:
        errors.append(f"alcance_medio ({alcance_medio}) must be >= 100.")
    if engagement_rate <= 0 or engagement_rate > 50:
        errors.append(f"engagement_rate ({engagement_rate}) must be 0.1–50.0%.")
    if nicho not in VALID_NICHES:
        errors.append(f"nicho '{nicho}' invalido. Validos: {sorted(VALID_NICHES)}.")
    if formato not in VALID_FORMATS:
        errors.append(f"formato '{formato}' invalido. Validos: {sorted(VALID_FORMATS)}.")
    if pacote not in VALID_PACKAGES:
        errors.append(f"pacote '{pacote}' invalido. Validos: {sorted(VALID_PACKAGES)}.")

    return errors


# ═══════════════════════════════════════════════════════════════
# PubliPriceCalculator
# ═══════════════════════════════════════════════════════════════

class PubliPriceCalculator:
    """Calculadora inteligente de preco de publi para Instagram.

    Formula de precificacao:
      preco_base = (alcance_medio / 1000) * engagement_multiplier * BASE_PRICE_SCALE
      preco_unitario = preco_base * mult_nicho * mult_formato * mult_pacote
      preco_unitario = max(preco_unitario, MIN_PRICE_BRL)

    CPM Comparison:
      cpm_omnis = (preco_unitario / alcance_medio) * 1000
      economia_pct = (1 - cpm_omnis / meta_cpm) * 100
    """

    def __init__(self, dry_run: bool = True):
        """Initialize calculator. dry_run=True means no side effects."""
        self.dry_run = dry_run

    # ── Core calculation ───────────────────────────────────────

    def calculate_price(
        self,
        seguidores: int,
        alcance_medio: int,
        engagement_rate: float,
        nicho: str,
        formato: str,
        pacote: str,
        num_collabs: int | None = None,
        meta_cpm: float = DEFAULT_META_CPM,
    ) -> dict[str, Any]:
        """Calculate publi price with full breakdown.

        Args:
            seguidores: Total follower count.
            alcance_medio: Average reach per post (impressions).
            engagement_rate: Engagement rate in % (e.g. 4.2 for 4.2%).
            nicho: Profile niche (turismo | gastronomia | familia).
            formato: Content format (reel | carrossel | collab | story).
            pacote: Package type (starter | growth | premium).
            num_collabs: Override default collab count for package (optional).
            meta_cpm: Meta Ads CPM reference in R$ (default 15.0).

        Returns:
            Dict with input, pricing, cpm_comparison, and proposta keys.
        """
        # Validate
        errors = _validate_input(seguidores, alcance_medio, engagement_rate, nicho, formato, pacote)
        if errors:
            return {"error": True, "messages": errors, "input": self._input_dict(
                seguidores, alcance_medio, engagement_rate, nicho, formato, pacote, num_collabs, meta_cpm
            )}

        # Resolve collab count
        pkg_cfg = PACKAGE_CONFIG[pacote]
        if num_collabs is None:
            num_collabs = pkg_cfg["default_collabs"]

        # Engagement multiplier
        eng_mult = _clamp(engagement_rate / BASE_ENGAGEMENT_RATE, ENGAGEMENT_FLOOR, ENGAGEMENT_CEILING)

        # Base price
        preco_base = (alcance_medio / 1000.0) * eng_mult * BASE_PRICE_SCALE

        # Multipliers
        mult_nicho = NICHE_MULTIPLIERS[nicho]
        mult_formato = FORMAT_MULTIPLIERS[formato]
        mult_pacote = pkg_cfg["discount_multiplier"]

        # Unit price (per collab) with floor
        preco_unitario = preco_base * mult_nicho * mult_formato * mult_pacote
        preco_unitario = max(preco_unitario, MIN_PRICE_BRL)
        preco_unitario = _round_brl(preco_unitario)

        # Total price for the package
        preco_total = _round_brl(preco_unitario * num_collabs)

        # CPM comparison
        cpm_omnis = (preco_unitario / alcance_medio) * 1000.0
        economia_pct = (1.0 - cpm_omnis / meta_cpm) * 100.0
        alcance_total_estimado = alcance_medio * num_collabs

        result = {
            "input": self._input_dict(
                seguidores, alcance_medio, engagement_rate, nicho, formato, pacote, num_collabs, meta_cpm
            ),
            "pricing": {
                "preco_base": _round_brl(preco_base),
                "multiplicador_nicho": mult_nicho,
                "multiplicador_formato": mult_formato,
                "multiplicador_pacote": mult_pacote,
                "preco_unitario": preco_unitario,
                "preco_total": preco_total,
                "preco_por_collab": preco_unitario,
            },
            "cpm_comparison": {
                "cpm_omnis": round(cpm_omnis, 2),
                "cpm_meta": meta_cpm,
                "economia_pct": round(economia_pct, 1),
                "alcance_total_estimado": alcance_total_estimado,
            },
        }

        result["proposta"] = self.format_proposal(result)
        return result

    def format_proposal(self, calculation_result: dict[str, Any]) -> str:
        """Format a commercial proposal text from calculation result.

        Args:
            calculation_result: Dict returned by calculate_price().

        Returns:
            Formatted proposal string in PT-BR.
        """
        if calculation_result.get("error"):
            return "ERRO: " + "; ".join(calculation_result.get("messages", []))

        inp = calculation_result["input"]
        prc = calculation_result["pricing"]
        cpm = calculation_result["cpm_comparison"]

        pkg_label = PACKAGE_CONFIG[inp["pacote"]]["label"]
        nicho_label = inp["nicho"].capitalize()
        formato_label = inp["formato"].capitalize()

        lines = [
            "=" * 60,
            "PROPOSTA COMERCIAL — PUBLISHER OS / OMNIS",
            "=" * 60,
            "",
            f"  Pacote: {pkg_label} ({inp['num_collabs']} collab{'s' if inp['num_collabs'] > 1 else ''})",
            f"  Nicho: {nicho_label}",
            f"  Formato: {formato_label}",
            f"  Seguidores: {inp['seguidores']:,}".replace(",", "."),
            f"  Alcance Medio: {inp['alcance_medio']:,}".replace(",", "."),
            f"  Engagement: {inp['engagement_rate']}%",
            "",
            "-" * 60,
            "INVESTIMENTO",
            "-" * 60,
            f"  Preco por collab: R$ {prc['preco_unitario']:,.0f}".replace(",", "."),
            f"  Preco total ({inp['num_collabs']} collabs): R$ {prc['preco_total']:,.0f}".replace(",", "."),
            "",
            "-" * 60,
            "COMPARATIVO CPM (Custo por Mil Impressoes)",
            "-" * 60,
            f"  CPM OMNIS: R$ {cpm['cpm_omnis']:.2f}",
            f"  CPM Meta Ads: R$ {cpm['cpm_meta']:.2f}",
            f"  Economia: {cpm['economia_pct']:.1f}%",
            f"  Alcance total estimado: {cpm['alcance_total_estimado']:,} impressoes".replace(",", "."),
            "",
            "-" * 60,
            "VANTAGENS DO PACOTE",
            "-" * 60,
            "  - Conteudo organico com credibilidade de influenciador real",
            "  - Segmentacao por nicho (audiencia qualificada)",
            "  - Engajamento real (likes, comentarios, saves, shares)",
            "  - Conteudo permanente no feed (exceto stories)",
            "  - Relatorio de performance pos-publicacao",
            "",
            f"  Economia estimada vs Meta Ads: R$ {cpm['cpm_meta'] * cpm['alcance_total_estimado'] / 1000 - prc['preco_total']:,.0f}".replace(",", "."),
            "=" * 60,
        ]

        return "\n".join(lines)

    def compare_packages(
        self,
        seguidores: int,
        alcance_medio: int,
        engagement_rate: float,
        nicho: str,
        formato: str = "collab",
        meta_cpm: float = DEFAULT_META_CPM,
    ) -> dict[str, Any]:
        """Compare all available packages for a given profile.

        Args:
            seguidores: Total follower count.
            alcance_medio: Average reach per post.
            engagement_rate: Engagement rate in %.
            nicho: Profile niche.
            formato: Content format (default: collab).
            meta_cpm: Meta Ads CPM reference.

        Returns:
            Dict with comparison table across starter/growth/premium.
        """
        comparisons: list[dict[str, Any]] = []

        for pkg_name in ["starter", "growth", "premium"]:
            result = self.calculate_price(
                seguidores=seguidores,
                alcance_medio=alcance_medio,
                engagement_rate=engagement_rate,
                nicho=nicho,
                formato=formato,
                pacote=pkg_name,
                meta_cpm=meta_cpm,
            )
            if result.get("error"):
                comparisons.append({"pacote": pkg_name, "error": result["messages"]})
            else:
                comparisons.append({
                    "pacote": pkg_name,
                    "label": PACKAGE_CONFIG[pkg_name]["label"],
                    "num_collabs": result["input"]["num_collabs"],
                    "preco_unitario": result["pricing"]["preco_unitario"],
                    "preco_total": result["pricing"]["preco_total"],
                    "cpm_omnis": result["cpm_comparison"]["cpm_omnis"],
                    "economia_pct": result["cpm_comparison"]["economia_pct"],
                })

        return {
            "perfil": {
                "seguidores": seguidores,
                "alcance_medio": alcance_medio,
                "engagement_rate": engagement_rate,
                "nicho": nicho,
                "formato": formato,
            },
            "comparacao": comparisons,
            "recomendacao": self._recommend_package(comparisons),
        }

    def _recommend_package(self, comparisons: list[dict[str, Any]]) -> str:
        """Recommend the best package based on CPM efficiency."""
        valid = [c for c in comparisons if "error" not in c]
        if not valid:
            return "Nenhum pacote disponivel."

        # Best CPM (lowest) with best total value
        best = min(valid, key=lambda c: c["cpm_omnis"])
        return (
            f"Pacote recomendado: {best['label']} — "
            f"R$ {best['preco_total']:,.0f} por {best['num_collabs']} collabs, "
            f"CPM de R$ {best['cpm_omnis']:.2f} ({best['economia_pct']:.1f}% economia vs Meta Ads)"
        ).replace(",", ".")

    def _input_dict(
        self,
        seguidores: int,
        alcance_medio: int,
        engagement_rate: float,
        nicho: str,
        formato: str,
        pacote: str,
        num_collabs: int | None,
        meta_cpm: float,
    ) -> dict[str, Any]:
        """Build the input summary dict."""
        d: dict[str, Any] = {
            "seguidores": seguidores,
            "alcance_medio": alcance_medio,
            "engagement_rate": engagement_rate,
            "nicho": nicho,
            "formato": formato,
            "pacote": pacote,
            "num_collabs": num_collabs,
            "meta_cpm": meta_cpm,
        }
        return d


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="pricing-calculator",
        description="Calculadora de preco de publi Instagram — OMNIS Forge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run.py -s 50000 -a 15000 -e 4.2 -n turismo -f collab -p starter
  python run.py -s 200000 -a 60000 -e 3.5 -n gastronomia -f carrossel -p growth
  python run.py -s 452000 -a 180000 -e 5.1 -n turismo -f reel -p premium
  python run.py -s 452000 -a 180000 -e 5.1 -n turismo --compare
        """,
    )

    parser.add_argument("-s", "--seguidores", type=int, required=True,
                        help="Numero total de seguidores (>=1000)")
    parser.add_argument("-a", "--alcance", type=int, required=True,
                        dest="alcance_medio",
                        help="Alcance medio por post/impressoes (>=100)")
    parser.add_argument("-e", "--engagement", type=float, required=True,
                        dest="engagement_rate",
                        help="Taxa de engajamento em %% (ex: 4.2)")
    parser.add_argument("-n", "--nicho", type=str, required=False,
                        default="turismo",
                        choices=sorted(VALID_NICHES),
                        help="Nicho do perfil")
    parser.add_argument("-f", "--formato", type=str, required=False,
                        default="collab",
                        choices=sorted(VALID_FORMATS),
                        help="Formato do conteudo")
    parser.add_argument("-p", "--pacote", type=str, required=False,
                        default="starter",
                        choices=sorted(VALID_PACKAGES),
                        help="Pacote de venda")
    parser.add_argument("-c", "--collabs", type=int, default=None,
                        dest="num_collabs",
                        help="Numero de collabs (padrao conforme pacote)")
    parser.add_argument("--cpm", type=float, default=DEFAULT_META_CPM,
                        dest="meta_cpm",
                        help=f"CPM Meta Ads referencia (padrao: {DEFAULT_META_CPM})")
    parser.add_argument("--compare", action="store_true", default=False,
                        help="Comparar todos os pacotes")
    parser.add_argument("--json", action="store_true", default=False,
                        dest="json_output",
                        help="Saida em JSON em vez de texto formatado")
    parser.add_argument("--no-proposal", action="store_true", default=False,
                        dest="no_proposal",
                        help="Suprimir proposta formatada no JSON")

    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    calc = PubliPriceCalculator(dry_run=True)

    if args.compare:
        result = calc.compare_packages(
            seguidores=args.seguidores,
            alcance_medio=args.alcance_medio,
            engagement_rate=args.engagement_rate,
            nicho=args.nicho,
            formato=args.formato,
            meta_cpm=args.meta_cpm,
        )
        if args.json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_comparison_text(result)
    else:
        result = calc.calculate_price(
            seguidores=args.seguidores,
            alcance_medio=args.alcance_medio,
            engagement_rate=args.engagement_rate,
            nicho=args.nicho,
            formato=args.formato,
            pacote=args.pacote,
            num_collabs=args.num_collabs,
            meta_cpm=args.meta_cpm,
        )
        if args.json_output:
            if args.no_proposal:
                result.pop("proposta", None)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result.get("error"):
                print("ERRO:", "; ".join(result["messages"]))
                sys.exit(1)
            print(result["proposta"])


def print_comparison_text(comparison: dict[str, Any]) -> None:
    """Pretty-print package comparison table."""
    perfil = comparison["perfil"]
    print(f"""
COMPARATIVO DE PACOTES
Perfil: {perfil['seguidores']:,} seguidores | Alcance: {perfil['alcance_medio']:,} |
        Nicho: {perfil['nicho']} | Formato: {perfil['formato']} | Eng: {perfil['engagement_rate']}%
{"-" * 70}
{'Pacote':<10} {'Collabs':<8} {'Preco/Collab':<15} {'Preco Total':<15} {'CPM OMNIS':<12} {'Economia':<12}
{"-" * 70}""".replace(",", "."))

    for c in comparison["comparacao"]:
        if "error" in c:
            print(f"{c['pacote']:<10} ERRO: {'; '.join(c['error'])}")
        else:
            print(
                f"{c['label']:<10} "
                f"{c['num_collabs']:<8} "
                f"R$ {c['preco_unitario']:>10,.0f}  "
                f"R$ {c['preco_total']:>10,.0f}  "
                f"R$ {c['cpm_omnis']:>8.2f}  "
                f"{c['economia_pct']:>8.1f}%"
            )

    print("-" * 70)
    print(f"\n{comparison['recomendacao']}\n")


# ═══════════════════════════════════════════════════════════════
# Example usage
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Example 1: Small profile, turismo, starter
    print("=" * 60)
    print("EXEMPLO 1: Perfil pequeno — 50K, turismo, Starter")
    print("=" * 60)
    calc = PubliPriceCalculator(dry_run=True)
    r1 = calc.calculate_price(
        seguidores=50000,
        alcance_medio=15000,
        engagement_rate=4.2,
        nicho="turismo",
        formato="collab",
        pacote="starter",
    )
    print(r1["proposta"])
    print()

    # Example 2: Medium profile, gastronomia, growth, 3 collabs carrossel
    print("=" * 60)
    print("EXEMPLO 2: Perfil medio — 200K, gastronomia, Growth (3 carrosseis)")
    print("=" * 60)
    r2 = calc.calculate_price(
        seguidores=200000,
        alcance_medio=60000,
        engagement_rate=3.5,
        nicho="gastronomia",
        formato="carrossel",
        pacote="growth",
    )
    print(r2["proposta"])
    print()

    # Example 3: Lucas @agenteviajabrasil, turismo, premium, 4 reels
    print("=" * 60)
    print("EXEMPLO 3: @agenteviajabrasil — 452K, turismo, Premium (4 reels)")
    print("=" * 60)
    r3 = calc.calculate_price(
        seguidores=452000,
        alcance_medio=180000,
        engagement_rate=5.1,
        nicho="turismo",
        formato="reel",
        pacote="premium",
    )
    print(r3["proposta"])
    print()

    # Example 4: Compare all packages
    print("=" * 60)
    print("EXEMPLO 4: Comparativo de pacotes — @agenteviajabrasil")
    print("=" * 60)
    comp = calc.compare_packages(
        seguidores=452000,
        alcance_medio=180000,
        engagement_rate=5.1,
        nicho="turismo",
        formato="reel",
    )
    print_comparison_text(comp)

    # If CLI args provided, run CLI mode instead
    if len(sys.argv) > 1:
        main()
