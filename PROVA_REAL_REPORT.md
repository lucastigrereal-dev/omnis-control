# PROVA_REAL_REPORT

Data: 2026-05-24  
Repo: `C:\Users\lucas\omnis-control`  
Branch: `feature/omnis-5waves-runtime-supreme`  
Modo: execução real (sem mock), usando registry vivo

## Escopo da prova

Rodamos as capacidades do `WorkflowRegistry.default()` com input real, `dry_run=False` (quando aplicável), medindo:

- tempo de execução;
- `cost_local_pct`;
- qualidade prática da saída (usável vs fraca vs quebra real).

## Observação importante de verdade operacional

Você pediu 16 capacidades do registry. No estado atual do código, o registry vivo está com **17 entradas** (entrou `caption_generator`).  
Então a prova foi feita no estado real atual: **17 capacidades**.

## Resumo rápido

- 🟢 PROVADA: **7**
- 🟡 RODA MAS FRACA: **2**
- 🔴 QUEBRA COM REAL: **8**

## Tabela de prova real

| Capacidade | Veredito | Tempo | cost_local_pct | Output real (resumo) |
|---|---|---:|---:|---|
| `deep_research` | 🟡 | 19.5s | 100 | Gerou só título markdown (`report_chars=70`), `citation_count=0`, `search_backend=null`. Houve erros de conexão LLM no fluxo (APIConnectionError para Ollama via LiteLLM). |
| `content_calendar` | 🟢 | 0.0s | 100 | Gerou 5 itens reais. Exemplo: `queue_id=8e460ffa-d000`, `@afamiliatigrereal`, `2026-05-24 09:00`, formato `feed`, objetivo `autoridade`. |
| `lead_scoring` | 🟢 | 0.0s | 100 | Scoreou 2 prospects reais. Top lead: `Bistrô da Praia`, tier `warm`, composite `0.56`. |
| `content_quality` | 🔴 | 0.001s | 100 (registry) | Quebra na inicialização: `TypeError` ao instanciar `AkashaSinkAdapter` abstrato (sem `health_check/query_events/write_event`). |
| `video_edit` | 🟢 | 7.47s | 100 | Com vídeo real (`C:\Users\lucas\_ORGANIZADO_POR_TIPO\Videos\#1 ... .mp4`) transcreveu com sucesso (`chars=500`, `files=1`). Preview: texto transcrito em PT-BR. |
| `app_factory` | 🟢 | 0.004s | 100 | Gerou PRD real (`prd_chars=2239`), `artifact_id=art_4fb0a50119`, escreveu 4 arquivos. |
| `code_run` | 🔴 | 0.039s | 100 | Quebra real: `HTTP Error 404: Not Found` no caminho OpenHands. Sem output executado (`output_lines=0`). |
| `system_health` | 🟡 | 0.0s | 100 | Executa, mas sinal fraco: `workflows_importable=0`, `workflows_total=0`, `agencies_total=0` (health roda sem dados reais registrados). |
| `sdr_pipeline` | 🟢 | 0.001s | 100 | Pipeline executou com 2 prospects, `actionable_count=2`, `sequences_generated=2`. |
| `daily_briefing` | 🟢 | 0.0s | 100 | Briefing completo gerado (Sistema + Leads + Calendário). Exemplo real inclui `HOT:0 WARM:2` e `Itens:3 posts planejados`. |
| `metrics_snapshot` | 🔴 | 0.001s | 100 (registry) | Quebra na inicialização pelo mesmo `AkashaSinkAdapter` abstrato. |
| `squad_assignment` | 🔴 | 0.001s | 100 (registry) | Quebra na inicialização pelo mesmo `AkashaSinkAdapter` abstrato. |
| `deliverable_mapping` | 🔴 | 0.001s | 100 (registry) | Quebra na inicialização pelo mesmo `AkashaSinkAdapter` abstrato. |
| `task_dispatch` | 🔴 | 0.001s | 100 (registry) | Quebra na inicialização pelo mesmo `AkashaSinkAdapter` abstrato. |
| `capability_forge` | 🔴 | 0.001s | 100 (registry) | Quebra na inicialização pelo mesmo `AkashaSinkAdapter` abstrato. |
| `skill_execution` | 🟢 | 23.8s | 100 | Executou 2 planos reais (`total_entries=7`, `review_entries=3`, `unique_skills=3`). |
| `caption_generator` *(extra no registry atual)* | 🔴 | 0.0s | 100 (registry) | Quebra de construção: `FileAkashaSink.__init__()` sem `target_dir` obrigatório. |

## Achados que mock tende a esconder (e aqui apareceram)

1. **Quebra estrutural de fábrica em lote**: 6 workflows (`content_quality`, `metrics_snapshot`, `squad_assignment`, `deliverable_mapping`, `task_dispatch`, `capability_forge`) não sobem em runtime real por uso de classe abstrata de sink.
2. **`code_run` depende de endpoint indisponível** (404 OpenHands) no caminho real.
3. **`deep_research` não está entregando conteúdo útil** sem resolver a conexão LLM no backend atual; retorna “sucesso técnico”, mas saída fraca.
4. **Drift do registry**: esperado 16, estado real 17 (`caption_generator`) e o extra está quebrando na construção.

## Evidências técnicas salvas

- Resultado bruto por capacidade:  
  `C:\Users\lucas\omnis-control\output\real_proof\real_proof_results.json`

## Recomendação objetiva para o Claude Code (sem eu mudar lógica aqui)

Prioridade P1 (bloqueia prova real robusta):

1. Corrigir construtores dos workflows que instanciam `AkashaSinkAdapter` abstrato.
2. Corrigir caminho real de `code_run` (OpenHands/endpoint).
3. Ajustar `deep_research` para falhar explicitamente quando LLM/search real cair, em vez de “success fraco”.
4. Corrigir `caption_generator` no registry (injeção de `target_dir` no `FileAkashaSink`).

Depois disso, repetir esta mesma prova em sequência para fechar 100% verde.
