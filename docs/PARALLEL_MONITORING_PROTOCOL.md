# Protocolo de Monitoramento Paralelo OMNIS

## 1. Objetivo

A aba principal (master) do OMNIS é responsável por monitorar o estado de todas as frentes paralelas em execução. Enquanto cada frente trabalha de forma isolada em sua worktree, a aba principal observa, valida e decide quando cada frente está pronta para merge.

Este protocolo define como usar o script `scripts/omnis_parallel_monitor.ps1` para acompanhar o estado da esteira paralela sem interferir no trabalho das frentes.

---

## 2. Conceitos

**Aba principal**
A instância do Claude Code rodando sobre o branch `master` em `C:\Users\lucas\omnis-control`. É ela que faz merges, roda full suites e mantém o histórico oficial.

**Aba de frente**
Uma instância do Claude Code rodando sobre uma worktree paralela (ex.: `C:\Users\lucas\omnis-p13-analytics-skeleton`). Cada frente tem escopo restrito e não deve afetar o master diretamente.

**Worktree**
Um checkout paralelo do mesmo repositório git em um diretório diferente. Permite que várias branches existam em disco simultaneamente sem `git stash` ou troca de branch.

**Branch parallel**
Branches no formato `parallel/<nome>` (ex.: `parallel/p13-analytics-skeleton`). Cada frente opera em sua branch própria. Após merge no master, essas branches são deletadas.

**Status clean**
Uma worktree está clean quando `git status --short` retorna vazio — nenhum arquivo modificado, nenhum arquivo não-rastreado relevante. É condição necessária para merge.

**Status dirty**
Uma worktree está dirty quando há arquivos pendentes. Pode ser intencional (trabalho em andamento) ou ruído operacional (logs, exports, timestamps). Verificar antes de declarar como bloqueio.

**Ready for merge**
Frente considerada pronta quando: path existe, branch começa com `parallel/`, worktree está clean e há ao menos um commit próprio registrado.

---

## 3. Como carregar o monitor

Execute a partir da raiz de `omnis-control`:

```powershell
. .\scripts\omnis_parallel_monitor.ps1
```

O ponto-espaço (`. `) carrega as funções no escopo atual da sessão PowerShell.

---

## 4. Como ver status uma vez

```powershell
Get-OmnisParallelStatus
```

Exibe tabela com todas as frentes detectadas automaticamente via `git worktree list` e scan de `C:\Users\lucas\omnis-*`.

Para fornecer frentes manualmente (quando worktrees ainda não existem):

```powershell
Get-OmnisParallelStatus -Fronts @("p13-analytics-skeleton", "p15-computer-ops-readonly")
```

---

## 5. Como acompanhar em tempo quase real

```powershell
Watch-OmnisParallelStatus -IntervalSeconds 20
```

Limpa a tela a cada ciclo, exibe horário e tabela atualizada. Encerre com `Ctrl+C`.

---

## 6. Como exportar JSON

```powershell
Export-OmnisParallelStatusJson
```

Cria `reports/parallel_status.json` com `generated_at` e lista de frentes. O diretório `reports/` é criado automaticamente se necessário. Só escreve quando chamada explicitamente — o monitor não exporta por conta própria.

---

## 7. O que significa clean

Uma frente está **clean** quando `git status --short` dentro da worktree retorna vazio. Isso significa:

- Nenhum arquivo modificado (staged ou unstaged)
- Nenhum arquivo não-rastreado relevante
- O código entregue pela frente está exatamente como foi commitado

Clean é condição necessária (mas não suficiente) para merge no master.

---

## 8. O que significa dirty

Uma frente está **dirty** quando há linhas em `git status --short`. Nem sempre é bloqueio — dirty pode ser:

- Arquivos criados durante desenvolvimento ainda não commitados
- Arquivos modificados após o commit (retrabalho)
- Diretório `exports/` gerado por runs de teste
- Documentos `docs/` gerados automaticamente por scripts
- Arquivos de `logs/` ou `.cache/`
- Timestamps e snapshots operacionais (`paths.yaml`, `ESTADO_ATUAL_RESUMIDO.md`)
- Sujeira de IDE (`.vscode/`, `__pycache__/`)

**Regra:** antes de declarar uma frente como bloqueada por dirty, inspecione `git diff` e `git status` para distinguir ruído de mudança real.

---

## 9. Quando uma frente está pronta para merge

Uma frente está **pronta para merge** quando todos os critérios abaixo são atendidos:

- [ ] Commit feito com mensagem descritiva
- [ ] Testes da suite da frente passaram (`python -m pytest tests/<frente>/ -q`)
- [ ] Worktree está clean (sem arquivos pendentes)
- [ ] Relatório final entregue em `docs/` (opcional mas recomendado)
- [ ] Frente não tocou arquivos fora de seu escopo declarado

A aba principal valida esses critérios antes de executar `git merge --no-ff`.

---

## 10. O que fazer se aparecer arquivo fora de escopo

Se durante a revisão pré-merge aparecer modificação em arquivo que a frente não deveria tocar:

1. **Pare** — não faça merge.
2. **Inspecione** com `git diff` dentro da worktree.
3. **Se for ruído operacional** (timestamp, log): restaure com `git restore <arquivo>` ou stash.
4. **Se for mudança real** fora do escopo: peça revisão e justificativa antes de prosseguir.
5. Documente a ocorrência no relatório da frente.

---

## 11. Relação com Onda 2

A Onda 2 deverá ser composta pelas seguintes frentes:

| Frente | Branch | Escopo |
|---|---|---|
| `p13-analytics-skeleton` | `parallel/p13-analytics-skeleton` | Pipeline de analytics e métricas |
| `p15-computer-ops-readonly` | `parallel/p15-computer-ops-readonly` | Operações read-only de infraestrutura |
| `p18-governance-audit` | `parallel/p18-governance-audit` | Auditoria e conformidade de governança |

Antes de abrir a Onda 2, confirmar:
- Master limpo
- Full suite da Onda 1 passando (2360 passed)
- `git worktree list` mostrando apenas `omnis-control`
- Nenhuma branch `parallel/*` pendente

---

## 12. Futuro Squad Runner

Este monitor é o embrião do futuro **OMNIS Squad Runner** — um sistema que automatizará a gestão completa da esteira paralela. Componentes planejados:

| Componente | Função |
|---|---|
| **Worktree Manager** | Cria, lista e remove worktrees automaticamente |
| **Prompt Generator** | Gera o prompt de instrução para cada frente com escopo restrito |
| **Claude Runner** | Abre e direciona abas de Claude Code por frente |
| **Status Collector** | Agrega status de todas as frentes em tempo real |
| **Test Gate** | Valida targeted tests antes de liberar para merge |
| **Merge Gate** | Executa merge sequencial seguro com rollback automático em caso de falha |

O Squad Runner transformará o processo manual atual (abas abertas pelo operador, prompts copiados, merges feitos um a um) em uma pipeline supervisionada e auditável.
