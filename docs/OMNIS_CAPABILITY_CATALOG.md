# OMNIS Capability Catalog
**Data:** 2026-05-18 | Baseado em outputs reais das fases 0-10

## 1. Campanha 30 dias (Content Factory)
- **Status:** PRONTO
- **Input:** projeto, nicho, objetivo, cidade/região, canal Instagram
- **Output:** 30 legendas SEOgram + 30 roteiros Reels + calendário CSV + estratégia + proposta comercial + tabela de preços
- **Arquivo exemplo:** missions/MIS-20260518-002/05_outputs/
- **Comando atual:** invocar skill omnis via Claude Code com brief da missão
- **Limitações:** sem publicação automática, sem agendamento real
- **Próxima evolução:** integrar com Publer para agendar direto

## 2. Carrossel Premium (Design Engine)
- **Status:** PRONTO
- **Input:** tema, perfil, tom, objetivo
- **Output:** estrutura slide a slide + copy + briefing Canva + direção visual + CTA + legenda SEOgram
- **Arquivo exemplo:** missions/MIS-20260518-003/05_outputs/
- **Comando atual:** mission brief via Claude Code
- **Limitações:** sem geração de imagem, sem exportação PNG
- **Próxima evolução:** preview HTML navegável

## 3. Pacote de Reels (Video Engine)
- **Status:** PRONTO
- **Input:** tema, perfil, nicho, tom
- **Output:** 10 roteiros cena a cena + 10 hooks + textos de tela + capas + legendas + briefing de edição
- **Arquivo exemplo:** missions/MIS-20260518-004/05_outputs/
- **Comando atual:** mission brief via Claude Code
- **Limitações:** sem processamento de vídeo real, sem SRT, sem render
- **Próxima evolução:** Video Studio com ffmpeg + whisper local

## 4. Blueprint de App (App Factory)
- **Status:** PRONTO
- **Input:** nome do app, domínio, usuários-alvo, features
- **Output:** PRD + user stories + schema SQL + API contract + frontend spec + test plan + README
- **Arquivo exemplo:** missions/MIS-20260518-005/05_outputs/
- **Comando atual:** mission brief via Claude Code
- **Limitações:** sem scaffold real de código, sem deploy
- **Próxima evolução:** repo scaffold + openhands mock

## 5. Criação de Skill (Capability Forge)
- **Status:** PRONTO
- **Input:** nome da skill, descrição, input/output esperado
- **Output:** SKILL.md + run.py + manifest.json + sample_payload.json + skill_report.md
- **Arquivo exemplo:** missions/MIS-20260518-006/05_outputs/
- **Comando atual:** mission brief via Claude Code
- **Limitações:** sem registro automático em skills.yaml
- **Próxima evolução:** auto-registro + testes automáticos

## 6. Daily Briefing (Autonomous Ops)
- **Status:** PRONTO
- **Input:** data, projetos ativos
- **Output:** briefing do dia com prioridades, tarefas e alertas
- **Arquivo exemplo:** docs/AUTONOMOUS_OPS_REPORT.md
- **Comando atual:** scripts/autonomous_ops.py
- **Limitações:** sem dados em tempo real, sem integração externa

## 7. Weekly Pack (Autonomous Ops)
- **Status:** PRONTO
- **Input:** semana, projetos
- **Output:** pack semanal com conteúdo, vídeos, design, proposta
- **Arquivo exemplo:** docs/AUTONOMOUS_OPS_REPORT.md
- **Próxima evolução:** Weekly Production Ritual com comando curto

## 8. Proposta Comercial
- **Status:** PRONTO (dentro de Content Factory)
- **Input:** perfil, nicho, dados de audiência
- **Output:** proposta pronta para hotéis/restaurantes com pacotes Starter/Growth/Premium
- **Arquivo exemplo:** missions/MIS-20260518-002/05_outputs/proposta_comercial.md

## 9. Cockpit Local
- **Status:** PRONTO
- **Input:** dados das missões (missions_data.js, ops_data.js)
- **Output:** dashboard HTML navegável com missões, outputs, approvals
- **Arquivos:** cockpit/index.html + cockpit/*.html
- **Como usar:** abrir cockpit/index.html no browser

## 10. Validação de Missão (Mission Acceptance)
- **Status:** PRONTO
- **Input:** mission_contract.json
- **Output:** validação estrutural, checagem de gates, relatório
- **Arquivo exemplo:** missions/MIS-20260518-001/
- **Comando atual:** scripts/mission_acceptance_test.py
