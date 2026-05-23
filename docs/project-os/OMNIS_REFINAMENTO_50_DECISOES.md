# 🎯 OMNIS — RESPOSTAS DE REFINAMENTO (50 DECISÕES CANÔNICAS)

> Anexo ao `OMNIS_BLUEPRINT_CANONICO.md`. Resolve as 50 perguntas do preflight.
> Cada resposta é uma DECISÃO FECHADA — o Claude Code executa sem rediscutir.
> Onde uma decisão vira tarefa nova, ela recebe ID e entra no backlog.

| Campo | Valor |
|---|---|
| **Versão** | 1.0 — Refinamento pós-preflight |
| **Data** | 2026-05-22 |
| **Contexto** | Preflight T-000 revelou 60 falhas em 8 clusters (vs 2 esperadas). Ver D-Q3. |
| **Regra** | Estas respostas têm a mesma autoridade do blueprint. Conflito → vence a mais recente (esta). |

---

## ⚠️ ACHADO CRÍTICO DO PREFLIGHT (ler primeiro)

O baseline mostrou **8786 passed / 60 failed**, mas o `CURRENT_STATE.md` de 2026-05-18 registrava só 2 falhas. Surgiram **~948 testes novos e 58 falhas sem ticket**, na branch `feature/kratos-0-10-operational-truth`. O blueprint assumia "falhas pré-existentes conhecidas" — **57 dessas NÃO eram conhecidas.**

**Decisão:** Wave 0 ganha a tarefa **T-006 — Triagem dos 8 clusters de falha** (detalhada em D-Q3). Nenhuma wave de feature avança até T-006 classificar cada cluster como `corrigir-agora | débito-aceito-com-ticket | descartar`. Isso é a lei nº4 (identifique conflitos) em ação.

---

# BLOCO A — 30 RESPOSTAS ESTRUTURAIS

## Bloco 0 — Identidade

**D-Q1 — Falta uma lei sobre ritmo?**
Sim, falta. Adicionar a **Lei nº7: RITMO.** "Uma wave por vez. Não iniciar wave N+1 antes do gate N estar verde. Não abrir frente paralela sem o `omnis-orchestrator` autorizar. Atropelar gate é como construir o segundo andar antes da laje do primeiro curar — desaba." Incorporar ao Bloco 0 do blueprint.

**D-Q2 — 7 personas diluem ou especializam?**
Especializam SE usadas como lente, não como comitê. Decisão: **persona primária por wave + 2 secundárias.** Mapa:
- Wave 0/1 (higiene+core) → primária: Runtime Infrastructure Engineer; secundárias: Systems Architect, Product Strategist.
- Wave 2 (integrações+memória) → primária: Knowledge Architect; secundárias: AI Orchestration, Systems Architect.
- Wave 3 (automações IG) → primária: Product Strategist; secundárias: AI Orchestration, Human Workflow Designer.
- Wave 4 (otimização) → primária: AI Orchestration Engineer; secundárias: Runtime, OSS Researcher.
As 7 continuam disponíveis; o que muda é qual lidera a decisão. Comitê de 7 vozes paralisa; uma lidera e duas conferem.

## Bloco 1 — Verdade Atual

**D-Q3 — 129 arquivos sem cobertura: débito ou coberto?**
Reclassificado pelo preflight. Não são 129 sem cobertura — são **60 testes FALHANDO**. Criar **T-006 (P1, Wave 0): Triagem de falhas.** Para cada um dos 8 clusters, o `test-guardian` classifica:
- `capability_forge_real` (28 falhas) → **CORRIGIR AGORA.** É o coração da auto-evolução (skills sob demanda). Se a Forge está quebrada, a Wave 3 inteira morre. Vira T-006a, P1.
- `skill_router_bridge` (9) → **CORRIGIR AGORA.** Roteamento de skill é caminho crítico. T-006b, P1.
- `observability` (7) + `integration` (1) → **CORRIGIR.** AuditTrail quebrado = perda de rastreabilidade (RNF3). T-006c, P1.
- `omnis_health` (3) → já era T-105. Mantém.
- `checkers` (4) + `execution_graph` (1) → **DÉBITO ACEITO COM TICKET** (Docker CLI + format). Não bloqueiam core. T-006d, P3.
- `e2e/skill_runner` (4) → **CORRIGIR config.** Procura skills em `~/.claude/skills/` em vez de `omnis-control/skills/`. É path errado, conserto barato. T-006e, P2.

**D-Q4 — Quem garante que imports do akasha/ não quebram ao mover?**
Ninguém ainda — por isso a absorção (T-201) tem protocolo obrigatório: (1) `grep -r "import akasha\|from akasha"` mapeia todos os imports antes de mover; (2) mover com `git mv` preservando histórico; (3) atualizar imports com sed + revisão; (4) rodar suite do akasha-paperless-brain; (5) só commitar se verde. Rollback: `git revert`. Sem esse protocolo, T-201 não começa.

**D-Q5 — Worktrees zumbi: quando/por quê criados, como evitar acúmulo?**
Foram criados como mecanismo de paralelismo (uma worktree por frente de wave) e não foram limpos após merge. Decisão: **TTL automático.** Criar T-007 (P2): script `omnis_worktree_audit.py` que flagga worktree sem commit há >7 dias e sem branch ativa no registry. Roda no checklist de fim de wave. Worktree é andaime — tira quando a parede está de pé.

## Bloco 2 — Arquitetura

**D-Q6 — Como o Lucas aprova ação do cockpit se KRATOS só lê?**
Via **OMNIS CLI exclusivamente**, no curto prazo. O KRATOS mostra a aprovação pendente (lê de `07_approval/approval_status.json`), mas o Lucas digita o GO no terminal OMNIS (`omnis approve MIS-xxx`). Médio prazo (Wave 4): KRATOS pode ter um botão que dispara um webhook **assinado** pro OMNIS — mas isso é a única escrita permitida, e passa pelo Approval Gate como qualquer ação. Até lá, CLI é a verdade.

**D-Q7 — Ollama falha: fallback automático ou trava?**
**Fallback automático para Sonnet, COM teto.** O `model_router.py` já tem `fallback.py`. Regra: Ollama falha → tenta Sonnet → registra no CostTracker como "fallback forçado". MAS: se fallbacks forçados passarem de X% do dia (sugiro 20%), o sistema alerta o Lucas ("teu Ollama está instável, está queimando crédito"). Trava nunca — missão não pode morrer por infra local. Mas estouro silencioso de custo também não. Ver D-Q44.

**D-Q8 — JSONL cresce infinito? Plano de rotação.**
Sim, cresceria. Decisão: **rotação por missão + compactação.** Cada missão tem seu `08_logs/` isolado. Criar T-008 (P2): política de retenção — logs de missões concluídas há >30 dias são compactados (`.jsonl.gz`) e movidos para `data/archive/`. O event bus ativo só mantém missões abertas + últimas 30 dias. Disco a 26% não é desculpa pra deixar crescer.

**D-Q9 — Automatizar a Matriz de Governança com Ollama?**
Sim — **classificação inicial automática, decisão final humana.** O Ollama local roda a primeira passada (skill? capability? core? feature-fantasma?) e propõe. O Lucas (ou o `omnis-orchestrator` em ações de baixo risco) confirma. Custo zero, e tira do Lucas o trabalho de classificar manualmente cada item. É exatamente o tipo de tarefa barata que justifica Ollama. Vira parte da skill `jarvis-decide`.

**D-Q10 — Quem audita que o CostTracker não é bypassado? Tem teste que força CostLimitError?**
O `errors.py` já tem `CostLimitError`. Decisão: criar **T-009 (P1): meta-teste de roteamento.** (1) Teste que força CostLimitError ao estourar limite. (2) Teste de arquitetura (lint custom) que falha o build se QUALQUER arquivo em `src/` importar `anthropic`/`openai` direto sem passar pelo `model_router`. Isso fecha o bypass na raiz — não dá pra furar o router se o build não deixa.

## Bloco 3 — Repositórios

**D-Q11 — Qual a stack real do akasha-paperless-brain?**
Não foi clonado no preflight (só os dois principais). Decisão: **T-201 começa com inspeção, não com mudança.** Primeiro passo da absorção é `clonar + ls + cat README/package.json/pyproject.toml` pra cravar a stack. Hipótese baseada no nome ("paperless" = paperless-ngx, que é Python/Django + Postgres): provavelmente Python + Docker Compose. Mas **validar antes de assumir** (lei nº1). O Claude Code reporta a stack real ao Lucas antes de mover qualquer arquivo.

**D-Q12 — Absorção do omnis-server inclui Caddy? Domínio/cert existe?**
A absorção inclui o **esqueleto** do Caddy (config template), não um cert real. Decisão: local-first não precisa de domínio nem cert agora — Caddy roda com `localhost` e cert interno. Domínio + cert público é tarefa da Wave 4 (quando for expor algo), e é ação humana do Lucas (comprar domínio). Por ora: `deploy/Caddyfile` aponta pra `localhost`, e fica documentado que produção exige domínio.

**D-Q13 — Plano de rollback se a absorção quebrar o Akasha?**
Protocolo de absorção segura (vale pra T-201 e T-202): (1) trabalhar em branch dedicada `feature/absorb-akasha`; (2) NUNCA deletar o `akasha/` original até o novo `core/` passar na suite — só copiar; (3) suite verde no destino → commit; (4) suite quebrada → `git checkout .` e o original intacto continua sendo a verdade; (5) só remover o `akasha/` original numa wave SEPARADA, após confirmação de que o `core/` roda em produção por alguns dias. Rollback = o original nunca foi tocado até ter certeza. Cinto e suspensório.

## Bloco 4 — PRD

**D-Q14 — `omnis mission "X"` já existe ou é target?**
**Já existe** — confirmado no relatório Supreme (Gate da Fase A: `omnis mission "cria campanha hotel"` cria a estrutura). É funcional. RF1 é validação, não construção. T-101 confirma que ainda funciona após as mudanças de branch.

**D-Q15 — "≥75% local" — medido como?**
**Por chamada de modelo** (a unidade que o CostTracker já registra). Fórmula: `chamadas_local / chamadas_totais` num período. Não por token (engana — uma chamada Opus longa pesaria igual a uma Ollama curta) nem por tarefa (vaga). O CostTracker já loga `provider` por chamada — só somar. Meta diária ≥75%, alvo Wave 4 ≥85%.

**D-Q16 — Ollama é 100% offline? Modelos baixados?**
Sim, SE os modelos já estiverem baixados (`ollama pull` feito uma vez, com internet). Decisão: criar **T-010 (P1, Wave 0): garantir modelos base baixados** — `llama3.1:8b` (geral) + `qwen2.5-coder:7b` (código) + modelo de embedding (`nomic-embed-text`). Depois disso, 100% offline. Adicionar `ollama list` ao state_check pra alertar se faltar modelo. Sem isso, "local-first" é só promessa.

**D-Q17 — Quantos dos 55+ endpoints do Contract V1 já retornam envelope?**
Desconhecido — não foi medido no preflight. Decisão: **T-205 começa com auditoria.** Primeiro passo é script que bate em cada endpoint e checa se a resposta tem `source`/`data`/`meta`. Gera um relatório `endpoints_envelope_audit.md`. Só depois corrige os que faltam. Medir antes de corrigir (lei nº1).

## Bloco 5 — Roadmap

**D-Q18 — Docker funcional? 18 containers?**
Disco confirmou 26.6% livre, mas o status do Docker não foi checado no preflight. Decisão: adicionar `docker ps` + `docker info` ao **T-005**, e ao state_check. Os 18 MCPs/containers do memory são alvo, não realidade confirmada. T-005 reporta quantos sobem de fato. Se o Docker Desktop não estiver rodando, isso é o primeiro a resolver na Wave 0.

**D-Q19 — Indexar 20K notas em Ollama: estimativa de tempo?**
Realista: **horas, possivelmente uma noite.** ~20K notas × embedding local. Decisão: T-203 roda em **batch noturno, idempotente e retomável** — se cair, retoma de onde parou (checkpoint a cada 500 notas). Não trava nenhuma outra wave (roda em background). E é one-time: depois só indexa o delta (notas novas/editadas). Rodar com `nomic-embed-text` (rápido e local). Não é gargalo se for assíncrono.

**D-Q20 — OAuth Meta bloqueia Waves 3 e 4 inteiras. Plano B?**
Sim, e o plano B é **essencial pra não travar tudo esperando o Lucas/Meta.** Decisão: **toda a Wave 3 desenvolve contra um Publisher MOCK primeiro.** O `browser_executor` já nasceu "mock-first" — mesma filosofia. O pipeline gera o conteúdo, agenda, e "publica" num sandbox que grava o que SERIA postado. Quando o OAuth Meta entrar (T-206), troca o mock pelo real numa linha. Assim Wave 3 e 4 avançam sem depender da burocracia da Meta. Desbloqueio total.

**D-Q21 — Qual perfil piloto?**
**@afamiliatigrereal (320K, família).** Confirmado como candidato e faz sentido: nicho família é evergreen, menos volátil que viral puro, e 320K é grande o suficiente pra monetizar mas não tão grande que um erro custe caro. É o tamanho certo pra piloto. Os outros 5 entram na Wave 4 (escala).

**D-Q22 — DM chatbot: API oficial ou browser automation?**
**API oficial (Meta), via mesmo OAuth da publicação.** Browser automation pra DM é frágil e arrisca ban da conta — risco alto demais pra um ativo de 320K seguidores. Decisão: DM chatbot espera o OAuth Meta (T-206) e usa a Instagram Messaging API oficial. Até lá, desenvolve contra mock (como D-Q20). Nunca arriscar a conta com automação não-oficial.

## Bloco 6 — Backlog

**D-Q23 — O que trava se o Lucas nunca rotacionar a chave (T-001)?**
Em segurança: a chave exposta continua um risco (qualquer um com acesso ao histórico do repo pode usá-la e queimar TEU crédito). Em execução: **quase nada trava** — o sistema é local-first e roda em Ollama sem a chave. Decisão: T-001 é P0 de SEGURANÇA, mas não bloqueia o desenvolvimento local. O Claude Code pode avançar Wave 0 (higiene) e Wave 1 (core, testável com mock) sem ela. A chave só é necessária quando for fazer chamada cloud real (Sonnet/Opus em produção). Então: importante, mas não é gargalo de execução.

**D-Q24 — Containers essenciais ou auxiliares, se é in-memory first?**
**Auxiliares no dev, essenciais em produção.** O princípio "in-memory first" significa que o CÓDIGO roda com adapters mock/memória pra testar. Os containers (Postgres, Qdrant, Neo4j, Redis) são a camada de persistência REAL. Decisão: desenvolvimento e testes usam in-memory (rápido, sem dependência); execução real de missão usa os containers. T-005 sobe os containers pra que a execução real funcione, mas a suite de testes não depende deles. Os dois mundos coexistem.

**D-Q25 — T-301→302→303 dependem de T-206 (OAuth). Paralelizar?**
Sim — resolvido por D-Q20. Com o Publisher mock, T-301/302/303 desenvolvem em paralelo ao T-206 (que é ação humana do Lucas). Decisão: **desacoplar.** T-301/302/303 dependem do MOCK (que existe na hora), não do OAuth real. T-206 só é pré-requisito da PUBLICAÇÃO REAL, não do desenvolvimento. Wave 3 não espera a Meta.

**D-Q26 — Quais tarefas sobram nos 15% cloud (meta 85% local)?**
As que exigem qualidade que o Ollama 8B não entrega: **copy criativa final de alto valor** (a legenda do post que vai pra 320K pessoas), **decisão arquitetural** (raro), e **fallback quando Ollama instável**. Tudo que é classificação, parse, rascunho, extração, teste → local. O cloud fica pro "última milha de qualidade" onde engajamento (= receita) está em jogo. Ver D-Q36 pro critério.

## Bloco 7 — Execução

**D-Q27 — Timeout 30s: por chamada ou por tarefa? Ollama pode estourar.**
**Por chamada, e diferenciado por tipo.** 30s é pra chamada de geração comum. Embedding de nota longa ou batch é outra categoria — timeout de 120s+ ou sem timeout (com checkpoint, como D-Q19). Decisão: o `model_router` recebe um parâmetro `timeout_class` (fast=30s / heavy=120s / batch=sem limite com checkpoint). Não é one-size-fits-all. Tarefa pesada local não pode morrer por um timeout pensado pra chamada rápida.

**D-Q28 — Quem audita print() residual? Tem lint rule?**
Não tem ainda. Decisão: parte de **T-009** (o meta-teste de arquitetura). Adicionar regra de lint (ruff/flake8) que falha o build se houver `print(` em `src/` (exceto CLI, onde `Rich.console` é o padrão e print é permitido em arquivos marcados). Build vermelho = print residual pego antes do commit. Automatiza a vigilância.

**D-Q29 — Wave 100% local: sucesso ou não testou o routing?**
**Sucesso, MAS com nuance.** Se uma wave usou 0% LLM (tudo determinístico/local), o CostTracker mostrar 100% local é o resultado IDEAL. Não significa que não testou o routing — o routing foi testado pelo T-009 (meta-teste dedicado), não por cada wave. Decisão: separar as duas coisas. "Custo da wave" mede economia (100% local = ótimo). "Routing funciona" é garantido pelo T-009 uma vez, não a cada wave. Não confundir economia com cobertura de teste.

**D-Q30 — cost_local_pct numa wave 100% local como T-000: basta "100%"?**
Sim, mas com a ressalva honesta que o próprio Claude Code já fez: a EXECUÇÃO foi 100% local; só a RESPOSTA escrita pro Lucas usou Sonnet. Decisão: o campo reporta o custo da EXECUÇÃO (o trabalho), não da comunicação. Formato: `cost_local_pct: "100% (execução); resposta ao operador via Sonnet"`. Transparente e preciso. Foi exatamente o que ele reportou ("~95%") — comportamento correto.

---

# BLOCO B — 20 RESPOSTAS PROFUNDAS (OPUS-LEVEL)

## Arquitetura Sistêmica

**D-Q31 — Falta um quarto corpo: quem treina? Loop de feedback?**
Achado certeiro. Os 3 corpos (OMNIS executa / KRATOS observa / Aurora interpreta) não fecham o loop de aprendizado. Decisão: o quarto corpo **já existe parcialmente** — é o `learning_writer.py` + Akasha. Formalizá-lo como **AKASHA = o corpo que LEMBRA E APRENDE.** Loop: Lucas corrige uma saída → a correção vira entrada estruturada (`10_learnings.md` + embedding no Akasha) → próxima missão similar recupera essa correção via `jarvis-brain`. Criar T-011 (P2, Wave 3): UI mínima de feedback no KRATOS ("essa saída foi boa? o que faltou?") que grava estruturado. Sem o loop fechado, o sistema repete erros. Memória = sistema nervoso inclui aprender com a dor.

**D-Q32 — Quem decide quando skill vira core? Threshold de uso?**
Sim, threshold automático. Decisão: **uma skill usada por ≥3 squads diferentes E com ≥20 execuções bem-sucedidas é candidata a promoção para core.** O `revenue-tracker`/observability já loga uso por skill. Quando o threshold bate, o sistema FLAGGA (não promove sozinho) — o `omnis-orchestrator` propõe ao Lucas. Promoção é decisão arquitetural (lei nº4: pare e reporte). Critério objetivo dispara; humano confirma. Evita tanto o sub-uso (skill que devia ser core mas vive isolada) quanto o over-engineering (promover cedo demais).

**D-Q33 — Quem é o árbitro OMNIS vs Aurora? Ex: Aurora sugere Sonnet, Router insiste em Ollama.**
**O Model Router vence em roteamento; Aurora vence em estratégia.** São domínios diferentes. Aurora interpreta O QUÊ fazer (estratégia, norte). O Router decide COM QUE MODELO fazer (mecânica de custo). Se Aurora diz "isso precisa de qualidade alta", ela seta uma flag `quality_required=true` na tarefa — e o Router respeita (sobe pra Sonnet). Mas Aurora não escolhe o modelo diretamente; ela declara o REQUISITO, o Router traduz em modelo. Separação de poderes: o legislativo (Aurora) define a necessidade, o executivo (Router) escolhe o meio mais barato que a atende. Conflito real → Lucas arbitra.

## Memória como Sistema Nervoso

**D-Q34 — Quem mantém consistência entre Postgres/Qdrant/Neo4j? IDs iguais?**
Ponto crítico de integridade. Decisão: **Postgres é a fonte de verdade dos IDs (source of truth).** Toda entidade nasce no Postgres com um `uuid`. Qdrant e Neo4j usam ESSE mesmo `uuid` como chave externa — nunca geram ID próprio. Escrita é transacional via uma camada única (`src/providers/semantic_memory.py` vira o ÚNICO ponto de escrita nos três). Nada escreve direto em Qdrant ou Neo4j sem passar por lá. Criar T-204 com esse contrato: um write = um uuid propagado aos três, ou rollback nos três. Sem fonte única de ID, vira três cérebros com memórias divergentes.

**D-Q35 — Akasha 606K chunks + 20K notas dobra volume. Qdrant 768d aguenta? Sharding?**
Sim, aguenta sem sharding por enquanto. Referência: Qdrant lida com milhões de vetores 768d em uma instância single-node confortavelmente; ~1.2M chunks está bem dentro do envelope. Decisão: **não fazer sharding agora (anti-overengineering, lei nº6 do Product Strategist).** Monitorar latência de query (já no envelope `meta.latency_ms`). Gatilho de sharding: query p95 > 200ms OU >5M vetores. Até lá, single-node + índice HNSW bem configurado resolve. Resolver problema que não existe ainda é desperdício. Mas instrumentar pra saber QUANDO vai existir.

## Economia de Crédito

**D-Q36 — Carrossel com copy Ollama vs Sonnet: diferença de engajamento mensurável? A/B test?**
A pergunta de ouro, porque conecta crédito a RECEITA. Decisão: **sim, A/B test, na Wave 3.** Criar T-012 (P2): o piloto (@afamiliatigrereal) posta metade do conteúdo com copy Ollama, metade com Sonnet, marcado no CRM/analytics. Após ~30 posts, compara engajamento. SE Ollama empata ou perde <5% → usa Ollama (economia total). SE perde muito → Sonnet só na legenda final. Deixa o DADO decidir, não o achismo. Essa é a régua que torna a economia de crédito uma decisão de negócio, não dogma. É o teu olhar de monetização aplicado ao próprio custo.

**D-Q37 — Limite do CostTracker é fixo ou adaptativo? Sobe se Lucas fatura R$500/dia?**
**Fixo por padrão, ajustável manualmente, NUNCA automático.** Decisão: limite automático que sobe com receita é perigoso — um dia bom não justifica queimar crédito no dia seguinte sem o Lucas decidir. O CostTracker tem teto fixo (ex: R$X/dia). Se a receita justifica subir, o Lucas sobe manualmente (uma linha de config). Razão: receita e custo de IA não são acoplados linearmente — você pode faturar R$500 com R$2 de crédito. Subir o teto automático destruiria a missão suprema de economia. Controle humano sobre o orçamento, sempre.

## Evolução e Autonomia

**D-Q38 — Forge cria skill, teste passa mas copy é ruim. Quem audita qualidade, não só sintaxe?**
O calcanhar de Aquiles da auto-evolução. Decisão: **dupla validação na Forge.** (1) Gate sintático: teste passa (já existe). (2) Gate de qualidade: a skill nova roda 3x num caso real e a saída é avaliada por um juiz (Sonnet, com rubrica) OU pelo Lucas em ações de alto valor. Skill que passa na sintaxe mas falha na qualidade fica em `quarentena` — registrada mas não disponível pra produção até aprovação. Criar T-013 (P2): quality gate na Forge. Teste verde ≠ skill boa. Pra um ativo de 320K seguidores, copy ruim é pior que skill ausente.

**D-Q39 — Quem calibra o risco? Se Lucas aprova 100% por 30 dias, sobe threshold pra ≥8?**
**Sim, mas com proposta + confirmação, nunca automático.** Decisão: o AutonomySupervisor LOGA o padrão de aprovação. Se o Lucas aprovou 100% das ações de risco 7 por 30 dias sem rejeitar nenhuma, o sistema PROPÕE: "você sempre aprova risco 7 — quer subir o gate pra ≥8 e parar de ser interrompido?". O Lucas confirma. Calibração dirigida por dado, decidida por humano. É como tirar as rodinhas da bicicleta: o sistema percebe que você não cai mais, mas você decide quando tirar. Subir threshold sozinho seria autonomia sem consentimento — proibido.

**D-Q40 — Que nível N0→N7 estamos hoje? Critério pra subir?**
Pelo estado atual (approval gate ativo, Lucas confirma ações de risco, sistema executa squads mas com supervisão): **estamos em ~N3** (executa com aprovação humana em pontos de risco). Critério pra N4: 30 dias de operação com taxa de rejeição <10% E zero incidente de guardrail violado. Cada nível sobe com track record + confirmação do Lucas (como D-Q39). Decisão: documentar a escala N0-N7 explicitamente com critério objetivo de cada salto, em `docs/project-os/AUTONOMY_LADDER.md` (T-014, P3). Hoje você dirige com a mão no volante; subir nível = soltar mais a mão, com prova de que o carro anda reto.

## Pipeline Instagram — o GAP real

**D-Q41 — Evergreen não dá mais receita; reels viral + collab dão. Roadmap cobre collab outreach?**
Correção aceita — e é o teu olho de monetização batendo no meu. Decisão: **expandir a Wave 3.** O evergreen é a BASE (consistência, SEO, autoridade), mas a RECEITA vem de reels + collab. Adicionar:
- T-015 (P2): skill `reels_viral_pipeline` (hook forte + ritmo de corte + trending audio) — reusa a lógica da pesquisa de video editor.
- T-016 (P2): skill `collab_outreach` (identifica perfis pra collab, gera proposta personalizada) — reusa a lógica do SDR. Os pacotes de venda (Starter R$350, Growth R$990, Premium R$1.200, CPM R$0,15) entram aqui como o produto que o outreach vende. Evergreen alimenta, viral+collab faturam. Roadmap corrigido.

**D-Q42 — Publer vs Argos: dois conectores? Qual canônico? Complementares?**
**Complementares, com papéis distintos.** Decisão: **Argos = fila/bridge interna** (o OMNIS empacota o conteúdo e entrega pro Argos, que é a camada de publicação interna). **Publer = scheduler externo** (agenda nas plataformas). Fluxo: OMNIS gera → Argos enfileira/valida → Publer agenda/posta. Argos é o canônico do LADO OMNIS (sempre passa por ele); Publer é uma opção de scheduler que o Argos pode usar (ou a API Meta direta). Não competem — são camadas. Documentar em T-205.

## Segurança e Resiliência

**D-Q43 — "Nunca ler .env" mas Router precisa de API keys. Como?**
Distinção precisa e importante. Decisão: o código **NUNCA abre/lê o ARQUIVO `.env`** (não faz `open('.env')`). Mas LÊ as VARIÁVEIS DE AMBIENTE (`os.getenv('ANTHROPIC_API_KEY')`) que foram carregadas no ambiente a partir do `.env` por uma ferramenta externa (python-dotenv no boot, ou export no shell). A regra protege contra: commitar o arquivo, logar seu conteúdo, parsear segredos. Não contra usar a variável injetada. O `model_router.py` já faz isso certo (`os.getenv`). Confirmar que NENHUM lugar faz `open('.env')` ou loga `os.environ` inteiro — parte do T-009.

**D-Q44 — Ollama cai em missão crítica: fallback automático pra cloud quebra limite de custo?**
Resolve o conflito entre D-Q7 (fallback automático) e D-Q37 (limite fixo). Decisão: **fallback respeita o limite, mas missão crítica tem reserva.** Hierarquia: (1) Ollama cai → tenta Sonnet (fallback). (2) Sonnet estouraria o limite diário → o sistema PARA e pergunta ao Lucas ("Ollama caiu, continuar em Sonnet vai estourar teu limite de hoje. Autoriza?"). (3) Exceção: missões marcadas `priority=critical` têm uma reserva de emergência (ex: 10% acima do limite) pra não morrer. Missão comum espera o Ollama voltar ou o Lucas decidir. Crítica usa a reserva. Custo controlado, missão protegida.

## Governança de Longo Prazo

**D-Q45 — WAVE_REGISTRY terá 100+ waves em 6 meses. Como evitar lista ilegível?**
Decisão: **arquivamento por época + visão viva.** Waves concluídas há >60 dias movem pra `WAVE_REGISTRY_ARCHIVE.yaml` (histórico, consultável). O `WAVE_REGISTRY.yaml` ativo só mostra: em andamento + próximas + concluídas recentes. Adicionar um `WAVE_REGISTRY_SUMMARY.md` gerado automaticamente (1 linha por época: "Waves 1-50: fundação+core, concluído 2026-05"). O KRATOS pode renderizar isso visualmente. Registry é diário de bordo — o de hoje fica na mesa, os antigos vão pra estante. T-017 (P3).

**D-Q46 — 8 worktrees (alguns stale) = modelo gera acúmulo. TTL automático?**
Já resolvido em D-Q5 (T-007: TTL de 7 dias, flag automático). Reforço aqui: o problema não é o paralelismo (worktrees são bons), é a falta de limpeza. O TTL + o checklist de fim de wave ("worktree desta wave foi removida?") fecham isso. Andaime que fica depois da obra pronta não é organização — é entulho.

**D-Q47 — Quem audita que EXECUTION_READY não é preenchido mecanicamente? Meta-teste?**
Risco real de teatro de governança. Decisão: criar **T-018 (P3): meta-validador de EXECUTION_READY.** Um script que pega os EXECUTION_READY das últimas N waves e checa: os arquivos listados em `files.created` existem mesmo? Os comandos em `test` rodam e passam? O `tests_passing` declarado bate com a realidade? Discrepância = flag. Isso pega o preenchimento mecânico (declarar "10/10 passando" quando rodou 8/10). Confiança é boa; verificação é melhor. O EXECUTION_READY do próprio T-000 foi honesto (reportou as 60 falhas) — esse é o padrão a manter.

## Sobre o Próprio Blueprint

**D-Q48 — Blueprint v1.0: processo de emenda? Lucas altera Bloco 5 sozinho? Claude propõe emendas?**
Decisão: **o Lucas é o constituinte (pode emendar qualquer bloco unilateralmente). O Claude Code é proponente (propõe emendas, não aplica sozinho).** Processo: (1) Claude Code identifica algo que o blueprint não previu → escreve uma proposta de emenda no formato `EMENDA-XXX` (o quê muda, por quê, impacto). (2) Lucas aprova/rejeita. (3) Aprovada → vira `OMNIS_BLUEPRINT_CANONICO.md v1.1` com changelog. Estas 50 respostas SÃO a primeira leva de emendas (geram T-006 a T-018). O blueprint é vivo, mas só o Lucas tem a caneta. Constituição com processo de emenda, não pedra.

**D-Q49 — "Conselho OMNIS" como autor implica múltiplos modelos. Qual foi o processo de síntese?**
Transparência total: o "Conselho OMNIS" é uma figura de linguagem pra a SÍNTESE AUDITADA, não literalmente vários modelos votando. O processo real foi: materiais de várias fontes (tuas pesquisas Perplexity/GPT + os repos + os relatórios) foram LIDOS, CRUZADOS contra o código vivo, e CONSOLIDADOS num documento único, com os conflitos resolvidos por decisão justificada. "Conselho" = a multiplicidade de fontes sintetizada numa voz canônica. Um humano (você) bateu o martelo nos conflitos. Não houve comitê de IAs — houve auditoria + síntese + tua validação. Honestidade sobre a autoria importa pra confiança no documento.

**D-Q50 — O que acontece com o OMNIS_SUPREME_EVOLUTION_REPORT.md (50 deliverables) da sessão anterior? Complementa, contradiz ou substitui?**
Decisão: **COMPLEMENTA como fonte histórica, mas o BLUEPRINT é a verdade arquitetural vigente onde houver conflito.** O EVOLUTION_REPORT é um snapshot do que foi feito (registro histórico, valioso). O Blueprint é o plano canônico do que SERÁ feito e como o sistema DEVE ser. Onde o report descreve algo que o blueprint redefine (ex: se o report assumia stack greenfield), o blueprint vence. Hierarquia de verdade: **Código vivo > Blueprint+Refinamento (este) > Relatórios históricos > Pesquisas externas.** O report vira input do Akasha (memória), consultável, mas não é mais a régua. Criar T-019 (P3): reconciliar o report com o blueprint, marcando explicitamente o que foi superado.

---

## 📋 NOVAS TAREFAS GERADAS (entram no backlog do blueprint)

| ID | Tarefa | Prioridade | Wave | Origem |
|---|---|---|---|---|
| T-006 | Triagem dos 8 clusters de falha (a–e) | P1 | 0 | D-Q3 |
| T-007 | TTL automático de worktrees (7 dias) | P2 | 0 | D-Q5/Q46 |
| T-008 | Política de retenção/rotação de logs JSONL | P2 | 1 | D-Q8 |
| T-009 | Meta-teste de roteamento + lint anti-bypass/print | P1 | 1 | D-Q10/Q28/Q43 |
| T-010 | Garantir modelos Ollama baixados (offline) | P1 | 0 | D-Q16 |
| T-011 | UI de feedback no KRATOS (loop de aprendizado) | P2 | 3 | D-Q31 |
| T-012 | A/B test copy Ollama vs Sonnet | P2 | 3 | D-Q36 |
| T-013 | Quality gate na Capability Forge | P2 | 3 | D-Q38 |
| T-014 | Documentar escala de autonomia N0-N7 | P3 | 3 | D-Q40 |
| T-015 | Skill reels_viral_pipeline | P2 | 3 | D-Q41 |
| T-016 | Skill collab_outreach | P2 | 3 | D-Q41 |
| T-017 | Arquivamento do WAVE_REGISTRY por época | P3 | 4 | D-Q45 |
| T-018 | Meta-validador de EXECUTION_READY | P3 | 4 | D-Q47 |
| T-019 | Reconciliar EVOLUTION_REPORT com blueprint | P3 | 1 | D-Q50 |

---

## ✅ ORDEM DE EXECUÇÃO ATUALIZADA (Wave 0 revisada)

```
T-000 (✅ feito)
   ↓
T-006 TRIAGEM DE FALHAS (P1) ──┬─→ T-006a forge (P1) ─┐
   │                           ├─→ T-006b router (P1) ─┤
   │                           ├─→ T-006c observ (P1) ─┼─→ suite limpa
   T-010 modelos Ollama (P1)   ├─→ T-006d débito (P3)  │
   T-007 TTL worktrees (P2)    └─→ T-006e skill path ──┘
   T-002/003/004/005 higiene
   ↓
GATE 0: suite com falhas P1 zeradas + débito P3 com ticket + Ollama offline OK
   ↓
WAVE 1 (core) → T-009 meta-testes → T-101..T-105
   ↓ ... segue o blueprint
```

> **Regra:** Wave 0 NÃO fecha com 60 falhas. Fecha com as P1 corrigidas (forge, router, observability, health) e as P3 viradas em ticket rastreado. Isso honra a lei nº4: não construir sobre fundação rachada.

---

*Fim do Refinamento — 50 decisões canônicas. Anexo ao Blueprint v1.0.*
