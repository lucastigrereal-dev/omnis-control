# PubliPrice v1.0

**Calculadora local-first de precificacao de collabs no Instagram.**
Feita para Lucas Tigre — 6 perfis, 2,58M seguidores, negociacao direta com hoteis e restaurantes.

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![Stack](https://img.shields.io/badge/stack-Python%203.12%20%2B%20SQLite%20%2B%20Vanilla%20JS-blue)
![Licenca](https://img.shields.io/badge/licen%C3%A7a-privada-red)

---

## O Problema

Voce tem 6 perfis no Instagram, vende pacotes de collab pra hoteis, e toda cotacao e feita no olhometro + Excel. Nao tem como comparar CPM com Meta Ads na hora da call. Nao tem historico de precos. Nao tem consistencia.

**PubliPrice resolve isso.** Em 10 segundos voce calcula um preco profissional com breakdown completo e gera uma proposta pronta pra colar no WhatsApp.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 + Flask |
| Banco de dados | SQLite (arquivo unico local) |
| Frontend | HTML5 + Vanilla JS + CSS3 |
| Testes | pytest |
| CLI opcional | Typer |

**Zero dependencia de nuvem.** O app roda 100% offline no seu computador.

---

## Como Instalar

### Pre-requisitos
- Python 3.12+
- Git (opcional, pra clonar)

### Passo a passo (Windows)

```powershell
# 1. Clone o repositorio (ou baixe o ZIP)
git clone https://github.com/lucastigre/publiprice.git
cd publiprice

# 2. Crie o ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instale as dependencias
pip install -r requirements.txt

# 4. Inicialize o banco de dados (com seed data)
python scripts/init_db.py

# 5. Rode o servidor
python src/publiprice/app.py

# 6. Abra no navegador
# http://localhost:5010
```

### Estrutura do projeto

```
publiprice/
├── src/
│   └── publiprice/
│       ├── app.py              # Servidor Flask
│       ├── calculadora.py      # Formula de precificacao
│       ├── database.py         # Camada de dados SQLite
│       └── exportador.py       # Gerador de propostas
├── frontend/
│   └── index.html              # Single-page app (HTML + CSS + JS inline)
├── data/
│   └── publiprice.db           # Banco SQLite (criado pelo init_db.py)
├── config/
│   └── precificacao.yaml       # Fatores parametrizaveis
├── tests/
│   ├── test_formula_precificacao.py
│   ├── test_database.py
│   ├── test_e2e.py
│   └── test_validacao.py
├── scripts/
│   └── init_db.py              # Inicializa banco com seed data
├── missions/
│   └── MIS-20260518-003/
│       └── 05_outputs/         # Documentacao completa (PRD, specs, etc.)
├── requirements.txt
└── README.md
```

---

## Como Funciona a Formula

O preco final e calculado assim:

```
preco_final = preco_base_pacote
            x fator_seguidores
            x fator_engajamento
            x fator_nicho
            x fator_volume
```

### Exemplo real

**Dados:**
- Perfil: @lucastigrereal (690K, lifestyle, 3.2% engajamento)
- Pacote: Growth (R$ 990,00 base)
- Volume: 1 mes

**Calculo:**
```
R$ 990,00
  x 1.15  (fator seguidores: 690K → faixa 500K-700K)
  x 0.96  (fator engajamento: 3.2% → faixa 2.0%-3.5%)
  x 1.20  (fator nicho: lifestyle → 1.20)
  x 1.00  (fator volume: 1 mes → sem desconto)
  = R$ 1.311,55
```

### Fatores por faixa

| Fator | Faixa | Multiplicador |
|---|---|---|
| **Seguidores** | < 100K | 0.85 |
| | 100K – 300K | 1.00 |
| | 300K – 500K | 1.10 |
| | 500K – 700K | 1.15 |
| | > 700K | 1.25 |
| **Engajamento** | < 2.0% | 0.85 |
| | 2.0% – 3.5% | 0.96 |
| | 3.5% – 5.0% | 1.05 |
| | > 5.0% | 1.20 |
| **Nicho** | Turismo | 1.00 |
| | Gastronomia | 0.90 |
| | Familia | 1.10 |
| | Lifestyle | 1.20 |
| **Volume** | 1 mes | 1.00 |
| | 2-3 meses | 0.85 |
| | 4-6 meses | 0.75 |
| | 7-12 meses | 0.65 |

> **Importante:** Todos os fatores sao parametrizaveis. Edite `config/precificacao.yaml` e reinicie o servidor para ajustar sem tocar no codigo.

---

## Os 6 Perfis (Seed Data)

| Perfil | Seguidores | Nicho | ER |
|---|---|---|---|
| @lucastigrereal | 690K | Lifestyle | 3.2% |
| @oinatalrn | 630K | Turismo | 4.1% |
| @agenteviajabrasil | 452K | Turismo | 3.8% |
| @afamiliatigrereal | 320K | Familia | 5.2% |
| @oquecomernatalrn | 249K | Gastronomia | 4.7% |
| @natalaivoueu | 240K | Turismo | 3.5% |

**Total:** 2.581.000 seguidores (maio/2026).

---

## Os 3 Pacotes

| Pacote | Composicao | Preco Base |
|---|---|---|
| **Starter** | 1 collab, 1 perfil | R$ 350 |
| **Growth** ⭐ | 3 collabs, 3 perfis + SEOgram | R$ 990/mes |
| **Premium** | 4 collabs + 3 stories, 3+ perfis | R$ 1.200 |

> Growth e o recomendado. Melhor custo-beneficio. Liderar venda com ele.

---

## Views do App

| View | Funcionalidade |
|---|---|
| 🧮 **Calculadora** | Input: perfil + pacote + volume → Resultado com breakdown + CPM |
| 📋 **Historico** | Tabela de cotacoes com filtros, busca, KPIs |
| 👥 **Perfis** | Grid de 6 perfis com metricas + tabela de pacotes |

---

## Atalhos de Teclado

| Atalho | Acao |
|---|---|
| `Ctrl + 1` | Calculadora |
| `Ctrl + 2` | Historico |
| `Ctrl + 3` | Perfis |
| `Ctrl + Enter` | Salvar cotacao |
| `Esc` | Fechar modal |

---

## Testes

```bash
# Suite completa
python -m pytest tests/ --import-mode=importlib -p no:warnings -v

# Apenas formula
python -m pytest tests/test_formula_precificacao.py -v

# Com cobertura
python -m pytest tests/ --cov=src/publiprice --cov-report=term-missing
```

Consulte `test_plan.md` para o plano completo de testes (unitarios, integracao, E2E, edge cases, validacao).

---

## Documentacao Completa

Toda a documentacao do projeto esta em `missions/MIS-20260518-003/05_outputs/`:

| Arquivo | Conteudo |
|---|---|
| `PRD.md` | Product Requirements Document — visao completa do produto |
| `user_stories.md` | 18 historias de usuario com criterios de aceitacao |
| `schema_banco.sql` | Schema SQLite completo com seed data |
| `api_contract.md` | Contrato da API REST — todos os endpoints |
| `frontend_spec.md` | Especificacao do frontend — wireframes, componentes, design system |
| `test_plan.md` | Plano de testes — unitarios, integracao, E2E, validacao, edge cases |

---

## Exportacao de Proposta

Ao clicar em "Copiar Proposta", o app gera um texto assim:

```
📊 *Proposta PubliPrice — Lucas Tigre*

🏨 Hotel: Grand Hotel Ponta Negra
📱 Perfil: @lucastigrereal (690K seguidores)
📦 Pacote: Growth
    • 3 collabs
    • 3 paginas
    • SEOgram incluso

💰 Investimento: R$ 1.311,55/mes

📈 Comparativo CPM:
    • PubliPrice: R$ 0,15 por mil impressoes
    • Meta Ads:   R$ 18,00 por mil impressoes
    • 🔽 99% mais barato que anuncios

📩 Proposta valida por 7 dias.
   Duvidas? Manda DM: @lucastigrereal
```

Pronto pra colar no WhatsApp, Direct ou e-mail.

---

## Roadmap (futuro)

| Versao | Features |
|---|---|
| **v1.0** (MVP atual) | Calculadora, historico, 6 perfis, exportacao markdown |
| v1.1 | Graficos de evolucao de cotacoes |
| v1.2 | Importacao CSV de leads |
| v2.0 | Integracao com API do Instagram (metricas em tempo real) |
| v2.5 | Multi-usuario local (150 influenciadores Interior SP) |

---

## Autor

**Lucas Tigre** (@lucastigrereal)
Operador OMNIS. 2,58M seguidores. 6 perfis. Venda de collab para hoteis e restaurantes.

📧 contato@lucastigre.com.br
📱 Instagram: [@lucastigrereal](https://instagram.com/lucastigrereal) | [@agenteviajabrasil](https://instagram.com/agenteviajabrasil)

---

**PubliPrice — "Feito > Perfeito. Mas bem feito."**
