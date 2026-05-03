# DECISOES OFICIAIS — OMNIS / JARVIS / ARGOS

**Data:** 2026-05-03
**Fonte:** Lucas Tigre (Tigrão)
**Status:** Oficial — substitui qualquer decisão anterior conflitante.

---

## D001 — Nome oficial

**Decisão:**
- O sistema operacional atual se chama **OMNIS**.
- O repositório oficial é **omnis-control**.
- `omnis.py` é o entrypoint principal.
- `jarvis.py` permanece como alias legado com aviso de depreciação.
- Jarvis é visão/conceito legado. OMNIS é a cabine operacional atual.

**Motivo:** Unificar nomenclatura e eliminar ambiguidade entre Claude Code e operador.

---

## D002 — ARGOS não é projeto novo

**Decisão:**
- ARGOS é a camada de publicação/agendamento Instagram, DENTRO do Publisher OS + OMNIS.
- Não criar outro publisher, Instagram Publisher, Publish OS, ou Argos do zero.
- OMNIS prepara drafts, calendários, legendas, status e exports.
- Publisher OS/ARGOS executa publicação quando integrações estiverem prontas.

**Motivo:** Evitar fragmentação. Publisher OS já existe com FastAPI, scheduler, queue, worker.

---

## D003 — Publisher OS não será alterado nesta fase

**Decisão:**
- Não mexer no Publisher OS.
- Não alterar containers, código, configuração ou dados do Publisher OS.
- Publisher OS só será acionado depois que OAuth/credenciais estiverem resolvidos.

**Motivo:** Publisher OS é motor operacional estável. Alterar agora arrisca a operação.

---

## D004 — 9 setores operacionais, 14 é visão futura

**Decisão:**
- Os 9 setores atuais em `config/sectors.yaml` são a versão operacional enxuta.
- Os 14 setores do blueprint são visão futura.
- Não expandir para 14 agora.
- Design fica dentro de `marketing_enterprise` como subcapacidade.
- Publicação/ARGOS fica dentro de `marketing_enterprise` + `automation_integrations`.
- Relacionamento/DM só depois do OAuth base.
- Criação de Skills e Setores são meta-processos em `app_factory` + `runtime_agentic`, não setores.

**Motivo:** Blueprint é mapa, não backlog imediato.

---

## D005 — R1 (modularização real do CLI) não agora

**Decisão:**
- R0-lite (plano) está aceito.
- R1 (extração real dos comandos) não será executada agora.
- Não modularizar `cli.py` nesta rodada.

**Motivo:** Prioridade atual é operação: assets, approvals, argos_drafts, diagnóstico, disco.

---

## D006 — Regras absolutas

**Decisão:**
- Não quebrar testes existentes.
- Não refatorar tudo agora.
- Não mexer em Docker.
- Não mexer no Publisher OS.
- Não chamar APIs externas.
- Não ler `.env`.
- Não criar arquitetura infinita.
- Não criar pastas vazias sem uso.
- Não criar outro Publisher ou Jarvis paralelo.
- Tudo deve ser local, testável e reversível.

---

## D007 — Aprovação manual é rotina operacional

**Decisão:**
- Aprovação de conteúdo deve ser facilitada via CLI.
- Frequência ideal: diária. Mínimo: 2x por semana.
- Criar comandos que agilizem a revisão em lote.

---

## D008 — Disco crítico é P0

**Decisão:**
- Disco abaixo de 10% é incidente operacional P0.
- Qualquer build, Docker ou log pode falhar.
- Não apagar nada automaticamente.
- Não rodar prune sem confirmação explícita.

---

## D009 — Memory-write local primeiro

**Decisão:**
- Registro de aprendizado pós-execução em JSONL local (`data/mission_learnings.jsonl`).
- Akasha/Qdrant ficam para fase futura (Fase 4+).

---

## D010 — OAuth Meta é fase separada

**Decisão:**
- OAuth Meta não será executado nesta fase sem autorização explícita.
- Fase futura específica: `META-0 — OAuth Readiness & Manual Token Setup`.
- Agora: apenas documentação e runbook.

---

## D011 — Claude Code continua desenvolvendo OMNIS

**Decisão:**
- Claude Code continua criando e modificando arquivos dentro de missões delimitadas.
- Lucas opera e valida. Claude Code desenvolve.
- Missões curtas, entregáveis concretos, sem invenção.

---

## D012 — Critério para virar "Manus executor"

**Decisão:**
OMNIS será considerado "Manus executor" quando conseguir:
1. Receber missão
2. Planejar
3. Puxar contexto
4. Gerar output
5. Passar por aprovação
6. Preparar entrega
7. Registrar logs
8. Repetir processo com pouca intervenção

---

## D013 — Protocolo 15-15-20

**Decisão:**
O protocolo 15-15-20 vira artefato operacional:
- `docs/PROTOCOLO_15_15_20.md`
- `docs/templates/15_15_20_TEMPLATE.md`
- Futuro comando CLI (não obrigatório agora)

---

## D014 — Setores transversais

**Decisão:**
- `security_audit` é transversal — monitora todos os setores.
- `mission_control` é o cockpit — display do sistema, não setor de produção.

---

## Histórico

| Data | Decisão | Mudança |
|------|---------|---------|
| 2026-05-03 | D001-D014 | Definições oficiais iniciais |
