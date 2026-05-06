---
name: export_content_batch_to_csv
sector: midia_conteudo
version: 1.0
status: active
priority: P1
model_recommended: haiku
approval_required: false
risk: low
inputs:
  - perfil (string): handle Instagram sem @
  - dias (int): quantidade de dias para exportar
  - formato (string): publer | metricool | content
outputs:
  - csv_file: CSV formatado para importação na ferramenta de agendamento
  - arquivo: CSV salvo em 60_OUTPUTS/instagram/csv_batches/
created: 2026-04-29
updated: 2026-04-29
---

# Skill: export_content_batch_to_csv

## Função
Exporta lote de conteúdo para CSV nos formatos Publer, Metricool ou content (genérico). Pronto para upload direto na ferramenta de agendamento.

## Quando usar
- Quando o usuário pedir "exportar", "CSV", "planilha de posts"
- Para subir lote de conteúdo no Publer ou Metricool
- Para ter backup planilhado do calendário editorial

## Inputs
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| perfil | string | sim | Handle Instagram |
| dias | int | não | Dias para exportar (default: 7) |
| formato | string | não | publer/metricool/content (default: publer) |

## Processo passo a passo
1. Identificar formato de exportação
2. Gerar dados fictícios para demonstração
3. Montar CSV com headers corretos do formato
4. Salvar em 60_OUTPUTS/instagram/csv_batches/

## Output esperado
CSV com cabeçalho compatível com a ferramenta escolhida

## Exemplo
```bash
python run.py oinatalrn 7 publer
```

## Modo de execução
automatico (CSV pronto para download e upload na ferramenta)

## next_action
Fazer upload do CSV no Publer/Metricool ou conectar ARGOS para publicação direta.
