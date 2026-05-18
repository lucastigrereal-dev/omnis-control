# PRD — PubliPrice v1.0

## Documento de Requisitos de Produto

**Versao:** 1.0
**Data:** 2026-05-18
**Status:** Em desenvolvimento
**Autor:** Lucas Tigre (Operador OMNIS)

---

## 1. Declaracao do Problema

Lucas Tigre opera 6 perfis no Instagram totalizando 2,58 milhoes de seguidores nos nichos de turismo, gastronomia e familia. Ele vende collabs (collaborations) para hoteis e restaurantes atraves de tres pacotes: Starter (R$350), Growth (R$990/mes) e Premium (R$1.200).

Atualmente, a precificacao e feita de forma manual e intuitiva. Nao existe uma ferramenta que:

- Calcule automaticamente o preco com base em metricas reais (seguidores, engajamento, alcance)
- Compare o CPM (custo por mil impressoes) com anuncios Meta Ads para justificar o valor ao cliente
- Gere propostas profissionais de forma rapida
- Mantenha historico de cotacoes para analise futura
- Permita ajustes por nicho (turismo tem CPM diferente de gastronomia)

**Consequencia:** Tempo perdido em negociacoes, precificacao inconsistente, dificuldade em justificar valor para clientes, e ausencia de dados historicos para otimizar a estrategia comercial.

## 2. Objetivo

Construir o **PubliPrice** — uma calculadora local-first de precificacao de pacotes de collab no Instagram. O app roda 100% offline, sem dependencia de nuvem, e permite que o operador calcule precos em segundos, gere propostas e mantenha historico.

## 3. Usuarios-Alvo

### Primario
**Lucas Tigre** — Operador solo, 6 perfis, venda direta para hoteis e restaurantes. Precisa de agilidade e precisao. TDAH: interface simples, sem friccao.

### Secundario (futuro)
**Influenciadores parceiros** — 150 influenciadores do Interior de SP no pipeline. Poderiam usar a mesma logica de precificacao.

## 4. Personas

| Persona | Necessidade | Dor |
|---|---|---|
| **Operador Solo** | Calcular preco em < 30s | Perde tempo no Excel |
| **Vendedor SDR** | Gerar proposta na hora da call | Nao sabe justificar o valor |
| **Cliente Hotel** | Entender o ROI da collab | Acha caro comparado a Meta Ads |

## 5. Requisitos Funcionais

### RF01 — Gestao de Perfis
O sistema deve permitir cadastrar, editar e visualizar os 6 perfis Instagram com: handle, seguidores, nicho, taxa de engajamento, alcance medio.

### RF02 — Gestao de Pacotes
O sistema deve manter os 3 pacotes padrao (Starter, Growth, Premium) com suas composicoes (quantidade de collabs, stories, reels, carrosseis) e preco base.

### RF03 — Calculo de Preco (Core)
O sistema deve calcular o preco sugerido para uma cotacao com base em:
- Perfil selecionado (seguidores, engajamento, alcance)
- Pacote selecionado (composicao, preco base)
- Nicho do perfil (fator de ajuste)
- Volume mensal (desconto por quantidade)
- Formula: `preco = preco_base_pacote * fator_seguidores * fator_engajamento * fator_nicho * fator_volume`

### RF04 — Comparativo CPM
O sistema deve exibir o CPM estimado da collab e compara-lo com o CPM medio de Meta Ads (R$15-25), destacando a economia percentual.

### RF05 — Historico de Cotacoes
O sistema deve armazenar todas as cotacoes geradas com: perfil, pacote, cliente, preco calculado, desconto aplicado, preco final, data e status.

### RF06 — Exportacao de Proposta
O sistema deve gerar uma proposta em texto markdown simples (copiavel) com: apresentacao do perfil, composicao do pacote, preco, comparativo CPM, validade.

### RF07 — Ajuste Manual
O operador pode aplicar desconto percentual ou valor fixo sobre o preco calculado, com registro do motivo.

### RF08 — Templates por Nicho
O sistema deve ajustar automaticamente o fator de precificacao conforme o nicho:
- Turismo: fator 1.0 (base)
- Gastronomia: fator 0.9 (mercado mais competitivo)
- Familia: fator 1.1 (publico mais segmentado)
- Lifestyle/Autoridade: fator 1.2 (maior influencia)

## 6. Requisitos Nao-Funcionais

### RNF01 — Local-First
Aplicacao roda 100% local. Zero dependencia de nuvem. SQLite como banco de dados.

### RNF02 — Performance
Calculo de preco em < 100ms. Interface responde em < 50ms para acoes CRUD.

### RNF03 — Portabilidade
Funciona em Windows 10/11. Script Python executavel. Backend Python 3.12, frontend HTML + vanilla JS servido localmente.

### RNF04 — Seguranca
Dados armazenados localmente em SQLite. Sem envio de dados para servidores externos. Sem dependencia de autenticacao.

### RNF05 — Usabilidade
Interface escura (dark theme) consistente com o cockpit OMNIS/KRATOS. Maximo 2 cliques para chegar ao resultado do calculo. Compativel com uso via teclado (TDAH-friendly).

### RNF06 — Extensibilidade
Formula de precificacao parametrizavel (fatores em arquivo de configuracao). Facil adicionar novos pacotes e perfis.

## 7. Metricas de Sucesso

| Metrica | Alvo | Medicao |
|---|---|---|
| Tempo para gerar cotacao | < 30 segundos | Cronometro manual |
| Cotacoes geradas/dia | > 5 | Contagem no historico |
| Precisao do CPM | Desvio < 5% do real | Comparacao pos-publicacao |
| Uso diario | 5+ dias/semana | Log de atividade |
| Satisfacao | "Nao volto pro Excel" | Qualitativo |

## 8. Escopo MVP

### Inclui (v1.0)
- CRUD de 6 perfis (seed data pre-carregada)
- 3 pacotes padrao (seed data pre-carregada)
- Calculadora com formula completa
- Comparativo CPM
- Historico de cotacoes
- Exportacao markdown
- Interface dark theme 3 views (Calculadora, Historico, Perfis)

### Nao inclui (v1.0)
- Multi-usuario / login
- Sincronizacao com nuvem
- Integracao com API do Instagram
- Graficos de analise
- Exportacao PDF formatada
- Upload de midia
- CRM integrado

## 9. Stack Tecnologica

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Backend | Python 3.12 + Flask | Simplicidade, ecossistema conhecido |
| Banco | SQLite (arquivo local) | Zero setup, portatil, confiavel |
| Frontend | HTML + vanilla JS + CSS | Sem build step, carrega instantaneo |
| Estilo | CSS customizado dark theme | Consistencia visual com cockpit |
| Testes | pytest | Padrao OMNIS |
| CLI | Typer | CLI opcional para calculos rapidos |

## 10. Riscos

| Risco | Probabilidade | Mitigacao |
|---|---|---|
| Formula simplista demais | Media | Fatores parametrizaveis via config |
| Dados de engajamento desatualizados | Alta | Campo editavel manualmente + atualizacao futura via API |
| Abandono por friccao na UI | Media | Teste com operador real no dia 1 |
| Escopo crescer para CRM completo | Alta | Gate rigido: MVP e calculadora, ponto. |

## 11. Próximos Passos

1. Aprovar PRD (operador)
2. Gerar schema SQL e seed data
3. Implementar formula core com testes
4. Construir frontend 3 views
5. Teste de usabilidade com operador real
6. Empacotar e distribuir

---

**Aprovado por:** _____________ **Data:** _____________
