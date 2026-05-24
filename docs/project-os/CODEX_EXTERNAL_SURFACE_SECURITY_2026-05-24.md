# CODEX External Surface Security Sweep — 2026-05-24

Branch: `feature/omnis-5waves-runtime-supreme`  
Mode: auditoria contínua (somente código commitado)  
Escopo: superfícies externas (mensageria, web research, browser, input externo)

## Executive Summary

- **P0:** não encontrado nesta varredura.
- **P1:** 2 riscos relevantes encontrados (Browser sandbox URL hardening; Research backend SSRF boundary por configuração).
- **P2:** 2 gaps de governança/política (approval parcial em outbound messaging; prompt-injection sem sanitização semântica).

---

## 1) ChannelMessengerLego (porta de envio externo)

Arquivo auditado: `src/legos/channel_messenger_lego.py`

### O que está correto
- Credenciais via `os.getenv` (`WA_API_TOKEN`, `TG_BOT_TOKEN` etc.); sem hardcode no módulo.
- Envio real só por `urllib.request` com payload JSON; sem `eval/exec`.
- Existe gate de approval para conteúdo de broadcast/massa (`_requires_broadcast_approval`).
- Há cobertura de comportamento atual em `tests/legos/test_channel_messenger_lego.py`.

### Achado
- **P2 (governança):** nem toda saída passa por approval gate; mensagens 1:1 em modo real seguem sem aprovação explícita.
  - Evidência: `send()` só bloqueia quando `_requires_broadcast_approval(spec.content)` é verdadeiro.
  - Teste já existente que comprova comportamento: `test_non_broadcast_real_flow_not_blocked_by_approval`.

### Impacto
- Menor segurança operacional para envios não classificados como broadcast.
- Risco de disparo indevido por automação (não massivo, mas externo).

### Recomendação (decisão de produto/construção)
- Introduzir `approval_mode` por canal/ambiente (`always`, `broadcast_only`, `never`), default seguro em produção.

---

## 2) ResearchConductorLego (porta de busca web)

Arquivo auditado: `src/legos/research_conductor_lego.py`

### O que está correto
- Query do usuário é URL-encoded (`urllib.parse.urlencode`) antes da chamada de busca.
- Input do tópico não injeta URL de destino; apenas parâmetro `q`.
- Não há execução de comando a partir do conteúdo coletado.

### Achado
- **P1:** backend de busca (`SEARXNG_URL`) aceita host privado/local sem validação (risco SSRF por configuração).
  - Evidência no teste de caracterização já existente:
    - `tests/legos/test_research_conductor_lego.py::test_searxng_backend_accepts_private_host_without_validation`.

### Impacto
- Se operador configurar `SEARXNG_URL` para endpoint interno, o serviço pode acessar rede interna.

### Recomendação (muda comportamento)
- Validar `SEARXNG_URL` com allowlist de esquema/host e bloqueio de loopback/link-local/private CIDR.

---

## 3) BrowserExecutorLego (porta de navegação)

Arquivos auditados:
- `src/legos/browser_executor_lego.py`
- `src/computer_use/sandbox.py`

### O que está correto
- Há validation hook (`SecuritySandbox.validate_url`) antes de navegar.
- Há gate para objetivos críticos em `dry_run=False`.
- Semáforo evita paralelismo excessivo de browser.

### Achado crítico de superfície (P1)
- **Sandbox URL atual não bloqueia**:
  - `localhost` / loopback
  - IPs privados (`10.x`, `172.16-31.x`, `192.168.x`)
  - esquema `file://`
  - (bloqueio atual é por substring de domínios sensíveis, não por parsing robusto de URL)

### Evidência (novos testes de caracterização)
- `tests/computer_use/test_sandbox.py`:
  - `test_validate_url_allows_localhost_characterization`
  - `test_validate_url_allows_private_ip_characterization`
  - `test_validate_url_allows_file_scheme_characterization`

### Impacto
- Possível navegação para recursos locais/internos por inputs externos ou automações encadeadas.
- Expõe vetor de coleta indevida de conteúdo local/rede interna.

### Recomendação (muda comportamento)
- Harden em `validate_url`:
  1. parse com `urllib.parse.urlparse`;
  2. allowlist de esquemas (`https` e opcionalmente `http` somente em dev);
  3. bloqueio explícito de `file`, `data`, `javascript`, `about`, `chrome`;
  4. resolução de hostname + bloqueio de loopback/private/link-local/multicast/reserved.

---

## 4) Input externo → comando/goal executável

### Pontos revisados
- `src/remote_control/webhook_gateway.py`
- `src/remote_control/pipeline.py`
- `src/remote_control/whitelist.py`
- `src/remote_control/security.py`
- `src/remote_control/command_dispatcher.py`
- `src/execution_graph/runner.py`
- `src/agentic/skill_runner_bridge.py`

### Conclusão
- Não foi encontrado caminho direto de `eval/exec` a partir de payload inbound.
- Inbound remoto passa por parsing + classificação de risco + whitelist + trusted source + gate de aprovação.
- `upstream_context` flui como texto/hint (não como comando executável direto).

### Risco residual (P2)
- Prompt-injection semântica (conteúdo web/mensagem pode influenciar decisão textual de agentes).
- Não é RCE, mas pode desviar objetivo/qualidade.

---

## Prioridades P0/P1/P2

### P0
- Nenhum achado nesta varredura.

### P1
1. Browser sandbox URL hardening (bloquear `file://`, localhost, IP privado e esquemas perigosos).
2. Validação de `SEARXNG_URL` contra SSRF por configuração.

### P2
1. Política de approval parcial no ChannelMessenger (somente broadcast).
2. Defesa de prompt-injection semântica (sanitização/política de confiança por fonte).

---

## Testes e regressão desta varredura

Focados executados:
- `tests/computer_use/test_sandbox.py`
- `tests/legos/test_channel_messenger_lego.py`
- `tests/legos/test_research_conductor_lego.py`
- `tests/legos/test_browser_executor_lego.py`

Regressão completa:
- `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`

Status esperado após merge desta auditoria:
- Sem alteração de comportamento de produção.
- Somente caracterização de risco e evidência de superfície externa.
