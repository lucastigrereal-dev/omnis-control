#!/bin/bash
# =============================================================
# OMNIS SKILL SYSTEM — Setup Automático v1.0
# Instala 15 Super Skills + Orquestrador de Waves
# Por: Lucas Tigre | github.com/lucastigrereal
# =============================================================
set -e

CYAN="\033[0;36m"; GREEN="\033[0;32m"; YELLOW="\033[1;33m"
RED="\033[0;31m"; BOLD="\033[1m"; RESET="\033[0m"

print_banner() {
  echo -e "${CYAN}"
  echo "  ██████╗ ███╗   ███╗███╗   ██╗██╗███████╗"
  echo " ██╔═══██╗████╗ ████║████╗  ██║██║██╔════╝"
  echo " ██║   ██║██╔████╔██║██╔██╗ ██║██║███████╗"
  echo " ██║   ██║██║╚██╔╝██║██║╚██╗██║██║╚════██║"
  echo " ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║███████║"
  echo "  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝"
  echo -e "         SKILL SYSTEM v1.0${RESET}"; echo ""
}

log_step() { echo -e "${BOLD}${CYAN}[OMNIS]${RESET} $1"; }
log_ok()   { echo -e "${GREEN}  ✓ $1${RESET}"; }
log_warn() { echo -e "${YELLOW}  ⚠ $1${RESET}"; }
log_err()  { echo -e "${RED}  ✗ $1${RESET}"; }

SKILLS_DIR="${SKILLS_DIR:-.claude/skills}"
CLAUDE_MD="CLAUDE.md"

# =============================================================
# 15 SUPER SKILLS — mapeadas por wave
# =============================================================
declare -A SKILLS=(
  ["sdd-brainstorm"]="NeoLabHQ|Spec-Driven Brainstorm — 6 soluções (3 diretas + 3 exploratórias)|wave_0_blueprint"
  ["tree-of-thoughts"]="NeoLabHQ|Tree of Thoughts — explorar/podar/expandir/avaliar com agentes paralelos|wave_0_blueprint"
  ["sdd-plan"]="NeoLabHQ|Spec-Driven Planning — 6 estágios com quality gates automáticos|wave_1_planning"
  ["context-engineering"]="muratcankoylan|Context Engineering — atenção, progressive disclosure, budget|wave_1_planning"
  ["software-architecture"]="NeoLabHQ|Clean Architecture + SOLID + design patterns|wave_2_architecture"
  ["multi-agent-patterns"]="NeoLabHQ|Padrões Supervisor/Swarm/Hierárquico com isolamento de contexto|wave_2_architecture"
  ["do-in-parallel"]="NeoLabHQ|Parallel Agent Dispatch — lança sub-agentes em paralelo por wave|wave_3_execution"
  ["subagent-driven-development"]="NeoLabHQ|Sub-agentes independentes com code review entre iterações|wave_3_execution"
  ["sdd-implement"]="NeoLabHQ|Implementação spec-driven com auto-reparo e breakpoint resume|wave_3_execution"
  ["write-tests"]="NeoLabHQ|Auto Write Tests — cobertura completa com agentes paralelos|wave_4_testing"
  ["fix-tests"]="NeoLabHQ|Auto Fix Tests — reparo sistemático sem tocar lógica de negócio|wave_4_testing"
  ["do-and-judge"]="NeoLabHQ|Execute + Judge Loop — auto-retry com LLM-as-Judge|wave_5_review"
  ["reflect"]="NeoLabHQ|Self-Reflection Framework — quality gatekeeper + confidence threshold|wave_5_review"
  ["review-local-changes"]="NeoLabHQ|Multi-agent review: segurança, bugs, qualidade, testes — 6 papéis|wave_5_review"
  ["git-create-pr"]="NeoLabHQ|PR workflow com conventional commits + emoji mapping automático|wave_6_delivery"
)

declare -a ANTHROPIC_SKILLS=("skill-creator" "mcp-builder" "webapp-testing")

check_deps() {
  log_step "Verificando dependências..."
  for cmd in curl git; do
    if command -v $cmd &>/dev/null; then log_ok "$cmd encontrado"
    else log_err "$cmd não encontrado. Instale antes de continuar."; exit 1; fi
  done
}

setup_dirs() {
  log_step "Criando estrutura de diretórios do Omnis..."
  mkdir -p "$SKILLS_DIR" .claude/agents .claude/hooks .claude/waves docs/skills
  log_ok "Estrutura criada"
}

install_skill() {
  local name="$1" author="$2" desc="$3" wave="$4"
  local dir="$SKILLS_DIR/$name"
  [ -d "$dir" ] && { log_warn "Skill '$name' já existe — pulando"; return 0; }
  mkdir -p "$dir"
  cat > "$dir/SKILL.md" <<SKILLEOF
---
name: $name
version: 1
description: $desc
wave: $wave
author: $author
installed_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
project: omnis
---

# Skill: $name
**Wave:** $wave | **Autor:** $author

$desc

## Uso no Omnis
Esta skill é carregada automaticamente pelo orquestrador quando
a wave correspondente é ativada. Para uso manual:
\`/skill $name <task>\`
SKILLEOF
  log_ok "[$wave] $name"
}

install_all_skills() {
  log_step "Instalando 15 Super Skills..."
  echo ""
  local prev_wave=""
  for name in "${!SKILLS[@]}"; do
    IFS='|' read -r author desc wave <<< "${SKILLS[$name]}"
    [ "$wave" != "$prev_wave" ] && { echo -e "  ${BOLD}${YELLOW}── $wave ──${RESET}"; prev_wave="$wave"; }
    install_skill "$name" "$author" "$desc" "$wave"
  done
  echo ""
  log_step "Instalando Skills Oficiais Anthropic (bonus)..."
  for s in "${ANTHROPIC_SKILLS[@]}"; do
    install_skill "$s" "Anthropic" "Skill oficial Anthropic" "wave_utils"
  done
}

generate_orchestrator() {
  log_step "Gerando Orquestrador de Waves..."
  mkdir -p .claude/waves
  cat > ".claude/waves/orchestrator.md" <<'ORCH'
# OMNIS — Wave Orchestrator v1.0

Você é o Orquestrador de Waves do sistema Omnis.
Ao receber um blueprint, execute EXATAMENTE este pipeline:

## WAVE 0 — Blueprint Analysis (Paralelo)
Skills: sdd-brainstorm + tree-of-thoughts
Gate: Blueprint validado + solução escolhida com justificativa

## WAVE 1 — Planning (Sequencial)
Skills: sdd-plan → context-engineering
Gate: Plano com todas as waves + skills mapeadas

## WAVE 2 — Architecture (Paralelo)
Skills: software-architecture + multi-agent-patterns
Gate: Arquitetura documentada com diagramas

## WAVE 3 — Execution (Totalmente Paralelo)
Skills: do-in-parallel + sdd-implement + subagent-driven-development
Um agente por módulo, todos simultâneos, contextos isolados.
Gate: Todos os módulos implementados

## WAVE 4 — Testing (Paralelo + Loop)
Skills: write-tests → fix-tests (loop até 100% green)
Gate: Todos os testes passando

## WAVE 5 — Review & Auto-Correction (Iterativo)
Skills: review-local-changes + do-and-judge + reflect
Loop até score >= 8.5/10. Se reprovado, volta à Wave 3.
Gate: Score >= 8.5 em todas as dimensões

## WAVE 6 — Delivery (Sequencial)
Skills: codebase-documenter → git-commit-neolab → git-create-pr
Gate: PR aberto + documentação gerada

## Acionamento
Quando o usuário disser "execute o blueprint", "roda o Omnis",
"build [projeto]" ou similar — inicie da Wave 0 até Wave 6
reportando o gate de cada wave antes de avançar.

Reporte formato:
  ✅ Wave X concluída | Skills: X,Y | Gate: APROVADO
  ⏭️  Iniciando Wave X+1...
ORCH
  log_ok "Orquestrador criado em .claude/waves/orchestrator.md"
}

generate_blueprint() {
  log_step "Gerando BLUEPRINT.md..."
  if [ -f "BLUEPRINT.md" ]; then
    # Preserve existing content, just warn
    log_warn "BLUEPRINT.md já existe — preservando conteúdo atual"
    return 0
  fi
  cat > "BLUEPRINT.md" <<'BP'
# OMNIS BLUEPRINT — [Nome do Projeto]
> Preencha e execute: claude "execute o blueprint em BLUEPRINT.md"

## 1. O QUE É O PROJETO


## 2. OBJETIVO PRINCIPAL


## 3. USUÁRIOS / CLIENTES


## 4. FUNCIONALIDADES CORE
-
-
-

## 5. STACK TECNOLÓGICA
- Frontend:
- Backend:
- Banco:
- Infra:

## 6. INTEGRAÇÕES EXTERNAS
-

## 7. RESTRIÇÕES / NÃO FAZER
-

## 8. CRITÉRIOS DE SUCESSO
-

## 9. PRAZO / URGÊNCIA

---
*OMNIS Skill System v1.0*
BP
  log_ok "BLUEPRINT.md criado na raiz"
}

update_claude_md() {
  log_step "Atualizando CLAUDE.md..."
  if grep -q "OMNIS SKILL SYSTEM" "$CLAUDE_MD" 2>/dev/null; then
    log_warn "CLAUDE.md já tem seção OMNIS SKILL SYSTEM — pulando"
    return 0
  fi
  cat >> "$CLAUDE_MD" <<'CMD'

## OMNIS SKILL SYSTEM v1.0

Skills em: .claude/skills/ | Orquestrador: .claude/waves/orchestrator.md

### Waves do Pipeline
- Wave 0: sdd-brainstorm + tree-of-thoughts (Blueprint Analysis)
- Wave 1: sdd-plan + context-engineering (Planning)
- Wave 2: software-architecture + multi-agent-patterns (Architecture)
- Wave 3: do-in-parallel + sdd-implement + subagent-driven-development (Execution)
- Wave 4: write-tests + fix-tests (Testing)
- Wave 5: review-local-changes + do-and-judge + reflect (Review)
- Wave 6: codebase-documenter + git-commit-neolab + git-create-pr (Delivery)

### Como usar
1. Preencha BLUEPRINT.md
2. Execute: claude "execute o blueprint em BLUEPRINT.md"
CMD
  log_ok "CLAUDE.md atualizado"
}

print_summary() {
  echo ""
  echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}${GREEN}║   OMNIS SKILL SYSTEM — INSTALADO! ✓     ║${RESET}"
  echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════╝${RESET}"
  echo ""
  echo -e "  Skills instaladas : ${BOLD}18${RESET} (15 super + 3 Anthropic)"
  echo -e "  Waves configuradas: ${BOLD}7${RESET} (Wave 0 → Wave 6)"
  echo -e "  Orquestrador      : ${BOLD}.claude/waves/orchestrator.md${RESET}"
  echo ""
  echo -e "  ${BOLD}${CYAN}PRÓXIMO PASSO:${RESET}"
  echo -e "  1. Edite o ${BOLD}BLUEPRINT.md${RESET}"
  echo -e "  2. Execute: ${BOLD}claude \"execute o blueprint em BLUEPRINT.md\"${RESET}"
  echo ""
}

main() {
  print_banner
  check_deps
  setup_dirs
  install_all_skills
  generate_orchestrator
  generate_blueprint
  update_claude_md
  print_summary
}

main "$@"
