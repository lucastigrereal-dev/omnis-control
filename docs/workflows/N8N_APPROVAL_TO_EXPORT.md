# n8n Workflow: Approval → Export Pipeline

## Objetivo

Pipeline de aprovação e exportação de conteúdo do OMNIS. Recebe um draft aprovado, valida os campos obrigatórios, monta pacote de exportação e notifica o operador.

## Fluxo

```
Manual Trigger → Validate Payload → Build Export Package → Notify Operator
```

### 1. Manual Trigger
Inicia o workflow manualmente. O operador cola o JSON do draft aprovado.

### 2. Validate Payload (Code Node — Python)
Valida que o payload contém:
- `draft_id` (string)
- `caption` (string)
- `perfil` (string) — handle Instagram
- `asset_url` (string) — URL do asset
- `approved` (boolean) — deve ser `true`

### 3. Build Export Package (Code Node — Python)
Monta pacote JSON com metadados de exportação.

### 4. Notify Operator (NoOp)
Ponto de substituição para notificação real (email, webhook, Telegram, etc).

## Como Importar

1. Acesse o n8n local em `http://localhost:5678`
2. Vá em **Workflows → Import from File**
3. Selecione `workflows/n8n/wf_approval_to_export.json`
4. Configure as credenciais se substituir o NoOp por notificação real
5. Clique em **Save** e depois **Execute Workflow**

## Variáveis Necessárias

Nenhuma credencial real embutida no workflow. Se substituir os Code Nodes por HTTP Request, você precisará configurar:

| Variável | Onde | Exemplo |
|---|---|---|
| `OMNIS_API_URL` | HTTP Request node | `http://localhost:8000/api/v1/export` |
| `OMNIS_API_KEY` | Header Auth | `Bearer <sua-chave>` |

## Riscos

- Workflow só deve ser executado com drafts **já aprovados** no OMNIS
- Não substitui o approval gate do OMNIS — é uma etapa de exportação
- Code Nodes usam Python — revise antes de adicionar credenciais reais

## Rollback

1. Desative o workflow em n8n
2. Remova manualmente se necessário

## Teste em Dry-Run

No n8n, use o botão **Execute Workflow** com dados de teste:

```json
{
  "draft_id": "test-001",
  "caption": "Legenda de teste",
  "perfil": "@lucastigrereal",
  "asset_url": "https://example.com/test.mp4",
  "approved": true,
  "timestamp": "2026-05-04T21:00:00Z"
}
```

## O que NÃO Fazer

- Não adicionar credenciais Meta/Instagram neste workflow
- Não configurar HTTP Request apontando para produção antes de testar
- Não ativar execução automática sem validação de payload
- Não compartilhar este JSON com credenciais reais embutidas
