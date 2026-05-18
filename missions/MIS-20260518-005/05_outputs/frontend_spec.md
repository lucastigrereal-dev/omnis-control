# Frontend Specification — PubliPrice v1.0

**Versao:** 1.0 | **Data:** 2026-05-18
**Tecnologia:** HTML5 + Vanilla JavaScript (ES6+) + CSS3 Custom Properties
**Build:** Zero dependencias externas (sem npm, sem webpack). Single HTML file + CSS + JS.

---

## 1. ARQUITETURA GERAL

```
index.html  (unico arquivo — ~400 linhas)
├── <style>   CSS completo (~300 linhas)
├── <main>    3 views com tabs
│   ├── View 1: Calculadora (#view-calculadora)
│   ├── View 2: Historico    (#view-historico)
│   └── View 3: Perfis       (#view-perfis)
└── <script>  JS vanilla (~500 linhas)
    ├── State Manager (objeto global + Proxy)
    ├── API Client (fetch wrapper)
    ├── Calculator Engine
    ├── View Renderers
    └── Event Handlers
```

---

## 2. COMPONENT TREE

```
<App>
├── <Navbar>                  // Topo fixo — logo + 3 tabs + atalhos teclado
│   ├── <Logo>                // "PubliPrice" + icone calculadora
│   ├── <TabGroup>            // 3 botoes: Calculadora | Historico | Perfis
│   └── <KeyboardHint>        // "Ctrl+1/2/3" subtle
│
├── <ViewCalculator>          // VIEW 1 — visivel por default
│   ├── <FormCotacao>         // Formulario principal
│   │   ├── <SelectPerfil>    // Dropdown dos 6 perfis
│   │   ├── <SelectPacote>    // Dropdown dos 3 pacotes
│   │   ├── <InputVolume>     // Slider de meses (1-12)
│   │   ├── <InputDesconto>   // % ou R$
│   │   └── <CampoCliente>    // Nome, hotel, cidade (collapsible)
│   ├── <ResultCard>          // Card do resultado — aparece apos calculo
│   │   ├── <PrecoFinal>      // Valor grande centralizado
│   │   ├── <Breakdown>       // Accordion com fatores aplicados
│   │   ├── <CPMComparison>   // Barras comparativas
│   │   ├── <AlcanceEstimado> // Impressoes projetadas
│   │   └── <BtnExportar>     // Copiar proposta
│   └── <BtnSalvar>           // Salvar cotacao (fixo no rodape da view)
│
├── <ViewHistorico>           // VIEW 2
│   ├── <KPIBar>              // 3 cards metricos no topo
│   │   ├── <KpiTotal>        // "R$ XX.XXX total cotado"
│   │   ├── <KpiFechadas>     // "18 propostas fechadas"
│   │   └── <KpiTaxa>         // "38% taxa de fechamento"
│   ├── <FilterBar>           // Busca + filtros
│   │   ├── <SearchInput>     // Campo busca por nome/hotel
│   │   ├── <FilterStatus>    // Dropdown status
│   │   └── <FilterPerfil>    // Dropdown perfil
│   └── <CotacoesTable>       // Tabela de cotacoes
│       └── <CotacaoRow>      // Linha individual com acoes inline
│
├── <ViewPerfis>              // VIEW 3
│   ├── <PerfisGrid>          // Grid de cards (2 colunas desktop)
│   │   └── <PerfilCard>      // Card individual com metricas
│   ├── <PacotesSection>      // Secao inferior — tabela de pacotes
│   └── <BtnAdicionarPerfil>  // Novo perfil
│
├── <Modal>                   // Modal reutilizavel
│   ├── <ModalEditarPerfil>
│   ├── <ModalPreviewProposta>
│   └── <ModalConfirmacao>
│
└── <Toast>                   // Feedback temporario (canto inferior direito)
```

---

## 3. VIEW 1 — CALCULADORA

### Wireframe descritivo

```
┌──────────────────────────────────────────────────────────┐
│  [PUBLIPRICE]    🧮 Calc  📋 Historico  👥 Perfis        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─ Perfil ──────────────────────────────────┐         │
│   │ [@lucastigrereal (690K) ▾        ]         │         │
│   └────────────────────────────────────────────┘         │
│                                                          │
│   ┌─ Pacote ─────────────────────────────────┐          │
│   │ [Growth — R$ 990/mês ▾ ⭐Recomendado]     │          │
│   └────────────────────────────────────────────┘         │
│                                                          │
│   ┌─ Volume ──────────────────────────────────┐         │
│   │ Fechamento mensal?  [====○====] 3 meses   │         │
│   └────────────────────────────────────────────┘         │
│                                                          │
│   ┌─ Desconto (opcional) ──────────────────────┐        │
│   │ [ 10% ▾ ]  Motivo: [_______________]       │        │
│   └────────────────────────────────────────────┘         │
│                                                          │
│   ┌─ Cliente (opcional) ────────────────────────┐       │
│   │ Nome: [____________] Hotel: [____________]  │       │
│   └─────────────────────────────────────────────┘       │
│                                                          │
│   ════════════════════════════════════════════           │
│                                                          │
│   ┌─ RESULTADO ─────────────────────────────────┐       │
│   │                                              │       │
│   │        R$ 1.425,60                           │       │
│   │      Preco sugerido/mes                      │       │
│   │                                              │       │
│   │  ▸ Breakdown (clique para expandir)          │       │
│   │    • Base: R$ 990,00                         │       │
│   │    • x1.15 (690K seguidores)                 │       │
│   │    • x0.96 (3.2% engajamento)                │       │
│   │    • x1.20 (nicho lifestyle)                 │       │
│   │    • x0.85 (3 meses — desconto volume)       │       │
│   │                                              │       │
│   │  ┌─ CPM ────────────────────────────┐       │       │
│   │  │ PubliPrice: R$0,15  ████ (99%)   │       │       │
│   │  │ Meta Ads:   R$18,00 ████████████ │       │       │
│   │  └──────────────────────────────────┘       │       │
│   │                                              │       │
│   │  Alcance estimado: 555K pessoas              │       │
│   │  Impressoes: ~925K                           │       │
│   │                                              │       │
│   │  [📋 Copiar Proposta]                        │       │
│   └──────────────────────────────────────────────┘       │
│                                                          │
│              [ 💾 Salvar Cotacao ]                        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Funcionamento
- Calculo em tempo real — ao alterar qualquer campo, recalcula instantaneamente (sem botao "Calcular")
- Breakdown collapsible (accordion) — expande/colapsa ao clicar
- Barras CPM animadas proporcionalmente
- Botao "Copiar Proposta" abre modal de preview antes de copiar

---

## 4. VIEW 2 — HISTORICO

### Wireframe descritivo

```
┌──────────────────────────────────────────────────────────┐
│  [PUBLIPRICE]    🧮 Calc  📋 Historico  👥 Perfis        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────┐  ┌──────┐  ┌──────┐                            │
│  │Total │  │Fech  │  │Taxa  │                            │
│  │89.6K │  │  18  │  │ 38%  │                            │
│  └──────┘  └──────┘  └──────┘                            │
│                                                          │
│  🔍 [Buscar cliente/hotel...]  Status: [Todas ▾]  Perfil: [Todos ▾] │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │Data       Cliente        Perfil      Pacote    Valor ││
│  ├──────────────────────────────────────────────────────┤│
│  │18/05 14h  Maria Souza    @lucas     Growth    1.425 ││
│  │           Grand Hotel    690K       3 meses   ▾🟢   ││
│  ├──────────────────────────────────────────────────────┤│
│  │17/05 10h  Joao R.        @oinatal   Starter    280 ││
│  │           Pousada Sol    630K       1 mes     📋🔴  ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Funcionalidades
- Cada linha expande ao clicar (detalhes: breakdown, CPM, desconto)
- Badge de status colorido inline (🟢 fechada, 🔵 enviada, ⚪ gerada, 🔴 perdida)
- Dropdown inline no status: clica no badge e troca status
- Busca filtra em tempo real (client-side com debounce 300ms)
- KPIs atualizam dinamicamente ao filtrar

---

## 5. VIEW 3 — PERFIS

### Wireframe descritivo

```
┌──────────────────────────────────────────────────────────┐
│  [PUBLIPRICE]    🧮 Calc  📋 Historico  👥 Perfis        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────┐ ┌─────────────────────┐        │
│  │ 👤 @lucastigrereal   │ │ 👤 @oinatalrn        │        │
│  │ 690K • lifestyle     │ │ 630K • turismo       │        │
│  │ ER: 3.2%  Alc: 185K │ │ ER: 4.1%  Alc: 210K │        │
│  │ [Editar]             │ │ [Editar]             │        │
│  └─────────────────────┘ └─────────────────────┘        │
│                                                          │
│  ┌─────────────────────┐ ┌─────────────────────┐        │
│  │ 👤 @agenteviajabrasil│ │ 👤 @afamiliatigrereal│       │
│  │ 452K • turismo       │ │ 320K • familia       │        │
│  │ ER: 3.8%  Alc: 145K │ │ ER: 5.2%  Alc: 128K │        │
│  └─────────────────────┘ └─────────────────────┘        │
│                                                          │
│  ┌─────────────────────┐ ┌─────────────────────┐        │
│  │ 👤 @oquecomernatalrn │ │ 👤 @natalaivoueu     │        │
│  │ 249K • gastronomia   │ │ 240K • turismo       │        │
│  │ ER: 4.7%  Alc: 95K  │ │ ER: 3.5%  Alc: 88K  │        │
│  └─────────────────────┘ └─────────────────────┘        │
│                                                          │
│  ─── PACOTES ──────────────────────────────────         │
│  ┌──────────────────────────────────────────────┐       │
│  │ Pacote    Collabs Stories  Preco Base        │       │
│  ├──────────────────────────────────────────────┤       │
│  │ Starter    1       0       R$ 350            │       │
│  │ Growth⭐    3       0       R$ 990/mes        │       │
│  │ Premium    4       3       R$ 1.200          │       │
│  └──────────────────────────────────────────────┘       │
│                                                          │
│  [+ Adicionar Perfil]                                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 6. STATE MANAGEMENT

Objeto global `AppState` com Proxy reativo:

```javascript
const AppState = new Proxy({
  view: 'calculadora',           // 'calculadora' | 'historico' | 'perfis'
  perfis: [],                    // Cache de perfis do banco
  pacotes: [],                   // Cache de pacotes do banco
  cotacoes: [],                  // Lista de cotacoes carregadas
  filtro: {                      // Filtros ativos no Historico
    busca: '',
    status: 'todas',
    perfil_id: null
  },
  calculo: {                     // Estado atual da Calculadora
    perfil_id: null,
    pacote_id: null,
    volume_meses: 1,
    desconto_pct: 0,
    resultado: null              // null ate primeiro calculo
  },
  kpis: {                        // Metricas calculadas
    total_cotado: 0,
    fechadas: 0,
    taxa_fechamento: 0
  },
  loading: false,
  toast: null                    // { mensagem, tipo: 'sucesso'|'erro'|'info' }
}, handler);
```

Fluxo: `User Action → AppState update → re-render apenas do componente afetado`.

---

## 7. DESIGN SYSTEM — DARK THEME

### Paleta de Cores

| Token | Hex | Uso |
|---|---|---|
| `--bg-primary` | `#0A0E17` | Fundo principal (deep space) |
| `--bg-secondary` | `#111827` | Fundo de cards, tabelas |
| `--bg-tertiary` | `#1C2536` | Fundo de inputs, hover rows |
| `--text-primary` | `#F1F5F9` | Texto principal (slate 100) |
| `--text-secondary` | `#94A3B8` | Texto secundario, labels (slate 400) |
| `--text-muted` | `#64748B` | Texto terciario, hints (slate 500) |
| `--accent-primary` | `#38BDF8` | Sky 400 — botoes, links, tab ativa |
| `--accent-secondary` | `#818CF8` | Indigo 400 — hover, selecionado |
| `--success` | `#34D399` | Emerald 400 — status fechada, toast sucesso |
| `--warning` | `#FBBF24` | Amber 400 — status enviada, alertas |
| `--danger` | `#F87171` | Red 400 — status perdida, erros |
| `--border` | `#1E293B` | Bordas sutis (slate 800) |
| `--shadow` | `rgba(0,0,0,0.4)` | Sombras de cards |

### Tipografia

| Uso | Google Font | CSS Class | Tamanho |
|---|---|---|---|
| Titulos (h1, h2) | **Inter** (600) | `.font-heading` | 24px / 20px |
| Corpo, labels, botoes | **Inter** (400) | — | 15px / 14px |
| Dados, precos, numeros | **JetBrains Mono** (500) | `.font-mono` | 32px / 18px / 14px |
| Badges, tags, micro-texto | **Inter** (500) | `.font-caption` | 12px |

Fontes carregadas via Google Fonts (2 familias):
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap">
```

### Hierarquia Visual
- **R$ 1.425,60** — preco final: JetBrains Mono 32px, `--accent-primary`, bold
- **Breakdown** — itens: Inter 14px, `--text-secondary`, expandido com transicao
- **Cards de perfil** — bg `--bg-secondary`, border `--border`, 8px radius
- **Badges de status** — 4 cores (success/warning/slate/danger), pill shape

### Espacamento (8px grid)
- Section padding: 24px
- Card padding: 16px
- Input height: 40px
- Gap entre elementos: 12px / 16px
- Tabs: 44px height, gap 4px

---

## 8. COMPORTAMENTO RESPONSIVO

Desktop-first (1080p, 1440p, ultra-wide). Mobile breakpoint unico em 768px:

- Desktop: 2 colunas no grid de perfis, tabela completa no Historico
- Mobile (< 768px): Cards empilhados, tabela vira cards, tabs com scroll horizontal

---

## 9. DETALHES DE INTERACAO

### Micro-interacoes
- **Resultado aparece com fade-in + slide-up** (300ms ease-out)
- **Barra CPM anima width** de 0 ao valor real (500ms ease-out delay 100ms)
- **Copiar proposta**: texto pisca (highlight por 500ms) + toast "Copiado!"
- **Mudar status**: badge com scale pulse (keyframe 0.3s)
- **Salvar cotacao**: botao com spinner interno enquanto salva (max 1s)
- **Filtro busca**: debounce 300ms antes de filtrar (digitar rapido nao trava)

### Atalhos de Teclado
| Atalho | Acao |
|---|---|
| `Ctrl + 1` | View Calculadora |
| `Ctrl + 2` | View Historico |
| `Ctrl + 3` | View Perfis |
| `Ctrl + Enter` | Salvar cotacao |
| `Ctrl + C` (na preview) | Copiar proposta |
| `Esc` | Fechar modal |

### Loading States
- Skeleton cards (pulsing gray blocks) enquanto carrega perfis/pacotes
- Spinner no botao "Salvar" durante POST
- Tabela mostra "Nenhuma cotacao encontrada" com ilustracao simples (icone vazio)

---

## 10. REFERENCIAS VISUAIS

### Carrosseis virais de referencia (mercado hoteleiro)
| Perfil | Estilo |
|---|---|
| @santosreservas | Clean, dados + storytelling |
| @hoteisincriveis | Fotos impactantes + numeros gigantes |
| @seguetebrasil | Tom proximo + CTA forte |

### Diretrizes de composicao
- Texto nunca > 40% do slide
- Uma ideia por slide
- Numero grande = impacto (nao dilua com texto)
- Contraste alto: fundo escuro + texto claro = legibilidade
- Consistencia: mesma paleta, mesma fonte, mesma margem em todos os slides
