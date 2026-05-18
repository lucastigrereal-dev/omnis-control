"""Pre-built brand visual profiles for the 6 Instagram pages."""

from __future__ import annotations

from .models import (
    BrandVisualProfile,
    ARCHETYPE_BOLD, ARCHETYPE_MINIMALIST, ARCHETYPE_ELEGANT,
    ARCHETYPE_PLAYFUL, ARCHETYPE_EDITORIAL,
)


class BrandPresets:
    """Factory of brand profiles for all Instagram pages."""

    LUCAS_TIGRE_REAL = BrandVisualProfile.new(
        name="Lucas Tigre Real",
        description="Perfil de autoridade e lifestyle do Lucas. Tom pessoal, direto, aventureiro.",
        brand_id="lucastigrereal",
        primary_color="#1A1A2E",
        secondary_color="#E94560",
        accent_color="#0F3460",
        heading_font="Montserrat",
        body_font="Inter",
        logo_style="lettermark",
        visual_archetype=ARCHETYPE_BOLD,
        mood_keywords=["aventureiro", "direto", "impactante", "masculino", "moderno"],
    )

    O_INATAL_RN = BrandVisualProfile.new(
        name="O Inatal RN",
        description="Turismo em Natal/RN. Visual tropical, cores quentes, praia e sol.",
        brand_id="oinatalrn",
        primary_color="#006994",
        secondary_color="#FFD700",
        accent_color="#FF6B35",
        heading_font="Poppins",
        body_font="Inter",
        logo_style="wordmark",
        visual_archetype=ARCHETYPE_PLAYFUL,
        mood_keywords=["praia", "tropical", "sol", "mar", "vibrante"],
    )

    AGENTE_VIAJA_BRASIL = BrandVisualProfile.new(
        name="Agente Viaja Brasil",
        description="Viagens pelo Brasil. Nacional, diverso, cultural.",
        brand_id="agenteviajabrasil",
        primary_color="#2D6A4F",
        secondary_color="#FFB703",
        accent_color="#FB8500",
        heading_font="Poppins",
        body_font="Inter",
        logo_style="wordmark",
        visual_archetype=ARCHETYPE_EDITORIAL,
        mood_keywords=["brasil", "cultural", "diverso", "natureza", "nacional"],
    )

    A_FAMILIA_TIGRE_REAL = BrandVisualProfile.new(
        name="A Familia Tigre Real",
        description="Perfil família. Aconchegante, divertido, emocional.",
        brand_id="afamiliatigrereal",
        primary_color="#6B4E71",
        secondary_color="#F4A261",
        accent_color="#E76F51",
        heading_font="Nunito",
        body_font="Inter",
        logo_style="wordmark",
        visual_archetype=ARCHETYPE_PLAYFUL,
        mood_keywords=["familia", "aconchegante", "divertido", "emocional", "uniao"],
    )

    O_QUE_COMER_NATAL_RN = BrandVisualProfile.new(
        name="O Que Comer Natal RN",
        description="Gastronomia de Natal. Apelativo, quente, saboroso.",
        brand_id="oquecomernatalrn",
        primary_color="#8B0000",
        secondary_color="#FFD700",
        accent_color="#FF6347",
        heading_font="Playfair Display",
        body_font="Inter",
        logo_style="wordmark",
        visual_archetype=ARCHETYPE_ELEGANT,
        mood_keywords=["gastronomia", "sabor", "apetitoso", "quente", "local"],
    )

    NATAL_AI_VOU_EU = BrandVisualProfile.new(
        name="Natal Ai Vou Eu",
        description="Guia de Natal, praias e passeios. Informativo e leve.",
        brand_id="natalaivoueu",
        primary_color="#028090",
        secondary_color="#F0F3BD",
        accent_color="#02C39A",
        heading_font="Poppins",
        body_font="Inter",
        logo_style="wordmark",
        visual_archetype=ARCHETYPE_MINIMALIST,
        mood_keywords=["guia", "praia", "leve", "informativo", "util"],
    )

    ALL: list[BrandVisualProfile] = [
        LUCAS_TIGRE_REAL, O_INATAL_RN, AGENTE_VIAJA_BRASIL,
        A_FAMILIA_TIGRE_REAL, O_QUE_COMER_NATAL_RN, NATAL_AI_VOU_EU,
    ]

    BY_BRAND_ID: dict[str, BrandVisualProfile] = {p.brand_id: p for p in [
        LUCAS_TIGRE_REAL, O_INATAL_RN, AGENTE_VIAJA_BRASIL,
        A_FAMILIA_TIGRE_REAL, O_QUE_COMER_NATAL_RN, NATAL_AI_VOU_EU,
    ]}

    @classmethod
    def get(cls, brand_id: str) -> BrandVisualProfile | None:
        return cls.BY_BRAND_ID.get(brand_id)

    @classmethod
    def all_dicts(cls) -> list[dict]:
        return [p.to_dict() for p in cls.ALL]
