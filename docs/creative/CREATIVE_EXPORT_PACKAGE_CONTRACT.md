# Creative Export Package Contract

## Localização

```
data/exports/creative_packages/<package_id>/
```

Onde `<package_id>` = `brief_<brief_id>` + timestamp.

## Artefatos

### Obrigatórios (10 arquivos textuais)

| # | Arquivo | Formato | Conteúdo | Fonte |
|---|---------|---------|----------|-------|
| 1 | `brief.md` | Markdown | Briefing criativo completo | CreativeBrief |
| 2 | `caption.txt` | Texto | Legenda final aprovada | brief.script |
| 3 | `hashtags.txt` | Texto | Lista de hashtags | — |
| 4 | `script.md` | Markdown | Roteiro (vídeo/carrossel) | brief.script |
| 5 | `shot_list.md` | Markdown | Lista de cenas/imagens | brief.shot_list |
| 6 | `design_notes.md` | Markdown | Notas de design | brief.design_notes |
| 7 | `editing_notes.md` | Markdown | Instruções de edição | brief.editing_notes |
| 8 | `asset_requirements.json` | JSON | Requisitos técnicos | brief.asset_requirements |
| 9 | `tool_suggestions.md` | Markdown | Ferramentas sugeridas | brief.tool_suggestions |
| 10 | `production_checklist.md` | Markdown | Checklist pré-publicação | Template |

### Novos — Preview Visual

| # | Arquivo | Formato | Conteúdo | Geração |
|---|---------|---------|----------|---------|
| 11 | `preview.html` | HTML | Preview visual do post no feed | Template HTML inline |
| 12 | `mock_image.png` | PNG | Placeholder 1080x1080 | Pillow (gradiente + texto) |

### Condicional

| # | Arquivo | Formato | Quando |
|---|---------|---------|--------|
| 13 | `WARNINGS.md` | Markdown | Apenas se houver campos ausentes no brief |

## Regras

1. **NUNCA** chamar APIs externas para gerar artefatos
2. **NUNCA** publicar packages automaticamente
3. Preview HTML deve ser auto-contido (CSS inline, sem CDN)
4. Mock image usa APENAS Pillow — sem DALL-E, Imagen, etc.
5. Se campo de dados estiver vazio, gerar placeholder honesto com aviso
6. Diretório `data/exports/creative_packages/` é gitignored
7. WARNINGS.md é obrigatório quando placeholders são usados

## Exemplo de Estrutura

```
data/exports/creative_packages/
└── brief_q-001_20260506_173000/
    ├── brief.md
    ├── caption.txt
    ├── hashtags.txt
    ├── script.md
    ├── shot_list.md
    ├── design_notes.md
    ├── editing_notes.md
    ├── asset_requirements.json
    ├── tool_suggestions.md
    ├── production_checklist.md
    ├── preview.html
    ├── mock_image.png
    └── WARNINGS.md
```

## Testes de Conformidade

- Package deve conter no mínimo 10 arquivos
- preview.html deve ser HTML válido sem referências externas
- mock_image.png deve ser 1080x1080 PNG válido
- WARNINGS.md só aparece quando há avisos
