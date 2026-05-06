---
name: generate_seogram_caption
sector: midia_conteudo
version: 1.0
status: active
priority: P1
model_recommended: haiku
approval_required: false
risk: low
inputs:
  - perfil (string): handle Instagram sem @
  - assunto (string): tema do post
  - formato (string): carrossel | reel | foto
outputs:
  - caption: legenda completa SEOgram com hook + CTA + hashtags
  - arquivo: txt salvo em 60_OUTPUTS/instagram/legendas/
created: 2026-04-29
updated: 2026-04-29
---

# Skill: generate_seogram_caption

## Função
Gera legenda otimizada para SEO do Instagram (SEOgram) com hook de alto engajamento, conteúdo estruturado, CTA e hashtags segmentadas por nicho.

## Quando usar
- Ao criar qualquer post no Instagram
- Quando o usuário pedir "legenda", "caption", "texto do post"
- Para garantir máximo alcance orgânico com palavras-chave

## Inputs
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| perfil | string | sim | Handle Instagram |
| assunto | string | sim | Tema do conteúdo |
| formato | string | não | carrossel, reel, ou foto (default: carrossel) |

## Processo passo a passo
1. Identificar nicho do perfil e hashtags correspondentes
2. Escolher template de caption baseado no formato
3. Montar hook + conteúdo + CTA + hashtags
4. Salvar em 60_OUTPUTS/instagram/legendas/

## Output esperado
```
**GUIA COMPLETO**
[conteúdo com word cloud SEO]
[CTA]
Salva pra ver depois
[hashtags segmentadas]
```

## Exemplo
```bash
python run.py lucastigrereal "guia de viagem" carrossel
```

## Modo de execução
automatico (run.py gera caption pronto para publicação)

## next_action
Revisar hook e hashtags antes de publicar.
