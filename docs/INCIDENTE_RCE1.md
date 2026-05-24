# INCIDENTE_RCE1 — SandboxRunner: Host-Exec Residual

**Status:** TRANCADO — real execution disabled pending container sandbox  
**Data:** 2026-05-24  
**Componente:** `src/capability_forge_real/sandbox.py` → `SandboxRunner.run()`  
**Acionado por:** self-improvement pipeline (stub, não ativo em produção)

---

## O que está aberto

O `SandboxRunner` executava código Python no mesmo processo (exec-in-process).
Fix anterior: subprocess isolation (código roda num processo filho separado).

**Problema residual confirmado pelo Codex em runtime:**  
O subprocess filho roda **no host OS** sem nenhum isolamento real. Código sandbox pode:

- Criar e ler arquivos arbitrários (`open('/etc/passwd', 'r')`)
- Ler variáveis de ambiente (`os.environ`)
- Spawnar processos filhos (`os.popen`, `subprocess` via bypass de scanner)
- Acessar a rede (se libs não bloqueadas)
- Consumir CPU/memória sem limite

O scanner estático (FORBIDDEN_CALLS) é burlável por ofuscação simples:
```python
# Burla o scanner — 'subprocess' não aparece como palavra isolada
mod = 'sub' + 'process'
__import__(mod).run(['whoami'], capture_output=True)
```

**Conclusão:** subprocess isolation protege o processo pai (OMNIS), mas não isola
o host. Não é um sandbox real.

---

## Por que foi trancado

O `SandboxRunner` é acionado exclusivamente pelo self-improvement pipeline
(`capability_forge_real`), que hoje é **stub** — não roda em produção.

Curar corretamente exige dias de trabalho (container isolado). Travar agora custa
5 linhas e fecha o risco sem bloquear nada que esteja em uso real.

**Mecanismo de travamento:**  
`_EXEC_DISABLED = True` em `sandbox.py` — qualquer chamada a `run()` que passe
o scanner levanta `SandboxDisabledError`. O modo `dry_run_validate()` (scan only)
permanece funcional.

---

## O que a cura real exige

Os 5 passos para um sandbox seguro de verdade:

### 1. Container / Job Object isolado
Rodar o código num container Docker efêmero (ou Windows Job Object) com namespace
de processo separado. O processo filho não enxerga o host fora do container.

```bash
docker run --rm --network none --read-only \
  --memory 128m --cpus 0.5 \
  python:3.12-slim python /code/sandbox_input.py
```

### 2. Ambiente mínimo (env mínimo)
Zerar variáveis de ambiente antes de criar o container. Não passar `PATH`,
`HOME`, credenciais, tokens de API, ou `PYTHONPATH` do host.

```python
env = {"PYTHONDONTWRITEBYTECODE": "1"}  # somente o necessário
```

### 3. Bloqueio de spawn de processos
No container: `--security-opt no-new-privileges`. No Linux, adicionar seccomp
profile bloqueando `fork`, `clone`, `execve` após o interpretador Python iniciar.

### 4. FS allowlist (filesystem)
Container com sistema de arquivos read-only (`--read-only`). Montar apenas
`/tmp` como tmpfs com tamanho limitado para código que precise de I/O.

```bash
--tmpfs /tmp:size=10m,noexec
```

### 5. Limite de memória e CPU
`--memory 128m --memory-swap 128m --cpus 0.5 --pids-limit 50`  
Previne fork bombs e consumo de recursos do host.

---

## Quando ativar

A cura real entra como tarefa ao ativar o self-improvement pipeline.
Remover `_EXEC_DISABLED = True` de `sandbox.py` **só após** os 5 passos
acima estarem implementados e testados.

Palavra-chave de busca para retomar: `INCIDENTE_RCE1`, `_EXEC_DISABLED`.
