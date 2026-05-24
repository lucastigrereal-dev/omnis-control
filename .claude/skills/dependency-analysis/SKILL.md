---
name: dependency-analysis
description: Análise de dependências de packages, capabilities e módulos do OMNIS
version: 1.0.0
tags: [dependencies, analysis, security, omnis]
---

## Dependency Analysis OMNIS

**Ao analisar dependências de um módulo:**
1. Listar dependências diretas do `pyproject.toml` / `package.json`
2. Verificar versões pinadas — preferir versões exatas ou com patch fixo
3. Checar supply chain risk:
   - Maintainer ativo? (último commit < 6 meses)
   - Stars + forks razoáveis para o tamanho do projeto?
   - Licença compatível (MIT, Apache 2.0, BSD preferidos)?
4. Detectar dependências transitivas problemáticas (`pip-audit` ou `npm audit`)
5. Capabilities OMNIS: verificar dependências circulares no Akasha

**Red flags:**
- Pacote com < 100 stars e acesso a filesystem/rede
- Versão não pinada em produção
- Licença GPL em código comercial
- Dependência de fork não-oficial

**Output:** tabela com nome, versão, risco, licença, alternativa recomendada.
