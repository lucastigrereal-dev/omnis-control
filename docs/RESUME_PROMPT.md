# PROMPT DE RETOMADA — OMNIS SUPREME

Cole este prompt em nova sessão Claude Code no diretório `omnis-control`:

---

```
Contexto: estamos construindo o OMNIS Supreme — sistema agentic de 30 agentes que transforma missões em pacotes entregues.

Roadmap completo está em: docs/OMNIS_SUPREME_ROADMAP.md
Estado salvo em: ~/.claude/projects/C--Users-lucas-omnis-control/memory/project_omnis_supreme_roadmap.md

O que já existe (não reescrever):
- omnis-appfactory/src/ tem execution_graph/, squad_composer/, mission_orchestrator/, skills_bridge/, capability_forge_real/, providers/ — tudo funcional
- 16 skills funcionais em ~/.claude/skills/ e omnis-control/skills/
- Providers: Langfuse, Akasha pgvector, TFIDF embedding, LangGraph ativos
- Suite passa 165/165, CRM container healthy
- Branch: feature/omnis-5waves-runtime-supreme

Regra: OMNIS executa e entrega pacote local. Lucas posta. Sem conexão externa.

Estrutura de missão:
missions/<MISSION_ID>/
  mission_contract.json
  01_mission_brief.md → 10_learnings.md
  relatorio_final.md

PRÓXIMA WAVE: W-A1
Criar src/agentic/mission_engine.py no omnis-appfactory com:
- Gera MISSION_ID único (ex: MIS-20260518-001)
- Cria pasta missions/<id>/ com subpastas 05_outputs/, 06_exports/, 07_approval/, 08_logs/
- Gera mission_contract.json com: id, timestamp, status=open, setor, objetivo, criado_por
- Método open_mission(objetivo, setor) → MissionContract
- Método close_mission(id) → atualiza status=closed, fecha timestamp
- Testes em tests/agentic/test_mission_engine.py

Depois W-A1 passar: W-A2 (mission_intake.py), W-A3 (deliverable_mapper.py), W-A4 (report_generator.py), W-A5 (CLI).

Execute W-A1 agora.
```
