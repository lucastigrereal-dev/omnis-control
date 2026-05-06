---
name: create_sales_dm_sequence
sector: comercial_sdr
version: 1.0
status: active
priority: P1
model_recommended: haiku
approval_required: false
risk: low
inputs:
  - empresa (string): nome do hotel/restaurante
  - contato (string): cargo da pessoa (ex: Gerente, Marketing)
  - pacote (string): starter | growth | premium
outputs:
  - sequencia_json: 5 DMs com timing, tipo e script
  - arquivo: JSON salvo em 60_OUTPUTS/instagram/scripts_dm/
created: 2026-04-29
updated: 2026-04-29
---

# Skill: create_sales_dm_sequence

## Função
Gera sequência de 5 DMs comerciais para prospecção de hotéis/restaurantes no Instagram: abertura → follow-up rápido → follow-up frio → qualificação → objeção de preço.

## Quando usar
- Quando o usuário pedir "DM", "sequência de vendas", "prospecção"
- Para iniciar contato comercial com hotel/restaurante via Instagram
- Quando precisar de script de venda padronizado

## Inputs
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| empresa | string | sim | Nome do hotel/restaurante |
| contato | string | não | Cargo (default: Gerente) |
| pacote | string | não | starter/growth/premium (default: growth) |

## Processo passo a passo
1. Identificar pacote e valor
2. Personalizar scripts com nome da empresa
3. Montar sequência de 5 DMs com timing
4. Salvar JSON em 60_OUTPUTS/instagram/scripts_dm/

## Output esperado
5 mensagens: abertura → follow-up 2h → follow-up 24h → qualificação → objeção de preço

## Exemplo
```bash
python run.py "Hotel Oceano" "Gerente" growth
```

## Modo de execução
semi_automatico (run.py gera script, humano copia e envia no Instagram)

## next_action
Copiar primeira DM e enviar para o contato no Instagram.
