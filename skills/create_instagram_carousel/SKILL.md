---
name: create_instagram_carousel
sector: midia_conteudo
version: 1.0
status: active
priority: P1
model_recommended: haiku
approval_required: false
risk: low
inputs:
  - perfil (string): handle Instagram sem @
  - tema (string): assunto do carrossel
  - qtd_slides (int): número de slides (mín 3, máx 10)
outputs:
  - carrossel_json: estrutura slide-a-slide com texto por slide
  - arquivo: JSON salvo em 60_OUTPUTS/instagram/carrosseis/
created: 2026-04-29
updated: 2026-04-29
---

# Skill: create_instagram_carousel

## Função
Gera estrutura completa de carrossel Instagram: capa, slides de conteúdo, prova social, dica prática e CTA.

## Quando usar
- Quando o usuário pedir "carrossel", "post de várias fotos"
- Para conteúdo educativo ou lista (rankings, guias, dicas)
- Sempre que o formato carrossel for o recomendado no calendário

## Inputs
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| perfil | string | sim | Handle Instagram |
| tema | string | sim | Assunto do carrossel |
| qtd_slides | int | não | Número de slides (default: 5, para 6 total) |

## Processo passo a passo
1. Identificar tema e quantidade de slides
2. Gerar slide 1 (capa com hook)
3. Gerar slides de conteúdo (N-2 slides)
4. Gerar slide de dica prática
5. Gerar slide final de CTA
6. Salvar JSON em 60_OUTPUTS/instagram/carrosseis/

## Output esperado
6 slides: capa → conteúdo (3-4) → dica → CTA

## Exemplo
```bash
python run.py afamiliatigrereal "5 praias do RN" 4
```

## Modo de execução
semi_automatico (run.py gera estrutura, humano revisa e cria design)

## next_action
Usar estrutura para criar design no Canva ou enviar para designer.
