# CODEX Backfill Audit — Onda 1 (Portability, File Locking, Interfaces)

Data: 2026-05-23  
Branch: `feature/omnis-5waves-runtime-supreme`  
Commits auditados: `00c221a`, `0893587`, `080461b`

## 1) Segurança / Portabilidade

## Portabilidade (00c221a)
- Migração para `OMNIS_ROOT` via `os.getenv` está aplicada nos arquivos auditados.
- Não foram encontrados novos hardcodes críticos de path nesses pontos.

## Interfaces (080461b)
- Protocols de Browser/Code estão claros e com teste de contrato (`tests/interfaces/test_lego_contracts.py`).
- Sem achado de segurança direto nessa camada.

## File Locking (0893587) — Achado principal
- `src/utils/file_lock.py` protege concorrência **in-process** com `threading.Lock`.
- Para concorrência **cross-process**, comportamento atual é apenas advisory:
  - se `.lock` já existe (`FileExistsError`), `_acquire_os_lock` retorna `None` e execução segue.
  - isso permite entrada simultânea de processos na seção crítica.

### Prova reproduzida nesta auditoria
- Processo A entrou no lock e segurou por ~3s.
- Processo B entrou quase instantaneamente (`~0.001s`) no mesmo lock path.
- Conclusão: lock cross-process não está efetivamente serializando.

## Classificação de risco
- **P1 (integridade de dados)** para cenários multi-processo, especialmente onde há rewrite de JSONL.

## 2) Cobertura adicionada

Arquivo:
- `tests/utils/test_file_lock.py`

Novo teste:
- `test_cross_process_lock_blocks_until_release` (marcado `xfail`)

Motivo:
- registrar a expectativa correta de bloqueio cross-process sem quebrar suíte atual.
- transforma o gap em dívida técnica explícita e rastreável.

## 3) Recomendação para frente de construção

1. Implementar lock cross-process real:
   - Windows: usar `msvcrt.locking` em handle compartilhado.
   - POSIX: usar `fcntl.flock` no arquivo de lock.
2. Em fallback degradado, **não** entrar na seção crítica quando lock externo não puder ser adquirido.
3. Após correção, remover `xfail` e validar teste como obrigatório.

