"""aurora_think.py — roda o pensador Aurora uma vez e mostra o insight.

Fase 2: por padrão GRAVA aurora_insight no data/state.json (merge-safe).
Use --no-write para apenas mostrar sem gravar.

Uso:
    python aurora_think.py            # pensa e grava no state.json
    python aurora_think.py --no-write # pensa e só mostra (não grava)
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, str(Path(__file__).parent))

from src.aurora.thinker import AuroraThinker, write_insight_to_state

def main():
    write = "--no-write" not in sys.argv

    print("\n" + "=" * 60)
    print("  AURORA — pensador OMNIS (Ollama local, custo zero)")
    print("=" * 60)

    thinker = AuroraThinker()

    print("\n[1/4] Verificando Ollama...")
    if not thinker.health_check():
        print("ERRO: Ollama não está respondendo. Inicie o Ollama e tente novamente.")
        sys.exit(1)
    print("      Ollama OK [ok]")

    print(f"\n[2/4] Carregando dados e enviando para {thinker.model}...")
    print("      (pode levar 10-30s na primeira execução)")

    result = thinker.think()

    print("\n[3/4] INSIGHT GERADO PELA AURORA:")
    print("-" * 60)
    print(result.insight)
    print("-" * 60)
    print(f"\nmodelo:  {result.model_used}")
    print(f"tokens:  {result.tokens_used}")
    print(f"horário: {result.updated_at}")

    print("\n[4/4] Persistência:")
    if write:
        path = write_insight_to_state(result)
        print(f"      GRAVADO em {path} (chaves aurora_* mescladas)")
    else:
        print("      --no-write: NÃO gravado (só exibição)")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
