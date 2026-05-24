---
name: artifact-analysis
description: Análise de artefatos de build, outputs de agentes e pacotes de entrega do OMNIS
version: 1.0.0
tags: [artifacts, analysis, quality, omnis]
---

## Artifact Analysis OMNIS

**Tipos de artefatos no OMNIS:** outputs de skills (JSON, Markdown, imagens, CSVs),
pacotes de campanha, builds de frontend, schemas e migrations, reports de sprint/wave.

**Ao analisar um artefato:**
1. Origem: qual skill/agente gerou? Qual versão?
2. Integridade: hash bate com o registrado no Akasha?
3. Schema compliance: output segue o schema declarado na capability?
4. Completude: todos os campos obrigatórios presentes?
5. Qualidade: conteúdo (tom, clareza, CTA, hashtags); código (lint passou?)

**Go/No-go:** artefato só promovido para produção após validação de schema +
aprovação humana para risk >= medium.
