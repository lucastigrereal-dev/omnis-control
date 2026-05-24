# CODEX Security Audit — Onda 6 (Legos Waves 2-6)

Data: 2026-05-23  
Branch: `feature/omnis-5waves-runtime-supreme`  
Escopo auditado (commitado): Browser / Code / Video / Research / Channel Legos + CLI Lego

## 1) Veredito RCE (CodeExecutorLego) — PRIORIDADE MÁXIMA

## Resultado
**RCE via interpolação de `goal` em `python -c` está CURADO no caminho local atual.**

## Evidência técnica
1. No `src/legos/code_executor_lego.py`, o script passado para `python -c` é estático e **não** concatena `spec.goal`.
2. `goal` e `output_dir` entram como argumentos posicionais (`argv`) após `--`, não como código.
3. Payload malicioso com quebra de linha e sintaxe de injeção é bloqueado antes do subprocess.

## Evidência em testes
- `test_local_sandbox_blocks_unsafe_payload_before_subprocess`
- `test_newline_injection_blocked`
- `test_semicolon_rm_injection_blocked`
- `test_dollar_paren_injection_blocked`
- `test_backtick_injection_blocked`
- `test_local_sandbox_uses_argv_not_goal_interpolation` (adicionado nesta rodada)

## Conclusão
No vetor específico previamente explorado (injeção por interpolação de `goal` no `python -c`), não há caminho explorável identificado nesta revisão.

---

## 2) ChannelMessengerLego (WhatsApp/Telegram)

## Achados
1. **Approval gate existe**, porém condicionado a conteúdo tipo broadcast/massa:
   - bloqueia em `dry_run=False` quando conteúdo contém keywords de disparo em massa.
   - não bloqueia mensagens normais (comportamento atual).
2. Credenciais estão via `os.getenv` (`WA_API_TOKEN`, `TG_BOT_TOKEN`, etc.), sem hardcode de segredo no código auditado.
3. Input de mensagem não é executado como código (sem `eval/exec/os.system/subprocess` com conteúdo externo).

## Risco residual
- Se a política desejada for “nenhum envio real sem aprovação humana”, o comportamento atual ainda está mais permissivo (decisão de produto/governança, não correção mecânica).

---

## 3) ResearchConductorLego (SSRF / URL boundary)

## Achado
- `SearXNGBackend` usa `SEARXNG_URL` sem validação de host/rede.
- Não há bloqueio explícito para hosts internos (`127.0.0.1`, `169.254.*`, `10.*`, etc.).

## Classificação
- **Risco médio (P1/P2 arquitetural)**: potencial SSRF/config misuse via ambiente comprometido.
- Não catastrófico imediato no fluxo default, mas merece hardening na frente de construção.

## Evidência em teste de caracterização
- `test_searxng_backend_accepts_private_host_without_validation` (adicionado nesta rodada).

---

## 4) Cobertura (Browser, Code, Video, Research, Channel)

Observação: não foi possível extrair porcentagem de cobertura por linha nesta máquina porque `pytest-cov` e `coverage.py` não estão instalados.

Mesmo assim, a cobertura funcional foi ampliada com novos testes de branch:

### Novos testes adicionados nesta rodada
- `tests/legos/test_code_executor_lego.py`
  - `test_local_sandbox_uses_argv_not_goal_interpolation`
- `tests/legos/test_browser_executor_lego.py`
  - `test_health_check_false_when_playwright_unavailable`
- `tests/legos/test_research_conductor_lego.py`
  - `test_searxng_backend_accepts_private_host_without_validation`
- `tests/legos/test_channel_messenger_lego.py`
  - `test_non_broadcast_real_flow_not_blocked_by_approval`

## Resultado dos testes
- `tests/legos/test_code_executor_lego.py` → 27 passed  
- `tests/legos/test_browser_executor_lego.py` → 18 passed  
- `tests/legos/test_research_conductor_lego.py` → 29 passed  
- `tests/legos/test_channel_messenger_lego.py` → 33 passed  
- `tests/legos/` → 157 passed  
- Suite completa `tests/` → **8752 passed, 4 skipped, 0 failed**

---

## 5) Recomendação objetiva para Claude Code (frente de construção)

1. **Research SSRF hardening**  
   - validar `SEARXNG_URL` com allowlist de host/scheme/port.
   - bloquear ranges internos por padrão (loopback/link-local/private), com override explícito.

2. **Policy de aprovação do ChannelMessenger**  
   - decidir se envio real normal também exige approval gate.
   - se sim, mudar regra de broadcast-only para gate obrigatório em `dry_run=False`.

