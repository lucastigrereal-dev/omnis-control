# OMNIS SUPREME 210 WAVES — Skill Routing

**Date:** 2026-05-15

---

## Skills core (sempre ativas)

| Skill | Funcao | Quando ativa |
|---|---|---|
| jarvis-router | Classificar intencao, setor, risco | Todo bloco |
| jarvis-brain | Carregar contexto multi-fonte | Todo bloco |
| jarvis-delegate | Escolher skill especializada | Todo bloco |
| jarvis-guardrails | Bloquear acoes perigosas | Todo bloco |
| jarvis-decide | Decidir PASS/BLOCKED/FAIL | Todo bloco |
| jarvis-memory-write | Persistir aprendizado | Fim de wave |
| verification-before-completion | Gate final | Fim de wave |

## Skills por grupo

### Grupo 01 — Foundation (W001-W010)
| Wave | Skills esperadas |
|---|---|
| W001 | jarvis-router, jarvis-brain, gsd:verify-work, security-review |
| W002 | sc:git, sc:analyze, review |
| W003 | sc:test, gsd:verify-work, review |
| W004 | writing-plans, sc:git, security-review |
| W005 | gsd:new-project, writing-plans, sc:document |
| W006 | security-review, jarvis-guardrails, sc:document |
| W007 | sc:implement, test-driven-development |
| W008 | gsd:progress, sc:document, jarvis-memory-write |
| W009 | writing-plans, sc:document, humanizer |
| W010 | gsd:validate-phase, security-review, verification-before-completion |

### Grupo 02 — Mission OS (W011-W020)
| Wave | Skills esperadas |
|---|---|
| W011 | sc:implement, test-driven-development, writing-plans |
| W012 | feature-dev:feature-dev, sc:implement, sc:test |
| W013 | sc:implement, systematic-debugging |
| W014 | sc:implement, sc:test |
| W015 | sc:document, jarvis-memory-write, humanizer |
| W016 | sc:implement, test-driven-development |
| W017 | sc:implement, security-review |
| W018 | sc:implement, jarvis-memory-write |
| W019 | sc:implement, systematic-debugging |
| W020 | gsd:validate-phase, sc:test, verification-before-completion |

### Grupo 03 — Memory/Akasha (W021-W030)
| Wave | Skills esperadas |
|---|---|
| W021 | writing-plans, sc:implement, db-readonly-audit |
| W022 | sc:implement, sc:test, review |
| W023 | security-review, sc:implement |
| W024 | sc:implement, sc:test |
| W025 | sc:implement, security-review |
| W026 | sc:implement, sc:test |
| W027 | sc:research, writing-plans, sc:implement |
| W028 | sc:implement, jarvis-brain |
| W029 | sc:implement, jarvis-memory-write |
| W030 | gsd:validate-phase, sc:test, verification-before-completion |

### Grupo 04 — Observability (W031-W040)
| Wave | Skills esperadas |
|---|---|
| W031 | sc:implement, sc:test |
| W032 | sc:implement, test-driven-development |
| W033 | sc:implement, sc:test |
| W034 | writing-plans, sc:document |
| W035 | sc:implement, sc:test |
| W036 | writing-plans, sc:document |
| W037 | sc:implement, sc:test |
| W038 | sc:implement, sc:test |
| W039 | sc:implement, sc:test |
| W040 | gsd:validate-phase, verification-before-completion |

### Grupo 05 — Skill Execution Runtime (W041-W050)
| Wave | Skills esperadas |
|---|---|
| W041 | sc:analyze, review, sc:document |
| W042 | sc:implement, test-driven-development |
| W043 | sc:implement, security-review |
| W044 | sc:implement, sc:test |
| W045 | sc:implement, test-driven-development |
| W046 | sc:implement, sc:test |
| W047 | sc:implement, sc:test |
| W048 | sc:implement, security-review |
| W049 | sc:implement, sc:test |
| W050 | gsd:validate-phase, verification-before-completion |

### Grupo 06 — Capability Forge (W051-W060)
| Wave | Skills esperadas |
|---|---|
| W051 | sc:analyze, sc:implement, review |
| W052 | writing-plans, sc:document, sc:implement |
| W053 | sc:implement, feature-dev:feature-dev |
| W054 | sc:implement, test-driven-development |
| W055 | sc:implement, sc:test |
| W056 | sc:implement, security-review |
| W057 | sc:implement, sc:test |
| W058 | sc:implement, security-review |
| W059 | sc:implement, sc:test |
| W060 | gsd:validate-phase, verification-before-completion |

### Grupo 07 — Squad Composer (W061-W070)
Skills: sc:implement, test-driven-development, role_registry usage, security-review

### Grupo 08 — Execution Graph (W071-W080)
Skills: sc:implement, test-driven-development, systematic-debugging, security-review

### Grupo 09 — Publisher/ARGOS (W081-W090)
Skills: sc:implement, security-review, publisher_argos usage, creative_production usage

### Grupo 10 — Content Factory (W091-W100)
Skills: sc:implement, test-driven-development, humanizer, brand, ui-ux-pro-max

### Grupo 11 — Video Studio (W101-W110)
Skills: sc:implement, sc:test, video_assets usage, security-review

### Grupo 12 — Sales/CRM (W111-W120)
Skills: sc:implement, sc:test, sales_crm usage, security-review

### Grupo 13 — Commercial/SDR (W121-W130)
Skills: sc:implement, sc:test, commercial_sdr usage, writing-plans

### Grupo 14 — App Factory (W131-W140)
Skills: feature-dev:feature-dev, sc:implement, writing-plans, sc:test

### Grupo 15 — Automation/n8n (W141-W150)
Skills: sc:implement, security-review, sc:test

### Grupo 16 — MCP/Plugin Runtime (W151-W160)
Skills: sc:implement, plugin-dev:mcp-integration, plugin-dev:skill-development, security-review

### Grupo 17 — Remote Control (W161-W170)
Skills: sc:implement, security-review, sc:test

### Grupo 18 — KRATOS Bridge (W171-W180)
Skills: sc:implement, writing-plans, sc:test

### Grupo 19 — Production Hardening (W181-W190)
Skills: sc:implement, systematic-debugging, security-review, sc:test

### Grupo 20 — First Real Missions (W191-W200)
Skills: gsd:execute-phase, gsd:validate-phase, security-review, jarvis-memory-write

### Grupo 21 — Supreme RC (W201-W210)
Skills: gsd:complete-milestone, security-review, verification-before-completion, jarvis-memory-write

---

## Regra de selecao

1. Se bloco cria modelos → `test-driven-development` + `sc:implement`
2. Se bloco mexe em seguranca → `security-review`
3. Se bloco e documentacao → `sc:document` + `humanizer`
4. Se bloco falha → `systematic-debugging`
5. Se bloco e final de wave → `verification-before-completion`
6. Se bloco e final de grupo → `gsd:validate-phase`
7. Se wave e apenas docs → pular `sc:implement`, usar `sc:document`
