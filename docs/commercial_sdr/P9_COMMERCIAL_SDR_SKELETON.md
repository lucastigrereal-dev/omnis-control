# P9 Commercial SDR Skeleton — Especificacao

**Criado:** 2026-05-12 | **Branch:** parallel/p9-commercial-sdr-skeleton | **Versao:** 1.0.0

## Objetivo

Frente de prospeccao B2B deterministica. Modela perfis de prospect, scoring de oportunidade, sequencias de outreach e planos SDR — sem nunca enviar mensagem real, sem API externa, sem rede.

## Escopo

### Permitido
- `src/commercial_sdr/` — Pacote principal
- `tests/commercial_sdr/` — Testes unitarios
- `docs/commercial_sdr/` — Documentacao

### Proibido
- `src/cli.py`, `src/core/`, `src/mission/`, `src/app_factory/`, `src/automation/`
- `src/governance/`, `src/analytics/`, `src/computer_ops/`
- `src/output_generator/`
- `data/**`, `exports/**`, `logs/**`, `config/**`
- `.env`, `pyproject.toml`

## Modelos

| Modelo | Descricao |
|---|---|
| `ProspectProfile` | Perfil de prospect B2B (hotel, restaurante, parceiro) |
| `LeadSource` | Enum: origem do lead (instagram, referral, manual_research, inbound, event, partnership) |
| `OutreachChannel` | Enum: canal de contato (email, instagram_dm, whatsapp, linkedin, phone) |
| `StepAction` | Enum: acao no passo (research, connect, intro_message, value_offer, follow_up, proposal, close_ask) |
| `SDRMessage` | Mensagem de outreach — template deterministico, nunca enviada |
| `OutreachStep` | Passo individual em sequencia de outreach |
| `OutreachSequence` | Sequencia completa de 7 passos para um prospect |
| `OpportunityScore` | Score composto deterministico + classificacao (hot/warm/cold/disqualified) |
| `SDRPlan` | Plano SDR completo agregando prospects, scores e sequencias |

## Servicos

| Funcao/Classe | Descricao |
|---|---|
| `CommercialSDRPlanner` | Planejador deterministico — build_sdr_plan() |
| `score_prospect()` | Calcula score composto (segment_fit + engagement + budget + urgency) |
| `generate_sdr_message()` | Gera template de mensagem por canal + acao |
| `build_outreach_sequence()` | Constroi sequencia de 7 passos (~25 dias) |
| `validate_sequence()` | Valida sequencia — retorna warnings |
| `build_batch_plan()` | Funcao de conveniencia para lote de prospects |

## Regras de Seguranca

1. **Dry-run por padrao** — `CommercialSDRPlanner.dry_run = True` sempre
2. **Nenhum envio real** — `SDRMessage.sent` sempre `False`
3. **Approval required** — Canais de alto risco (instagram_dm, whatsapp, phone) e propostas sempre requerem aprovacao
4. **Risk flags ativas** — `no_real_delivery`, `approval_required_for_external_send`, `mass_outreach_flagged`
5. **Deterministico** — Scoring sem LLM, sem rede, sem banco de dados
6. **Stdlib only** — Apenas `dataclasses`, `enum`, `uuid`, `datetime`, `typing`

### Canais de Risco

| Canal | Nivel de Risco | Approval Required |
|---|---|---|
| `email` | Baixo | Apenas para PROPOSAL |
| `linkedin` | Medio | Sempre |
| `instagram_dm` | Alto | Sempre |
| `whatsapp` | Alto | Sempre |
| `phone` | Alto | Sempre |

## Estrutura do Pacote

```
src/commercial_sdr/
├── __init__.py     # API publica, __all__
├── models.py       # 8 dataclasses + 4 enums
├── service.py      # CommercialSDRPlanner, funcoes core
├── errors.py       # 13 excecoes hierarquicas

tests/commercial_sdr/
├── __init__.py
├── conftest.py     # Fixtures compartilhadas
├── test_models.py  # 60+ testes de modelos
├── test_service.py # 40+ testes de servico

docs/commercial_sdr/
└── P9_COMMERCIAL_SDR_SKELETON.md  # Este arquivo
```

## Scoring — Formula Composta

```
composite = segment_fit * 0.35 + engagement_signal * 0.25
          + budget_indicator * 0.25 + urgency * 0.15

Tiers:
  >= 0.70 → HOT (pursuable)
  >= 0.40 → WARM (pursuable)
  >= 0.15 → COLD
  < 0.15  → DISQUALIFIED
```

### Heuristicas

| Dimensao | Input | Logica |
|---|---|---|
| `segment_fit` | Segmento do prospect | High = hotel/resort/pousada/restaurante (0.90), Medium = evento/experiencia/guia (0.55), Low = outros (0.25) |
| `engagement_signal` | Canais de contato | 3+ canais (0.85), 2 (0.55), 1 (0.30), 0 (0.05) |
| `budget_indicator` | LeadSource | referral (0.80), inbound (0.75), partnership (0.65), instagram (0.50), event (0.45), manual_research (0.30) |
| `urgency` | Tags + notes | Keywords urgentes (0.75), website presente (0.45), default (0.30) |

## Cadencia Padrao (7 passos, ~25 dias)

| # | Acao | Canal | Delay |
|---|---|---|---|
| 1 | RESEARCH | email | 0d |
| 2 | CONNECT | email | 0d |
| 3 | INTRO_MESSAGE | email | 0d |
| 4 | VALUE_OFFER | email | +3d |
| 5 | FOLLOW_UP | email | +5d |
| 6 | PROPOSAL | email | +7d |
| 7 | CLOSE_ASK | email | +10d |

## Testes

```bash
python -m pytest tests/commercial_sdr/ -q
```

Cobertura:
- Round-trip `to_dict()`/`from_dict()` para todos os modelos
- Validacao de campos obrigatorios (company_name, contact_name, body)
- Valores padrao e fully-populated
- Propriedades calculadas (`has_instagram`, `has_email`, `is_pursuable`, `total_steps`, etc.)
- Score por segmento, canal, source e urgencia
- Templates de mensagem para cada combinacao canal+acao
- Garantias dry-run (nunca enviado, nunca API externa)
- Validacao de sequencia (warnings para violacoes)
- Parametrizacao de source → budget
- Bloqueio de lista vazia

## Nao Escopo (para frentes futuras)

- Integracao com CLI (`cli.py`)
- Envio real de email (SMTP)
- Envio real de DM (Instagram API)
- Conexao com WhatsApp Business API
- Integracao com Akasha/Gringotts
- CRM pipeline real (HubSpot/Pipedrive)
- Workflows n8n para SDR
- Enriquecimento de leads (Apollo/Cognism)
- Email tracking (pixels, links)
