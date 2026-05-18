# OMNIS Local Supreme — Prompt do Operador
**Colar este prompt no Claude Code ao iniciar operação OMNIS**

---

Você está operando o OMNIS Local Supreme.

**Estado atual (2026-05-18):**
- 11 fases concluídas (0-10)
- 30 outputs reais em missions/MIS-20260518-002 a MIS-20260518-006
- Cockpit em cockpit/index.html
- Capacidades: Content Factory, Design Engine, Video Engine, App Factory, Capability Forge
- Branch: feature/omnis-5waves-runtime-supreme | Commit: cbd273f

**REGRAS ABSOLUTAS:**

1. Não conecte APIs externas (Instagram, Meta, WhatsApp, Notion, Gmail)
2. Não publique, não envie, não faça deploy
3. Não leia .env ou secrets/
4. Não delete arquivos sem approval explícito
5. Não faça git push sem autorização do operador
6. dry_run=True como padrão universal

**TODA MISSÃO deve gerar:**
- mission_contract.json
- mission_brief.md
- execution_plan.md
- outputs/ com arquivos reais
- relatorio_final.md

**ANTES de criar algo novo:**
1. Verificar se capacidade já existe em docs/OMNIS_CAPABILITY_CATALOG.md
2. Verificar outputs existentes em missions/
3. Só criar novo se não existe

**AÇÕES PERIGOSAS param em approval:**
- qualquer delete
- qualquer push
- qualquer integração externa
- qualquer alteração em src/ sem teste

**SEMPRE terminar com:**
- próximos 3 passos concretos
- como testar o output gerado
- o que está pronto para uso humano hoje

**Para operar:**
- Campanha: "Crie missão Content Factory para [perfil] tema [X]"
- Carrossel: "Crie missão Design Engine tema [X] perfil [Y]"
- Reels: "Crie missão Video Engine tema [X]"
- App: "Crie missão App Factory app [nome]"
- Skill: "Crie missão Capability Forge skill [nome]"
- Cockpit: abrir cockpit/index.html no browser
- Índice: ver docs/OMNIS_LOCAL_SUPREME_OUTPUT_INDEX.md
- Manual: ver docs/COMO_USAR_OMNIS_LOCAL_SUPREME.md
