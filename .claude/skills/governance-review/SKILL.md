---
name: governance-review
description: Review de governança de capabilities, agentes e mudanças arquiteturais no OMNIS
version: 1.0.0
tags: [governance, review, security, omnis]
---

## Governance Review OMNIS

Ao revisar qualquer capability, skill, agente ou mudança arquitetural:

**Checklist obrigatório:**
- [ ] Risk level definido: low / medium / high / critical
- [ ] Permissões explícitas (sem wildcard de filesystem ou rede)
- [ ] Sandbox policy aplicada para risk >= medium
- [ ] required_approvals definido (>= 1 para risk medium, >= 2 para high)
- [ ] Changelog atualizado
- [ ] Testes presentes (unit e/ou e2e)
- [ ] Sem credenciais hardcoded
- [ ] OWASP Agentic Skills Top 10 revisado

**Classificação de risco:**
- `low`: leitura de dados internos, geração de texto
- `medium`: escrita em filesystem, chamadas HTTP externas
- `high`: acesso a APIs de terceiros com escrita, publicação de conteúdo
- `critical`: acesso a dados financeiros, sistemas de produção

Documente a decisão em `docs/GOVERNANCE_REVIEW.md`.
