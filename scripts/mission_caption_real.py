"""Missao real: gerar legenda via Ollama usando o pipeline E2E completo."""
import json
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ["OMNIS_DRY_RUN"] = "false"

from src.skills.caption_skill import CaptionRequest, CaptionResult, build_full_prompt
from src.skills_bridge.models import SkillCall, SkillIntent
from src.skills_bridge.adapter import RealSkillAdapter

print("=" * 60)
print("MISSAO REAL: Gerar legenda para @lucastigrereal")
print("Topic: viagem em Natal com familia")
print("=" * 60)

# 1. Construir prompt
req = CaptionRequest(
    topic="viagem em Natal com familia",
    page="@lucastigrereal",
    tone="autentico e caloroso",
    max_words=120,
)
prompts = build_full_prompt(req)
print(f"\n[PROMPT] {len(prompts['user'])} chars")

# 2. Criar adapter real (dry_run=False)
adapter = RealSkillAdapter(dry_run=False)
adapter._router.dry_run = False

# 3. SkillCall (dry_run=False em tudo)
call = SkillCall(
    skill_id="generate_caption",
    intent=SkillIntent.CREATE,
    input_payload={"prompt": prompts["user"], "system": prompts["system"]},
    dry_run=False,
)

print("[EXECUTANDO] RealSkillAdapter -> ModelRouter -> Ollama...")
result = adapter.call_skill(call)

print(f"\n[STATUS] {result['status']}")
print(f"[MODELO] {result.get('model_used', 'N/A')}")
print(f"[PROVIDER] {result.get('provider', 'N/A')}")

output_text = result.get("output", "SEM OUTPUT")

# 4. Salvar em arquivo
output_dir = Path("exports/captions")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "legenda_natal_familia.json"

caption_result = CaptionResult.from_llm_response(
    output_text,
    req,
    model_used=result.get("model_used", "unknown"),
)
caption_result.save(str(output_path))

# Tambem salvar o texto puro pra leitura facil
txt_path = output_dir / "legenda_natal_familia.txt"
txt_path.write_text(output_text, encoding="utf-8")

print(f"\n[ARQUIVO SALVO] {output_path}")
print(f"[TXT SALVO] {txt_path}")
print(f"[HOOK] {caption_result.hook[:80]}")
print(f"[HASHTAGS] {caption_result.hashtags}")
print(f"\n--- LEGENDA (primeiras 300 chars) ---")
# Encoding seguro pro terminal Windows
print(output_text[:300].encode("ascii", errors="replace").decode("ascii"))
