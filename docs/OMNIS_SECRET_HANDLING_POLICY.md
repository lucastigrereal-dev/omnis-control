# OMNIS Secret Handling Policy

## Regras Absolutas

1. **Nunca imprimir segredo** — não exibir no chat, log, terminal, ou tela
2. **Nunca copiar segredo** para chat, clipboard, ou arquivo de log
3. **Nunca commitar segredo** — usar variável de ambiente
4. **Nunca escrever segredo** em arquivos não-.gitignored

## Protocolo ao Encontrar Segredo

1. **NÃO ler o valor** além do necessário para confirmar que é segredo
2. **Registrar localização** (arquivo, linha) sem copiar o valor
3. **Adicionar P0** em `omnis_blocked_items.yaml`
4. **Substituir** valor real por placeholder de env var:
   ```yaml
   # Antes (PERIGOSO):
   auth: "sk-abc123..."
   # Depois (SEGURO):
   auth: "${LITELLM_MASTER_KEY}"
   ```
5. **Criar/atualizar** arquivo `.example` seguro (sem valores reais)
6. **Recomendar rotação/revogação** da chave exposta

## Padrões de Alto Risco

- `api_key`
- `secret`
- `token`
- `sk-` (chaves Stripe/OpenAI)
- `AKIA` (chaves AWS)
- `master key`
- `password`

## Arquivos de Alto Risco

- `.env` e `.env.*`
- `config/*.yaml` (especialmente `connectors.yaml`)
- `config/*.json`
- `credentials.*`
- `*.key`, `*.pem`

## Exemplo Seguro

`config/connectors.example.yaml`:
- Mesma estrutura do original
- Valores trocados por placeholders (`${VAR_NAME}`)
- Comentários explicando como obter cada valor
- Seguro para commitar e compartilhar
