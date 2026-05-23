# CODEX Wave 3 Risk Report (P0/P1)

Data: 2026-05-23  
Commits auditados: `63b41d4` + `0fc08ed`  
Escopo: Legos de código e vídeo (`CodeExecutorLego`, `VideoProcessorLego`) + gate de secret scan

## Resumo Executivo

- **P0 confirmado:** risco de execução arbitrária no host no fallback local de `CodeExecutorLego` por interpolação direta de `spec.goal` em script executado via `python -c`.
- **Curativo aplicado:** bloqueio de payload suspeito (`unsafe_goal_payload`) antes de chamar `python -c` (incorporado pela frente de construção no commit `0fc08ed`).
- **Não é cura definitiva.** A arquitetura de sandbox continua frágil por design.

## Achados

### P0 — RCE no fallback local do CodeExecutor

**Arquivo:** `src/legos/code_executor_lego.py`  
**Ponto:** construção de script com interpolação de `spec.goal` + execução por `subprocess.run([python, "-c", script])`.

Impacto:
- Payload com quebra de linha e tokens de injeção pode alterar o código efetivamente executado no host.
- Isso é risco de execução arbitrária local.

Status:
- **Mitigado parcialmente** por gate local `unsafe_goal_payload` (já em `0fc08ed`).
- **Risco estrutural permanece** até redesign do sandbox.

### P1 — Validação de path insuficiente no VideoProcessor

**Arquivo:** `src/legos/video_processor_lego.py`  
Pontos observados:
- `spec.video_path` e `spec.output_dir` seguem para operações de transcrição/corte/ffmpeg sem normalização forte de fronteira.
- Não há `safe_path` explícito para limitar escrita/leitura em base permitida.

Impacto:
- Em contextos de input não confiável, aumenta risco de path traversal / escrita em local não previsto.

Status:
- **Somente sinalizado** (mudança de comportamento exigiria decisão da frente de construção).

### P1 — Dependência de supply-chain do modelo Whisper

**Arquivo:** `src/legos/video_processor_lego.py` (`whisper.load_model("tiny")`)  
Ponto observado:
- Lazy load está correto (não carrega na importação), mas a origem do modelo depende do mecanismo padrão do pacote.

Impacto:
- Sem pinning/artefato interno, há risco operacional de dependência externa em runtime.

Status:
- **Somente sinalizado** para decisão de arquitetura/deploy.

## Cobertura da Onda 3 (estado após auditoria)

Testes focados dos legos:
- `tests/legos/test_code_executor_lego.py`
- `tests/legos/test_video_processor_lego.py`

Inclui agora:
- detecção de payload inseguro (`_has_unsafe_goal_payload`)
- bloqueio garantido antes de `subprocess.run` no fallback local
- branches de erro/timeout/openhands fallback

## Curativo aplicado (mecânico)

Arquivos alterados (pela frente de construção):
- `src/legos/code_executor_lego.py`
- `tests/legos/test_code_executor_lego.py`

Comportamento novo:
- `CodeExecutorLego._local_sandbox()` retorna erro `local_sandbox: unsafe_goal_payload` para payloads suspeitos.

Observação:
- Esse bloqueio reduz risco imediato, mas não transforma o fallback em sandbox real.

## Recomendação de cura definitiva (para frente de construção)

1. **Remover interpolação de string em `python -c` com dados de usuário.**
2. Trocar fallback local por uma destas opções:
   - execução em processo/container isolado com filesystem e network restritos;
   - runner com script fixo e entrada via arquivo/JSON validado (sem compor código executável com input livre).
3. Aplicar política explícita de path allowlist (`safe_paths`) para `video_path` e `output_dir`.
4. Pinning de modelo/artefato Whisper (cache interno/versionado) para reduzir risco de supply-chain em runtime.

## Resultado de regressão desta rodada

- Suite completa: **8653 passed, 4 skipped, 0 failed**
