# Creative Production OS

## O que é

O Creative Production OS é o setor de **produção criativa** do OMNIS. Ele transforma itens da fila de conteúdo em briefs criativos, gerencia a produção de assets, coordena revisões e gera pacotes de exportação prontos para publicação.

## Onde entra no OMNIS

```
Camada 5 — Produção & Publishing
├── Content Queue (fila de ideias)
├── Caption Approval (aprovação de legendas)
├── Creative Production OS ← você está aqui
├── Argos Bridge (ponte de publicação — futuro)
└── Publisher OS (publicação real — futuro)
```

## Relação com outros módulos

| Módulo | Relação |
|--------|---------|
| **Content Queue** | Fornece `queue_id` e `account_handle` para o brief |
| **Caption Approval** | Fornece `caption_draft_id` e validação de legenda aprovada |
| **Argos Bridge** | Consome export packages para preparar publicação (futuro) |
| **Publisher OS** | Publicação real no Instagram (futuro) |

## O que faz AGORA

- Cria briefs criativos com validação de fila e caption
- Gerencia fila de produção (itens, assets, status)
- Sistema de revisão e aprovação (approve/reject/changes_requested)
- Geração de export packages com 13 artefatos:
  - 10 arquivos textuais (.md, .txt, .json)
  - preview.html (visualização HTML do post)
  - mock_image.png (placeholder 1080x1080 via Pillow)
  - WARNINGS.md (avisos de campos ausentes)
- 18 testes automatizados (mais 8 novos de export)

## O que ainda NÃO faz

- ❌ Publicar no Instagram (depende de OAuth Meta)
- ❌ Conectar com APIs externas (DALL-E, Imagen, etc.)
- ❌ Gerar legendas automaticamente (vem do Caption Approval)
- ❌ Agendar posts (futuro, via Argos/Publisher OS)
- ❌ Dashboard web (futuro)

## Regras de Segurança

1. Export packages NUNCA são publicados automaticamente
2. Imagens mock são geradas localmente via Pillow — sem APIs externas
3. Preview HTML é auto-contido (sem CDN, sem trackers)
4. WARNINGS.md é obrigatório quando dados estão ausentes
5. Diretório de exports é gitignored

## Comandos CLI

```bash
python omnis.py creative status                      # Status do módulo
python omnis.py creative briefs list [--limit N]     # Listar briefs
python omnis.py creative briefs show <brief_id>      # Detalhes do brief
python omnis.py creative export-package --brief-id X # Gerar export package
```
