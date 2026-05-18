# OMNIS Secret Handler Prompt

```md
Você está no projeto OMNIS CONTROL.

Sua missão: tratar possível segredo em config/connectors.yaml:82 SEM EXIBIR O VALOR.

## Regras Críticas
- **NUNCA** imprima o valor da chave no chat, log, ou terminal
- **NUNCA** copie o valor para nenhum lugar
- **NUNCA** inclua o valor real em nenhum commit

## Localização
Arquivo: `config/connectors.yaml`
Linha: 82
Campo: `notes` do connector `litellm-proxy`
Contém: referência a "Master key"

## Ações Permitidas
1. Ler a estrutura do arquivo (sem imprimir o valor da linha 82)
2. Substituir o valor real por placeholder de env var: `${LITELLM_MASTER_KEY}`
3. Criar `config/connectors.example.yaml` com placeholders seguros
4. Atualizar `.gitignore` se necessário
5. Commitar a correção de segurança

## Ações Proibidas
- Imprimir o segredo
- Copiar o segredo para outro arquivo
- Fazer push (requer autorização humana)
- Deletar arquivos

## Pós-correção
1. Atualizar `omnis_blocked_items.yaml`: marcar `secret_litellm_connectors_yaml` como `resolved`
2. Atualizar `omnis_state.yaml`: remover P0 da lista
3. Recomendar ao operador: rotacionar/revogar a chave exposta
4. Commit message: `fix(security): externalize LiteLLM master key to env var`
```
