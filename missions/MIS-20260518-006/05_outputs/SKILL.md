---
name: pricing-calculator
version: 1.0.0
tier: core
sector: finance
description: Calculadora inteligente de preco de publi para Instagram baseada em alcance, nicho, formato e pacote
triggers:
  - calcular preco
  - precificar publi
  - quanto cobrar
  - cotacao publi
  - precificacao
  - proposta comercial
  - comparar pacotes
dependencies: []
author: OMNIS Forge
created: 2026-05-18
---

# pricing-calculator

## Visao Geral

A `pricing-calculator` e a skill core do setor financeiro responsavel por calcular o preco justo de publicacoes (publi) no Instagram. Ela implementa o algoritmo de precificacao da OMNIS baseado em metricas reais de audiencia (seguidores, alcance medio, taxa de engajamento), ajustado por multiplicadores de nicho, formato e desconto de pacote.

A skill tambem gera uma comparacao de CPM (OMNIS vs Meta Ads) que serve como argumento comercial principal: o anunciante paga **ate 98% menos** por impressao em relacao ao trafego pago tradicional.

## Exemplos de Uso

### Exemplo 1: Perfil pequeno, nicho turismo, pacote Starter
```
Entrada:
  - seguidores: 50.000
  - alcance_medio: 15.000
  - engagement_rate: 4.2%
  - nicho: turismo
  - formato: collab
  - pacote: starter

Saida esperada:
  - preco_unitario: ~R$ 350,00
  - cpm_omnis: ~R$ 23,33
  - economia_vs_meta: ~98%
```

### Exemplo 2: Perfil medio, nicho gastronomia, pacote Growth
```
Entrada:
  - seguidores: 200.000
  - alcance_medio: 60.000
  - engagement_rate: 3.5%
  - nicho: gastronomia
  - formato: carrossel (3 collabs)
  - pacote: growth

Saida esperada:
  - preco_por_collab: ~R$ 297,00
  - preco_total: ~R$ 891,00
  - economia total vs Meta Ads: ~R$ 1.200+
```

### Exemplo 3: @agenteviajabrasil, pacote Premium
```
Entrada:
  - seguidores: 452.000
  - alcance_medio: 180.000
  - engagement_rate: 5.1%
  - nicho: turismo
  - formato: reel (4 collabs)
  - pacote: premium

Saida esperada:
  - preco_por_collab: ~R$ 612,00
  - preco_total: ~R$ 2.448,00
  - economia vs Meta Ads: ~98%
```

## Parametros de Entrada

| Parametro | Tipo | Obrigatorio | Descricao |
|---|---|---|---|
| `seguidores` | int | Sim | Numero total de seguidores do perfil |
| `alcance_medio` | int | Sim | Alcance medio por post (impressoes) |
| `engagement_rate` | float | Sim | Taxa de engajamento em % (ex: 4.2) |
| `nicho` | str | Sim | Nicho do perfil: `turismo`, `gastronomia`, `familia` |
| `formato` | str | Sim | Formato do conteudo: `reel`, `carrossel`, `collab`, `story` |
| `pacote` | str | Sim | Pacote de venda: `starter`, `growth`, `premium` |
| `num_collabs` | int | Nao | Numero de collabs no pacote (padrao: 1 para starter, 3 para growth, 4 para premium) |
| `meta_cpm` | float | Nao | CPM de referencia Meta Ads (padrao: 15.0 = R$ 15,00) |

## Formato de Saida

A skill retorna um dicionario (`dict`) com a seguinte estrutura:

```json
{
  "input": {
    "seguidores": 452000,
    "alcance_medio": 180000,
    "engagement_rate": 5.1,
    "nicho": "turismo",
    "formato": "reel",
    "pacote": "premium",
    "num_collabs": 4
  },
  "pricing": {
    "preco_base": 750.00,
    "multiplicador_nicho": 1.0,
    "multiplicador_formato": 1.2,
    "multiplicador_pacote": 0.75,
    "preco_unitario": 675.00,
    "preco_total": 2700.00,
    "preco_por_collab": 675.00
  },
  "cpm_comparison": {
    "cpm_omnis": 3.75,
    "cpm_meta": 15.00,
    "economia_pct": 75.0,
    "alcance_total_estimado": 720000
  },
  "proposta": "PROPOSTA COMERCIAL - @agenteviajabrasil\n..."
}
```

## Regras de Negocio (Algoritmo de Precificacao)

### 1. Calculo do Preco Base
```
preco_base = alcance_medio / 1000 * engagement_multiplier
engagement_multiplier = clamp((engagement_rate / 3.0), 0.8, 1.5)
```
O engagement_rate de referencia e 3.0%. Acima disso, o preco sobe proporcionalmente ate o teto de 1.5x. Abaixo, desce ate o piso de 0.8x.

### 2. Multiplicador de Nicho
| Nicho | Multiplicador |
|---|---|
| `turismo` | 1.00 |
| `gastronomia` | 0.90 |
| `familia` | 0.85 |

O nicho turismo tem o maior ticket medio de anunciantes (hoteis, resorts), justificando o multiplicador base. Gastronomia e familia possuem anunciantes com ticket medio menor.

### 3. Multiplicador de Formato
| Formato | Multiplicador |
|---|---|
| `reel` | 1.20 |
| `carrossel` | 1.15 |
| `collab` | 1.00 |
| `story` | 0.70 |

Reels tem maior retencao e alcance organico. Carrosseis geram mais saves e compartilhamentos. Collab e o formato padrao. Stories sao efemeros (24h).

### 4. Desconto de Pacote
| Pacote | Desconto | Collabs |
|---|---|---|
| `starter` | 1.00 (sem desconto) | 1 |
| `growth` | 0.85 por collab | 3 |
| `premium` | 0.75 por collab | 4 |

O desconto e aplicado ao preco unitario de cada collab dentro do pacote. O preco total = preco_unitario * num_collabs.

### 5. Calculo do CPM
```
cpm_omnis = (preco_unitario / alcance_medio) * 1000
meta_cpm = 15.0 (padrao R$ 15,00 CPM Meta Ads)
economia_pct = (1 - cpm_omnis / meta_cpm) * 100
```

O argumento de venda principal e a economia de 75-98% em relacao ao CPM de Meta Ads.

### 6. Preco Minimo
Nenhum preco unitario pode ser inferior a R$ 150,00 (piso operacional).

### 7. Arredondamento
Todos os precos sao arredondados para o inteiro mais proximo (R$ XXX,00).

## Pontos de Integracao

| Ponto | Descricao |
|---|---|
| `src/finance/service.py` | FinancePlanner usa o pricing-calculator para registrar revenue forecasts |
| `src/sales/proposal_generator.py` | Gerador de propostas comerciais consome `format_proposal()` |
| `jarvis-decide` | Decision Engine avalia preco vs budget do anunciante |
| `jarvis-memory-write` | Persiste calculos de proposta no Akasha como historico comercial |
| `Publisher OS / ARGOS` | Propostas aprovadas podem ser enviadas diretamente ao ARGOS |

## Notas

- **Zero LLM**: todos os calculos sao deterministicos, sem chamadas a modelos de linguagem.
- **Zero rede**: nenhuma chamada a APIs externas.
- **Zero banco**: opera inteiramente em memoria.
- **dry_run por padrao**: a skill apenas calcula e retorna, nunca executa acoes laterais.
- Os valores de referencia (engagement_rate base de 3.0%, Meta CPM de R$ 15,00) podem ser ajustados via parametros opcionais.
