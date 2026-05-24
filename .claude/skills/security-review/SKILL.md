---
name: security-review
description: Review de segurança de código, skills, APIs e infra do OMNIS
version: 1.0.0
tags: [security, review, owasp, omnis]
---

## Security Review OMNIS

**OWASP Agentic Skills Top 10 — verificar:**
1. Prompt injection: inputs de usuário sanitizados antes de ir ao LLM?
2. Deserialização insegura: YAML/JSON arbitrário nunca executado diretamente
3. Permissões excessivas: filesystem e rede com escopo mínimo
4. Supply chain: dependências verificadas (hash/pinning)
5. Secrets exposure: nenhuma credencial em código, logs ou outputs
6. Sandbox escape: capabilities com acesso externo rodam em container isolado
7. Excessive agency: agentes pedem aprovação humana para ações irreversíveis
8. Insecure output handling: outputs de LLM validados antes de executar
9. Dependency confusion: packages internos com namespace próprio
10. Logging de dados sensíveis: PII e tokens nunca em logs plain text

**Antes de publicar qualquer skill:**
- [ ] Scan de secrets no código
- [ ] Verificar permissões no `skill.json` (filesystem: read-only por padrão)
- [ ] Nenhum input externo vai direto para `eval()` ou `exec()`
