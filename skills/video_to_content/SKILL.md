---
name: video_to_content
sector: midia_conteudo
version: 1.0
status: active
priority: P1
model_recommended: haiku
approval_required: false
risk: low
inputs:
  - titulo_video (string): título do vídeo original
  - topicos (list): principais pontos abordados no vídeo
outputs:
  - carrossel_json: estrutura de carrossel + hooks + slides
  - arquivo: JSON salvo em 60_OUTPUTS/instagram/content_batches/
created: 2026-04-29
updated: 2026-04-29
---

# Skill: video_to_content

## Função
Transforma vídeos (YouTube, TikTok, reels) em conteúdo Instagram reaproveitável: estrutura de carrossel, hooks de legenda, e slides prontos.

## Quando usar
- Quando o usuário tiver um vídeo e quiser reaproveitar como post
- Quando pedir "repurpose", "reaproveitar", "transformar vídeo"
- Para extrair máximo valor de cada vídeo produzido

## Inputs
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| titulo_video | string | sim | Título do vídeo original |
| topicos | list | não | Lista de tópicos do vídeo |

## Processo passo a passo
1. Receber título e tópicos do vídeo
2. Gerar 3 hooks alternativos para legenda
3. Montar slides: capa → conteúdo (1 por tópico) → CTA
4. Salvar JSON em 60_OUTPUTS/instagram/content_batches/

## Output esperado
Carrossel com N+1 slides (capa + N tópicos + CTA) + 3 hooks sugeridos

## Exemplo
```bash
python run.py "5 dicas para viajar" "Planeje com antecedência" "Escolha destinos fora de temporada" "Use milhas"
```

## Modo de execução
semi_automatico (run.py gera estrutura, humano ajusta tom e revisa)

## next_action
Revisar slides gerados e programar publicação no calendário.
