"""Shared fixtures for Commercial SDR tests."""
from __future__ import annotations

import pytest

from src.commercial_sdr.models import (
    ProspectProfile,
    LeadSource,
    OutreachChannel,
    StepAction,
    SDRMessage,
    OutreachStep,
    OutreachSequence,
    OpportunityScore,
    SDRPlan,
)
from src.commercial_sdr.service import (
    score_prospect,
    build_outreach_sequence,
    generate_sdr_message,
    build_batch_plan,
    validate_sequence,
)


@pytest.fixture
def sample_hotel_prospect() -> ProspectProfile:
    return ProspectProfile.new(
        company_name="Hotel Villa D'oro",
        contact_name="Roberta Campos",
        segment="hotel",
        source=LeadSource.INSTAGRAM,
        instagram_handle="@hotelvilladoro",
        email="roberta@hotelvilladoro.com.br",
        phone="+55 84 99999-0001",
        website="https://hotelvilladoro.com.br",
        location="Natal-RN",
        notes="Hotel boutique 40 quartos, publico premium",
        tags=["boutique", "premium", "natal"],
    )


@pytest.fixture
def sample_restaurant_prospect() -> ProspectProfile:
    return ProspectProfile.new(
        company_name="Restaurante Mar & Fogo",
        contact_name="Chef Pedro",
        segment="restaurante",
        source=LeadSource.REFERRAL,
        instagram_handle="@marefogo",
        email="chefpedro@marefogo.com.br",
        location="Ponta Negra-RN",
        notes="Gastronomia contemporanea, busca visibilidade urgente",
        tags=["contemporanea", "gastronomia", "urgente"],
    )


@pytest.fixture
def sample_minimal_prospect() -> ProspectProfile:
    return ProspectProfile.new(
        company_name="Pousada Simples",
        contact_name="Joao Silva",
        segment="transporte",
        source=LeadSource.MANUAL_RESEARCH,
        location="Interior-SP",
    )


@pytest.fixture
def sample_prospects(sample_hotel_prospect, sample_restaurant_prospect, sample_minimal_prospect) -> list[ProspectProfile]:
    return [sample_hotel_prospect, sample_restaurant_prospect, sample_minimal_prospect]


@pytest.fixture
def sample_message(sample_hotel_prospect) -> SDRMessage:
    return generate_sdr_message(
        sample_hotel_prospect,
        OutreachChannel.EMAIL,
        StepAction.INTRO_MESSAGE,
    )


@pytest.fixture
def sample_sequence(sample_hotel_prospect) -> OutreachSequence:
    return build_outreach_sequence(sample_hotel_prospect)


@pytest.fixture
def sample_score(sample_hotel_prospect) -> OpportunityScore:
    return score_prospect(sample_hotel_prospect)


@pytest.fixture
def sample_plan(sample_prospects) -> SDRPlan:
    return build_batch_plan("Plano Teste", "Descricao teste", sample_prospects)
