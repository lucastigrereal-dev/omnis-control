# Test Plan — PubliPrice v1.0

**Versao:** 1.0 | **Data:** 2026-05-18
**Framework:** pytest 8.x
**Banco de testes:** SQLite em `:memory:` (isolado por teste)
**Cobertura alvo:** > 85% (backend), > 70% (frontend via integracao)

---

## 1. ESTRATEGIA DE TESTES

| Camada | Tipo | Peso | Execucao |
|---|---|---|---|
| **Formula de preco** | Unitario | 30% | Cada commit |
| **SQLite CRUD** | Integracao | 25% | Pre-commit |
| **API endpoints** | Integracao | 20% | Pre-merge |
| **Fluxo E2E** | End-to-End | 15% | Pre-release |
| **Frontend (manual)** | Smoke manual | 10% | MVP pronto |

---

## 2. TESTES UNITARIOS — FORMULA DE PRECIFICACAO

**Arquivo:** `tests/test_formula_precificacao.py`
**Modulo:** `src/publiprice/calculadora.py`

### Classe: `TestFatorSeguidores`

| ID | Cenario | Input | Esperado |
|---|---|---|---|
| UT-FS01 | Perfil pequeno (< 100K) | 50_000 seguidores | `fator = 0.85` |
| UT-FS02 | Perfil medio-baixo (100K–300K) | 249_000 seguidores | `fator = 1.00` |
| UT-FS03 | Perfil medio-alto (300K–500K) | 452_000 seguidores | `fator = 1.10` |
| UT-FS04 | Perfil grande (500K–700K) | 630_000 seguidores | `fator = 1.15` |
| UT-FS05 | Perfil gigante (> 700K) | 750_000 seguidores | `fator = 1.25` |
| UT-FS06 | Limite exato (300K) | 300_000 seguidores | `fator = 1.10` (>= 300K) |
| UT-FS07 | Zero seguidores (edge) | 0 seguidores | `ValueError` — "seguidores deve ser > 0" |
| UT-FS08 | Negativo (edge) | -1 seguidor | `ValueError` — "seguidores deve ser > 0" |

### Classe: `TestFatorEngajamento`

| ID | Cenario | Input | Esperado |
|---|---|---|---|
| UT-FE01 | Engajamento baixo (< 2.0%) | 1.5% | `fator = 0.85` |
| UT-FE02 | Engajamento medio-baixo (2.0%–3.5%) | 3.2% | `fator = 0.96` |
| UT-FE03 | Engajamento medio-alto (3.5%–5.0%) | 4.1% | `fator = 1.05` |
| UT-FE04 | Engajamento alto (> 5.0%) | 5.2% | `fator = 1.20` |
| UT-FE05 | Limite exato (2.0%) | 2.0% | `fator = 0.96` (>= 2.0) |
| UT-FE06 | Engagement negativo (edge) | -0.5% | `ValueError` |
| UT-FE07 | Engagement > 100% (edge) | 150% | `ValueError` |
| UT-FE08 | Engagement zero (edge) | 0% | `fator = 0.85` (faixa < 2.0) |

### Classe: `TestFatorNicho`

| ID | Cenario | Input | Esperado |
|---|---|---|---|
| UT-FN01 | Nicho turismo | "turismo" | `fator = 1.00` |
| UT-FN02 | Nicho gastronomia | "gastronomia" | `fator = 0.90` |
| UT-FN03 | Nicho familia | "familia" | `fator = 1.10` |
| UT-FN04 | Nicho lifestyle | "lifestyle" | `fator = 1.20` |
| UT-FN05 | Nicho invalido | "fitness" | `ValueError` — "nicho desconhecido" |
| UT-FN06 | Nicho vazio | "" | `ValueError` |

### Classe: `TestFatorVolume`

| ID | Cenario | Input | Esperado |
|---|---|---|---|
| UT-FV01 | 1 mes | 1 | `fator = 1.00` |
| UT-FV02 | 2 meses | 2 | `fator = 0.85` |
| UT-FV03 | 3 meses | 3 | `fator = 0.85` |
| UT-FV04 | 4 meses | 4 | `fator = 0.75` |
| UT-FV05 | 6 meses | 6 | `fator = 0.75` |
| UT-FV06 | 7 meses | 7 | `fator = 0.65` |
| UT-FV07 | 12 meses | 12 | `fator = 0.65` |
| UT-FV08 | Zero meses (edge) | 0 | `ValueError` — "volume deve ser >= 1" |
| UT-FV09 | Negativo (edge) | -3 | `ValueError` |

### Classe: `TestPrecoFinal`

| ID | Cenario | Dados | Formula Esperada |
|---|---|---|---|
| UT-PF01 | Growth + @lucastigrereal 1 mes | 690K, 3.2%, lifestyle, 1 | `990.00 * 1.15 * 0.96 * 1.20 * 1.00 = R$ 1.311,55` |
| UT-PF02 | Starter + @oquecomernatalrn 1 mes | 249K, 4.7%, gastronomia, 1 | `350.00 * 1.00 * 1.05 * 0.90 * 1.00 = R$ 330,75` |
| UT-PF03 | Premium + @oinatalrn 6 meses | 630K, 4.1%, turismo, 6 | `1200.00 * 1.15 * 1.05 * 1.00 * 0.75 = R$ 1.086,75` |
| UT-PF04 | Growth + @afamiliatigrereal 3 meses | 320K, 5.2%, familia, 3 | `990.00 * 1.10 * 1.20 * 1.10 * 0.85 = R$ 1.220,92` |
| UT-PF05 | Growth + @natalaivoueu 1 mes | 240K, 3.5%, turismo, 1 | `990.00 * 1.00 * 1.05 * 1.00 * 1.00 = R$ 1.039,50` |

### Classe: `TestCalculoCPM`

| ID | Cenario | Input | Esperado |
|---|---|---|---|
| UT-CPM01 | CPM basico | alcance=185K, preco=R$1.425,60 | `cpm = (1425.60 / 185000) * 1000 = R$ 7,71` |
| UT-CPM02 | CPM muito baixo | alcance=2M, preco=R$350 | `cpm = R$ 0,175` |
| UT-CPM03 | CPM comparativo economia | cpm=0.15, meta=15.00 | `economia = 99.0%` |
| UT-CPM04 | Alcance zero (edge) | alcance=0 | `ValueError` |

---

## 3. TESTES DE INTEGRACAO — SQLITE

**Arquivo:** `tests/test_database.py`
**Fixture:** `db_teste` — SQLite `:memory:` com schema completo + seed data

### Classe: `TestPerfisCRUD`

| ID | Cenario |
|---|---|
| IT-DB01 | `INSERT` perfil valido — retorna `id > 0` |
| IT-DB02 | `SELECT` todos perfis — retorna 6 registros |
| IT-DB03 | `SELECT` por id — retorna perfil correto |
| IT-DB04 | `UPDATE` seguidores — persiste valor novo |
| IT-DB05 | `DELETE` (soft) — `ativo = 0`, mas registro existe |
| IT-DB06 | `INSERT` handle duplicado — `IntegrityError` |
| IT-DB07 | `INSERT` sem campos obrigatorios — `IntegrityError` |
| IT-DB08 | `CHECK` constraint — engagement_rate negativo rejeitado |

### Classe: `TestPacotesPredefinidos`

| ID | Cenario |
|---|---|
| IT-DB09 | 3 pacotes inseridos via seed — `SELECT COUNT(*) = 3` |
| IT-DB10 | Pacote "Growth" tem `recomendado = 1` |
| IT-DB11 | `preco_base` nunca negativo — constraint CHECK |

### Classe: `TestCotacoesRelacionamentos`

| ID | Cenario |
|---|---|
| IT-DB12 | `INSERT` cotacao com FK perfil_id valido — OK |
| IT-DB13 | `INSERT` cotacao com FK perfil_id invalido — `IntegrityError` |
| IT-DB14 | `DELETE` perfil com cotacao vinculada — RESTRICT (bloqueia) |
| IT-DB15 | `SELECT` cotacao com JOIN perfil + pacote + cliente — retorna objeto completo |

### Classe: `TestMetricasHistoricas`

| ID | Cenario |
|---|---|
| IT-DB16 | `INSERT` metrica — OK |
| IT-DB17 | `INSERT` metrica duplicada (mesmo perfil+data) — UNIQUE constraint rejeita |
| IT-DB18 | `DELETE` perfil — metricas historicas em CASCADE (removidas) |

---

## 4. TESTES E2E — FLUXOS COMPLETOS

**Arquivo:** `tests/test_e2e.py`
**Setup:** Flask test client + SQLite `:memory:` com seed data

### Fluxo 1: Calcular → Salvar → Visualizar no Historico

| Passo | Acao | Esperado |
|---|---|---|
| 1 | `POST /api/calculate` com perfil_id=1, pacote_id=2 | 200 + preco_sugerido + breakdown completo |
| 2 | `POST /clientes` com dados do hotel | 201 + cliente_id |
| 3 | `POST /cotacoes` com resultado do calculo + cliente_id | 201 + cotacao_id |
| 4 | `GET /cotacoes?cliente_id=X` | 200 + lista contendo a cotacao recem-criada |
| 5 | `POST /api/export/proposta` com cotacao_id | 200 + texto formatado pronto pra WhatsApp |

### Fluxo 2: Editar perfil → recalcular → reabrir cotacao

| Passo | Acao | Esperado |
|---|---|---|
| 1 | `PUT /perfis/1` atualizando engagement_rate de 3.2% para 5.0% | 200 + dados atualizados |
| 2 | `POST /api/calculate` com perfil_id=1 atualizado | Preco MAIOR que antes (fator engajamento subiu) |
| 3 | `PATCH /cotacoes/1` com novo preco + status "enviada" | 200 + versao incrementada |

### Fluxo 3: Fechar cotacao → KPIs atualizam

| Passo | Acao | Esperado |
|---|---|---|
| 1 | Criar 3 cotacoes (2 "gerada", 1 "fechada") | — |
| 2 | `GET /api/dashboard` | `total_cotacoes=3, fechadas=1, taxa_fechamento=33.3` |
| 3 | `PATCH /cotacoes/2` status="fechada" | 200 |
| 4 | `GET /api/dashboard` | `fechadas=2, taxa_fechamento=66.7` |

---

## 5. TESTES DE VALIDACAO

**Arquivo:** `tests/test_validacao.py`

### Classe: `TestValidacaoCampos`

| ID | Cenario | Input | Esperado |
|---|---|---|---|
| VA01 | handle sem @ | "perfil" | 400 — "handle deve comecar com @" |
| VA02 | handle vazio | "" | 400 — "handle obrigatorio" |
| VA03 | seguidores zero | 0 | 400 — "seguidores deve ser > 0" |
| VA04 | engagement_rate > 100 | 150.0 | 400 — "engagement_rate deve estar entre 0 e 100" |
| VA05 | preco_final negativo | -50.00 | 400 — "preco_final deve ser > 0" |
| VA06 | perfil_id inexistente no calculate | 999 | 400 — "perfil nao encontrado" |
| VA07 | pacote_id inexistente no calculate | 999 | 400 — "pacote nao encontrado" |
| VA08 | volume_meses = 0 | 0 | 400 — "volume_meses deve ser >= 1" |
| VA09 | desconto maior que preco | preco=350, desconto=500 | 400 — "desconto nao pode exceder o preco calculado" |
| VA10 | uf com mais de 2 caracteres | "RNN" | 400 — "UF deve ter exatamente 2 caracteres" |

---

## 6. EDGE CASES (CASOS LIMITE)

**Arquivo:** `tests/test_edge_cases.py`

| ID | Cenario | Esperado |
|---|---|---|
| EC01 | Perfil com 100.000 EXATOS | Cai na faixa 100K–300K, fator 1.00 |
| EC02 | Perfil com 300.000 EXATOS | Cai na faixa 300K–500K, fator 1.10 |
| EC03 | Engagement 2.0% EXATO | Cai na faixa 2.0%–3.5%, fator 0.96 |
| EC04 | Engagement 5.0% EXATO | Cai na faixa 3.5%–5.0%, fator 1.05 |
| EC05 | Desconto 100% | `preco_final = 0` — deve ser rejeitado (CHECK > 0) |
| EC06 | Sem cliente (cliente_id = NULL) | Cotacao salva normalmente, JOIN retorna NULL |
| EC07 | Busca com string vazia | Retorna todas (sem filtro de busca) |
| EC08 | Pagina sem resultados (offset > total) | Retorna `[]` com total correto |
| EC09 | Numero MUITO grande (overflow) | 2^53 seguidores — sem perda de precisao (SQLite REAL = double) |

---

## 7. SMOKE TESTS MANUAIS (FRONTEND)

Checklist pre-release:

- [ ] Abrir `index.html` — carrega sem erros no console
- [ ] 3 tabs visiveis e funcionais
- [ ] Dropdown de perfil mostra 6 opcoes com seguidores formatados
- [ ] Dropdown de pacote mostra 3 opcoes com precos
- [ ] Alterar perfil → resultado atualiza em < 100ms
- [ ] Slider de volume → resultado recalcula
- [ ] Aplicar desconto → preco final riscado + novo valor
- [ ] Clicar "Copiar Proposta" → modal aparece → texto copia pro clipboard
- [ ] Preencher dados do cliente → "Salvar Cotacao" → toast verde
- [ ] Ir pra Historico → nova cotacao aparece no topo
- [ ] Mudar status inline → cor do badge muda
- [ ] KPIs atualizam apos mudanca de status
- [ ] Busca filtra em tempo real
- [ ] Tela Perfis mostra 6 cards
- [ ] Editar perfil → abre modal → salvar → card atualiza
- [ ] Atalhos Ctrl+1/2/3 funcionam
- [ ] Dark theme consistente em todas as views
- [ ] Responsivo: colapsa em mobile < 768px

---

## 8. COMANDOS DE EXECUCAO

```bash
# Todos os testes unitarios
python -m pytest tests/test_formula_precificacao.py -v

# Testes de integracao (SQLite)
python -m pytest tests/test_database.py -v

# Testes E2E (API)
python -m pytest tests/test_e2e.py -v

# Validacao
python -m pytest tests/test_validacao.py -v

# Edge cases
python -m pytest tests/test_edge_cases.py -v

# Suite completa
python -m pytest tests/ --import-mode=importlib -p no:warnings -v

# Com coverage
python -m pytest tests/ --cov=src/publiprice --cov-report=term-missing -v
```

---

## 9. CI/CD (FUTURO — GitHub Actions local)

```yaml
# .github/workflows/test.yml (placeholder)
# Roda no push pra main: full suite
# Roda no PR: targeted tests do modulo alterado
```
