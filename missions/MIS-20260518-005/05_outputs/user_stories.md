# User Stories — PubliPrice v1.0

**Projeto:** PubliPrice — Calculadora de Precificacao de Collabs
**Data:** 2026-05-18
**Formato:** "Como [perfil], quero [acao] para [beneficio]"

---

## US01 — Pre-cadastro de perfis
**Como** operador solo,
**quero** que os 6 perfis ja venham pre-cadastrados com dados reais de seguidores, nicho e engajamento
**para** comecar a calcular precos imediatamente, sem precisar configurar nada.

**Criterios de aceitacao:**
- [ ] Os 6 perfis (@lucastigrereal, @oinatalrn, @agenteviajabrasil, @afamiliatigrereal, @oquecomernatalrn, @natalaivoueu) aparecem na tela de Perfis ao abrir o app
- [ ] Cada perfil tem: handle, seguidores, nicho, engagement_rate, alcance_medio
- [ ] Dados correspondem a realidade de maio/2026

---

## US02 — Visualizar metricas de um perfil
**Como** operador solo,
**quero** clicar em um perfil e ver todas as suas metricas (seguidores, engajamento, alcance, nicho)
**para** decidir rapidamente qual perfil usar na proposta.

**Criterios de aceitacao:**
- [ ] Card de perfil exibe: foto/avatar, @handle, seguidores formatados (ex: 690K), engagement rate %, alcance medio
- [ ] Nicho aparece como badge colorido
- [ ] Um clique expande os detalhes completos

---

## US03 — Editar metricas de um perfil
**Como** operador solo,
**quero** editar manualmente os seguidores, engajamento e alcance de qualquer perfil
**para** manter os dados atualizados mesmo sem integracao com API do Instagram.

**Criterios de aceitacao:**
- [ ] Botao "Editar" no card do perfil abre formulario modal
- [ ] Campos: seguidores (numero), engagement_rate (decimal), alcance_medio (numero)
- [ ] Salvar atualiza no banco SQLite e reflete imediatamente na interface
- [ ] Validacao: seguidores > 0, engagement_rate entre 0 e 100

---

## US04 — Visualizar pacotes disponiveis
**Como** operador solo,
**quero** ver os 3 pacotes padrao (Starter, Growth, Premium) com suas composicoes e precos base
**para** saber exatamente o que cada um inclui antes de cotar.

**Criterios de aceitacao:**
- [ ] Tabela/listagem mostra: nome, collabs, stories, reels, carrosseis, preco_base
- [ ] Pacote Growth destacado como "Recomendado" (liderar venda)
- [ ] Tooltip explica o que cada formato entrega

---

## US05 — Calcular preco de uma collab
**Como** operador solo,
**quero** selecionar um perfil e um pacote, clicar em "Calcular", e ver o preco sugerido com breakdown
**para** gerar uma cotacao em menos de 10 segundos durante uma call com cliente.

**Criterios de aceitacao:**
- [ ] Dropdown de perfil carrega os 6 perfis cadastrados
- [ ] Dropdown de pacote carrega os 3 pacotes
- [ ] Campo opcional "Volume mensal" (1 a 12 meses)
- [ ] Resultado exibe: preco base, fatores aplicados (seguidores, engajamento, nicho, volume), preco final
- [ ] Calculo acontece em tempo real ao mudar qualquer campo (sem precisar clicar)

---

## US06 — Comparar CPM com Meta Ads
**Como** operador solo,
**quero** ver o CPM estimado da collab lado a lado com o CPM medio de Meta Ads
**para** ter um argumento matador de venda na hora de falar com o cliente.

**Criterios de aceitacao:**
- [ ] Card de CPM mostra: "CPM PubliPrice: R$0,15" vs "CPM Meta Ads: R$18,00"
- [ ] Destaque visual: "98% mais barato que anuncios"
- [ ] Calculo visivel: alcance_estimado / 1000 * cpm
- [ ] Valores referenciais de Meta Ads sao configuraveis (default: R$18,00)

---

## US07 — Aplicar desconto manual
**Como** operador solo,
**quero** aplicar um desconto percentual ou valor fixo e ver o preco final atualizado
**para** ter flexibilidade em negociacao sem perder o tracking do desconto dado.

**Criterios de aceitacao:**
- [ ] Campo desconto aceita % ou R$
- [ ] Toggle % / R$ muda comportamento
- [ ] Preco original fica visivel (tachado) ao lado do preco com desconto
- [ ] Campo "Motivo do desconto" (opcional) — ex: "Primeira collab", "Fechamento trimestral"

---

## US08 — Salvar cotacao com dados do cliente
**Como** operador solo,
**quero** preencher nome, hotel, cidade e segmento do cliente e salvar a cotacao
**para** manter um historico organizado de todas as propostas geradas.

**Criterios de aceitacao:**
- [ ] Formulario do cliente: nome, hotel, cidade, segmento
- [ ] Campos minimos obrigatorios: nome e hotel
- [ ] Ao salvar, cotacao aparece no Historico com status "Gerada"
- [ ] Confirmacao visual (toast verde) apos salvamento

---

## US09 — Visualizar historico de cotacoes
**Como** operador solo,
**quero** ver uma tabela com todas as cotacoes passadas: data, cliente, perfil, pacote, valor
**para** consultar precos anteriores antes de uma nova negociacao com o mesmo cliente.

**Criterios de aceitacao:**
- [ ] Tabela com colunas: Data, Cliente, Hotel, Perfil, Pacote, Valor, Status
- [ ] Ordenavel por data (default: mais recente primeiro)
- [ ] Filtro por status: Todas / Geradas / Enviadas / Fechadas / Perdidas
- [ ] Campo de busca por nome do cliente ou hotel

---

## US10 — Alterar status de uma cotacao
**Como** operador solo,
**quero** mudar o status de uma cotacao entre "Gerada", "Enviada", "Fechada", "Perdida"
**para** acompanhar o pipeline comercial visualmente.

**Criterios de aceitacao:**
- [ ] Dropdown de status inline na tabela do Historico
- [ ] Opcoes: Gerada / Enviada / Fechada / Perdida
- [ ] Status muda cor do badge (cinza/azul/verde/vermelho)
- [ ] Ao marcar "Fechada", opcao de registrar "Valor fechado" (diferente do calculado)

---

## US11 — Exportar proposta em texto
**Como** operador solo,
**quero** clicar em "Exportar" e receber um texto formatado pronto pra colar no WhatsApp, e-mail ou DM
**para** enviar a proposta profissional em segundos, sem editar nada.

**Criterios de aceitacao:**
- [ ] Botao "Exportar Proposta" visivel no resultado do calculo
- [ ] Texto gerado inclui: nome do hotel/cliente, perfil sugerido, composicao do pacote, preco calculado, comparativo CPM, validade (7 dias)
- [ ] Botao "Copiar" copia para clipboard com feedback visual
- [ ] Formato markdown simples com bold e bullets

---

## US12 — Editar uma cotacao existente
**Como** operador solo,
**quero** reabrir uma cotacao do historico e ajustar perfil, pacote ou desconto
**para** renegociar sem precisar criar do zero.

**Criterios de aceitacao:**
- [ ] Botao "Reabrir" na linha da cotacao
- [ ] Carrega todos os dados originais no formulario de calculo
- [ ] Ao salvar, atualiza a cotacao existente (nao duplica)
- [ ] Campo "Versao" incrementa (v1, v2...)

---

## US13 — Ver resumo financeiro rapido
**Como** operador solo,
**quero** ver no topo do Historico: total de cotacoes, valor total cotado, taxa de fechamento
**para** ter nocao do pipeline sem abrir planilha.

**Criterios de aceitacao:**
- [ ] 3 KPI cards no topo da tela Historico: Total Cotado, Fechadas, Taxa de Conversao
- [ ] Atualiza em tempo real ao mudar status de qualquer cotacao
- [ ] Valor total formatado em reais (R$ XX.XXX)

---

## US14 — Alternar entre perfis rapidamente
**Como** operador solo (TDAH),
**quero** alternar entre as 3 views (Calculadora, Historico, Perfis) com um clique em tabs fixas no topo
**para** nao me perder navegando.

**Criterios de aceitacao:**
- [ ] 3 tabs fixas no topo: 🧮 Calculadora | 📋 Historico | 👥 Perfis
- [ ] Tab ativa destacada com cor
- [ ] Atalho de teclado: Ctrl+1 Calculadora, Ctrl+2 Historico, Ctrl+3 Perfis
- [ ] Estado da view preservado ao alternar

---

## US15 — Template de nicho automatico
**Como** operador solo,
**quero** que ao selecionar um perfil de gastronomia, o sistema ajuste automaticamente o fator nicho
**para** que o preco seja competitivo sem eu ter que pensar nisso.

**Criterios de aceitacao:**
- [ ] Ao selecionar perfil, fator_nicho e aplicado automaticamente:
  - Turismo: 1.0
  - Gastronomia: 0.9
  - Familia: 1.1
  - Lifestyle: 1.2
- [ ] Fator visivel no breakdown do calculo
- [ ] Tooltip explica o fator quando passar o mouse

---

## US16 — Ver proposta antes de enviar
**Como** operador solo,
**quero** ver uma pre-visualizacao exata da proposta antes de copiar ou enviar
**para** revisar tom, dados e valores sem surpresas.

**Criterios de aceitacao:**
- [ ] Modal de preview mostra o texto exato que sera copiado
- [ ] Formatacao markdown renderizada visualmente (bold, bullets, separadores)
- [ ] Botao "Editar" permite ajustar texto final manualmente
- [ ] Botao "Copiar e Fechar" executa acao em 1 clique

---

## US17 — Filtrar historico por perfil
**Como** operador solo,
**quero** filtrar o historico de cotacoes por perfil especifico
**para** analisar qual perfil gera mais propostas e fechamentos.

**Criterios de aceitacao:**
- [ ] Dropdown "Perfil" no topo da tabela de Historico
- [ ] Ao selecionar @lucastigrereal, mostra apenas cotacoes desse perfil
- [ ] KPIs de resumo atualizam conforme o filtro

---

## US18 — Busca rapida de cliente
**Como** operador solo,
**quero** digitar o nome do hotel e ver se ja existe cotacao anterior para ele
**para** precificar o retorno com inteligencia, nao no escuro.

**Criterios de aceitacao:**
- [ ] Campo de busca no Historico com autocomplete por nome de cliente/hotel
- [ ] Ao selecionar, mostra todas as cotacoes daquele cliente
- [ ] Indicador visual de "Cliente Recorrente" quando > 1 cotacao

---

## Resumo — Cobertura por Tela

| Tela | User Stories |
|---|---|
| **Calculadora** | US05, US06, US07, US08, US15 |
| **Historico** | US09, US10, US12, US13, US17, US18 |
| **Perfis** | US01, US02, US03, US04 |
| **Exportacao** | US11, US16 |
| **Navegacao** | US14 |

Total: **18 user stories** cobrindo o MVP completo.
