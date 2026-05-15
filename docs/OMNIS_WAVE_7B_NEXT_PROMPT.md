# OMNIS WAVE 7B — NEXT EXECUTOR PROMPT

**STATUS: NAO EXECUTAR AINDA — AGUARDAR AUTORIZACAO EXPLICITA**

---

Quando autorizado, cole o prompt abaixo:

```
VOCE E A ABA 3 — OMNIS WAVE 7B EXECUTOR.

AUTORIZACAO EXPLICITA: EXECUTAR ONDA 7B — P37 A P42 EM SEQUENCIA CONTROLADA.

Contexto:
- Wave 7A concluida no master @ d550ad3
- 5428 testes passando
- Planejamento completo em: docs/OMNIS_WAVE_7B_RUNTIME_BRIDGE_PLANNING.md

Fases a executar em sequencia:
- P37: War Room Runtime Bridge (src/war_room_bridge/)
- P38: Skill Router Real Bridge (src/skills_bridge/ extendido)
- P39: Approval Runtime (src/approval_runtime/)
- P40: Akasha Event Sink (src/akasha_sink/)
- P41: Telegram Control Planning (docs only, zero codigo)
- P42: Observability, Rollback & Audit (src/observability/ extendido)

REGRAS ABSOLUTAS:
- Trabalhe somente em C:/Users/lucas/omnis-control
- NAO mexa em KRATOS
- NAO mexa em .kratos, exceto War Room reports/
- NAO faca push sem autorizacao
- NAO faca pull
- NAO faca rebase
- NAO use git add .
- NAO delete arquivos
- NAO instale dependencias
- NAO suba Docker
- NAO execute acao externa real
- NAO conecte APIs externas (Instagram, Gmail, GitHub)
- NAO conecte pgvector real (so file-backed/mock)
- NAO implemente bot Telegram (so docs)
- NAO execute shell commands reais
- dry_run=True como default universal

PASSO A PASSO:
1. Criar branch: feature/omnis-wave-7b-runtime-bridge a partir de master
2. Para cada fase P37→P42:
   a. Criar arquivos fonte
   b. Criar arquivos de teste
   c. Rodar testes da fase (pytest tests/<fase>/ -v)
   d. Rodar suite completa (pytest tests/ -q)
   e. Se tudo passar, commitar: feat(pXX): <descricao>
   f. Avancar para proxima fase automaticamente
3. Ao final, gerar: docs/OMNIS_WAVE_7B_FINAL_REPORT.md
4. Atualizar War Room: C:/Users/lucas/.kratos/war-room/status/aba-3-omnis.md
5. NAO fazer push — aguardar autorizacao

STOP CONDITIONS:
- Se teste falhar, PARE e diagnostique
- Se houver conflito, PARE e reporte
- Se remote divergir, PARE e reporte
- Se duvida de seguranca, PARE e reporte

Execute uma fase por vez. Nao pule etapas. Nao agrupe commits.
```
