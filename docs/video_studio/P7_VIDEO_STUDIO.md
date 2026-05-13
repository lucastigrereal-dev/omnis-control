# P7 Video Studio — Skeleton

**Data:** 2026-05-12 | **Branch:** parallel/p7-video-studio
**Fase:** Onda 4 — Skeleton
**Base Spec:** OMNIS Roadmap Wave 4

## Visao Geral

P7 Video Studio implementa o planejamento deterministico de edicao de video. Opera exclusivamente em modo dry-run: modela specs, timestamps e pacotes sem processar video real, sem ffmpeg, sem moviepy, sem transcricao de audio.

## Arquivos Criados

```
src/video_studio/
├── __init__.py    # Barrel re-exports com __all__
├── models.py      # 7 dataclasses + 8 enums
├── service.py     # VideoStudioPlanner + 6 funcoes module-level
└── errors.py      # 7 excecoes hierarquicas

tests/video_studio/
├── __init__.py    # Package marker
├── test_models.py # 22 testes de modelos
└── test_service.py# 24 testes de servico + edge cases

docs/video_studio/
└── P7_VIDEO_STUDIO.md  # Este documento
```

## Arquivos NAO Alterados

- src/cli.py
- src/core/
- src/mission/
- src/app_factory/
- src/automation/
- src/governance/
- src/analytics/
- src/computer_ops/
- src/finance/
- src/commercial_sdr/
- src/sales_crm/
- src/marketing/
- src/memory_pack/
- src/design_art/
- src/output_generator/
- data/**
- exports/**
- logs/**
- config/**
- .env
- pyproject.toml

## Modelos

| Modelo | Descricao |
|---|---|
| VideoSource | Metadados da fonte de video (codec, resolucao, fps) |
| TranscriptSegment | Segmento de transcricao com timestamps |
| HookCandidate | Candidato a hook detectado deterministicamente |
| CutPlan | Plano de corte agregando CutInstructions |
| CutInstruction | Instrucao individual de corte (keep/trim/remove) |
| ReelScript | Roteiro de reel com segmentos numerados |
| ReelSegment | Segmento individual do roteiro |
| CaptionOverlaySpec | Especificacao de legenda na tela |
| VideoPackage | Pacote completo agregando todos os artefatos |

## Servico — VideoStudioPlanner

Pipeline deterministico:

1. `analyze_transcript_segments()` — metricas agregadas (duracao, palavras, confianca)
2. `detect_hook_candidates()` — heuristica baseada em densidade de palavras e confianca
3. `build_cut_plan()` — classifica segmentos em KEEP/TRIM/REMOVE baseado nos hooks
4. `build_reel_script()` — gera roteiro numerado a partir do plano de corte
5. `build_video_package()` — orquestra pipeline completo
6. `validate_video_package()` — valida e gera relatorio com warnings

## Regras

- Nao processa video real (apenas metadados e specs)
- Nao usa ffmpeg, moviepy ou OpenCV
- Nao transcreve audio real
- Nao usa rede, LLM ou banco de dados
- Operacoes 100% deterministicas baseadas em heuristica stdlib
- Dataclasses com serializacao to_dict()/from_dict()

## Design Decisions

- **Heuristica de hook**: densidade de palavras (word_count / duration) ponderada por confidence. Thresholds: >= 0.7 HIGH, >= 0.4 MEDIUM, < 0.4 LOW.
- **Target duration**: cortes menores sao removidos primeiro para caber no tempo alvo.
- **Validacao cross-ref**: verifica consistencia de source_id e plan_id entre componentes.
- **Module-level functions**: wrappers de conveniencia que usam instancia shared de VideoStudioPlanner.

## Proximos Passos

- Integrar com pipeline de publicacao (ARGOS)
- Adicionar suporte a templates de formatos especificos
- Conectar com modulo de transcricao real quando disponivel
- Implementar renderizacao de legendas
