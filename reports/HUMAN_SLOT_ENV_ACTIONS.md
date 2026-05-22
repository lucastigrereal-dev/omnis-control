# Human Slot — ENV Actions

**Date:** 2026-05-22
**Mode:** READ-ONLY — No env changes executed

---

## ANTHROPIC_API_KEY — CRITICAL

**Problema:** A chave está disponível apenas no contexto interno do Claude Code. KRATOS, Publisher OS e OMNIS Runtime não conseguem acessar `ANTHROPIC_API_KEY` porque ela não existe no environment do sistema.

### Onde setar

**Opção A — Windows User Environment (recomendado)**
```
System Properties → Environment Variables → User variables → New
  Variable: ANTHROPIC_API_KEY
  Value:   <cole a chave aqui>
```

**Opção B — PowerShell (sessão atual)**
```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', '<chave>', 'User')
```

**Opção C — .env do OMNIS Control** (não recomendado — security risk)

### Como validar sem imprimir segredo

```powershell
# PowerShell — verifica se existe sem mostrar valor
if ($env:ANTHROPIC_API_KEY) { Write-Host "SET (length: $($env:ANTHROPIC_API_KEY.Length))" } else { Write-Host "UNSET" }

# Para KRATOS — verificar se o Python consegue ler
python -c "import os; print('SET' if os.environ.get('ANTHROPIC_API_KEY') else 'UNSET')"
```

### Impacto

| Sistema | Sem a chave | Com a chave |
|---------|------------|-------------|
| KRATOS | Falha em chamadas Anthropic | RuntimeAgent funcional |
| Publisher OS | Sem acesso ao Claude | CrewAI pode usar Claude |
| OMNIS ProviderInterface | Fallback para Ollama local | Tier routing completo |

---

## Outras variáveis pendentes (B0 Preflight)

| Variável | Status | Onde setar |
|----------|--------|------------|
| META_APP_ID | UNSET | OAuth Instagram bloqueado |
| META_APP_SECRET | UNSET | OAuth Instagram bloqueado |
| NOTION_TOKEN | UNSET | Integração Notion |
| LITELLM_MASTER_KEY | Set no .env | Publisher OS — OK |

---

## Próximo passo
1. Operador seta `ANTHROPIC_API_KEY` manualmente
2. Validar com comando seguro acima
3. Rodar `python -m pytest tests/` para confirmar que nada quebrou
