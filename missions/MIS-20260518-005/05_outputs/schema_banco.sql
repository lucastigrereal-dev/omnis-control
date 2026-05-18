-- ============================================================================
-- PubliPrice v1.0 — Schema SQLite (Local-First)
-- Data: 2026-05-18
-- SGBD: SQLite 3.45+
-- Encoding: UTF-8
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA encoding = 'UTF-8';

-- ============================================================================
-- TABELA: perfis
-- Armazena os perfis Instagram usados para collab.
-- Seed: 6 perfis reais do Lucas Tigre (maio/2026).
-- ============================================================================

CREATE TABLE IF NOT EXISTS perfis (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    handle          TEXT    NOT NULL UNIQUE,                -- @ do Instagram
    nome_exibicao   TEXT    NOT NULL,                       -- Nome amigavel
    seguidores      INTEGER NOT NULL CHECK (seguidores > 0),
    nicho           TEXT    NOT NULL CHECK (nicho IN (
                        'turismo', 'gastronomia', 'familia', 'lifestyle'
                    )),
    engagement_rate REAL    NOT NULL CHECK (engagement_rate >= 0 AND engagement_rate <= 100),
    alcance_medio   INTEGER NOT NULL CHECK (alcance_medio > 0),
    foto_url        TEXT,                                   -- URL local ou placeholder
    ativo           INTEGER NOT NULL DEFAULT 1,             -- 0 = desativado
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_perfis_nicho   ON perfis (nicho);
CREATE INDEX IF NOT EXISTS idx_perfis_ativo   ON perfis (ativo);

-- ============================================================================
-- TABELA: pacotes
-- Pacotes de venda pre-definidos.
-- Seed: 3 pacotes padrao (Starter, Growth, Premium).
-- ============================================================================

CREATE TABLE IF NOT EXISTS pacotes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL UNIQUE,                 -- Starter | Growth | Premium
    descricao       TEXT    NOT NULL,                        -- Descricao comercial
    collabs         INTEGER NOT NULL DEFAULT 0,             -- Qtde de collabs inclusas
    stories         INTEGER NOT NULL DEFAULT 0,             -- Qtde de stories inclusos
    reels           INTEGER NOT NULL DEFAULT 0,             -- Qtde de reels inclusos
    carrosseis      INTEGER NOT NULL DEFAULT 0,             -- Qtde de carrosseis inclusos
    perfis_minimos  INTEGER NOT NULL DEFAULT 1,             -- Qtde minima de perfis
    preco_base      REAL    NOT NULL CHECK (preco_base > 0), -- Preco base em R$
    seogram         INTEGER NOT NULL DEFAULT 0,             -- 1 = inclui SEOgram
    recomendado     INTEGER NOT NULL DEFAULT 0,             -- 1 = destaque "Recomendado"
    ativo           INTEGER NOT NULL DEFAULT 1,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_pacotes_ativo ON pacotes (ativo);

-- ============================================================================
-- TABELA: clientes
-- Dados dos clientes (hoteis, restaurantes).
-- ============================================================================

CREATE TABLE IF NOT EXISTS clientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,                        -- Nome do contato
    hotel           TEXT    NOT NULL,                        -- Nome do hotel/restaurante
    cidade          TEXT,                                    -- Cidade
    uf              TEXT    CHECK (length(uf) = 2),          -- Sigla estado
    segmento        TEXT    CHECK (segmento IN (
                        'hotel', 'pousada', 'resort', 'restaurante', 'outro'
                    )),
    telefone        TEXT,
    email           TEXT,
    instagram       TEXT,                                    -- @ do estabelecimento
    data_contato    TEXT    NOT NULL DEFAULT (date('now', 'localtime')),
    observacao      TEXT,
    ativo           INTEGER NOT NULL DEFAULT 1,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_clientes_cidade   ON clientes (cidade);
CREATE INDEX IF NOT EXISTS idx_clientes_segmento ON clientes (segmento);
CREATE INDEX IF NOT EXISTS idx_clientes_hotel    ON clientes (hotel);

-- ============================================================================
-- TABELA: cotacoes
-- Historico completo de cotacoes geradas.
-- Relaciona: perfil + pacote + cliente.
-- ============================================================================

CREATE TABLE IF NOT EXISTS cotacoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    perfil_id       INTEGER NOT NULL,
    pacote_id       INTEGER NOT NULL,
    cliente_id      INTEGER,
    -- Dados do calculo
    preco_calculado REAL    NOT NULL CHECK (preco_calculado > 0),
    desconto        REAL    NOT NULL DEFAULT 0,              -- Valor absoluto do desconto
    desconto_pct    REAL    NOT NULL DEFAULT 0,              -- Percentual de desconto aplicado
    motivo_desconto TEXT,                                    -- Ex: "Primeira collab"
    preco_final     REAL    NOT NULL CHECK (preco_final > 0),
    -- Fatores aplicados (transparencia)
    fator_seguidores REAL   NOT NULL DEFAULT 1.0,
    fator_engajamento REAL  NOT NULL DEFAULT 1.0,
    fator_nicho      REAL   NOT NULL DEFAULT 1.0,
    fator_volume     REAL   NOT NULL DEFAULT 1.0,
    volume_meses     INTEGER NOT NULL DEFAULT 1 CHECK (volume_meses >= 1),
    -- Metadados
    cpm_estimado    REAL    NOT NULL DEFAULT 0,
    cpm_meta_ads    REAL    NOT NULL DEFAULT 18.00,
    status          TEXT    NOT NULL DEFAULT 'gerada'
                           CHECK (status IN ('gerada', 'enviada', 'fechada', 'perdida')),
    versao          INTEGER NOT NULL DEFAULT 1,
    data_criacao    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    data_atualizacao TEXT   NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (perfil_id)  REFERENCES perfis(id)   ON DELETE RESTRICT,
    FOREIGN KEY (pacote_id)  REFERENCES pacotes(id)   ON DELETE RESTRICT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)  ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_cotacoes_status      ON cotacoes (status);
CREATE INDEX IF NOT EXISTS idx_cotacoes_data        ON cotacoes (data_criacao);
CREATE INDEX IF NOT EXISTS idx_cotacoes_perfil      ON cotacoes (perfil_id);
CREATE INDEX IF NOT EXISTS idx_cotacoes_cliente     ON cotacoes (cliente_id);

-- ============================================================================
-- TABELA: metricas_historicas
-- Registro mensal de metricas por perfil para analise de tendencia.
-- ============================================================================

CREATE TABLE IF NOT EXISTS metricas_historicas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    perfil_id       INTEGER NOT NULL,
    data_ref        TEXT    NOT NULL,                        -- YYYY-MM-DD (1o do mes)
    seguidores      INTEGER NOT NULL CHECK (seguidores > 0),
    alcance         INTEGER NOT NULL CHECK (alcance >= 0),
    engagement      REAL    NOT NULL CHECK (engagement >= 0 AND engagement <= 100),
    impressoes      INTEGER NOT NULL DEFAULT 0,
    cliques_link    INTEGER NOT NULL DEFAULT 0,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (perfil_id) REFERENCES perfis(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metricas_data   ON metricas_historicas (data_ref);
CREATE INDEX IF NOT EXISTS idx_metricas_perfil ON metricas_historicas (perfil_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_metricas_unico ON metricas_historicas (perfil_id, data_ref);

-- ============================================================================
-- SEED DATA — Perfis Reais (maio/2026)
-- ============================================================================

INSERT OR IGNORE INTO perfis (handle, nome_exibicao, seguidores, nicho, engagement_rate, alcance_medio) VALUES
('lucastigrereal',      'Lucas Tigre Real',     690000, 'lifestyle',    3.2, 185000),
('oinatalrn',           'O Inata RN',           630000, 'turismo',      4.1, 210000),
('agenteviajabrasil',   'Agente Viaja Brasil',  452000, 'turismo',      3.8, 145000),
('afamiliatigrereal',   'A Familia Tigre Real', 320000, 'familia',      5.2, 128000),
('oquecomernatalrn',    'O Que Comer Natal RN', 249000, 'gastronomia',  4.7,  95000),
('natalaivoueu',        'Natal Ai Vou Eu',      240000, 'turismo',      3.5,  88000);

-- ============================================================================
-- SEED DATA — Pacotes Padrao
-- ============================================================================

INSERT OR IGNORE INTO pacotes (nome, descricao, collabs, stories, reels, carrosseis, perfis_minimos, preco_base, seogram, recomendado) VALUES
('Starter',  '1 collab em 1 perfil. Entrada acessivel.',                                  1, 0, 0, 0, 1, 350.00,  0, 0),
('Growth',   '3 collabs + SEOgram em 3 perfis. MELHOR CUSTO-BENEFICIO. Recomendado.',     3, 0, 0, 0, 3, 990.00,  1, 1),
('Premium',  '4 collabs + 3 stories em 3+ perfis. Pacote completo para alta exposicao.',  4, 3, 0, 0, 3, 1200.00, 0, 0);

-- ============================================================================
-- VIEW: vw_resumo_mensal — Dashboard rapido (uso futuro)
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_resumo_mensal AS
SELECT
    strftime('%Y-%m', c.data_criacao) AS mes,
    COUNT(*)                          AS total_cotacoes,
    SUM(CASE WHEN c.status = 'fechada' THEN 1 ELSE 0 END) AS fechadas,
    SUM(CASE WHEN c.status = 'perdida' THEN 1 ELSE 0 END) AS perdidas,
    ROUND(SUM(c.preco_final), 2)      AS valor_total_cotado,
    ROUND(AVG(c.preco_final), 2)      AS ticket_medio
FROM cotacoes c
GROUP BY mes
ORDER BY mes DESC;

-- ============================================================================
-- VIEW: vw_perfil_performance — Performance por perfil (uso futuro)
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_perfil_performance AS
SELECT
    p.handle,
    p.nicho,
    COUNT(c.id)                              AS total_cotacoes,
    SUM(CASE WHEN c.status = 'fechada' THEN 1 ELSE 0 END) AS fechadas,
    ROUND(
        CAST(SUM(CASE WHEN c.status = 'fechada' THEN 1 ELSE 0 END) AS REAL) /
        NULLIF(COUNT(c.id), 0) * 100,
        1
    )                                        AS taxa_fechamento_pct,
    ROUND(COALESCE(SUM(c.preco_final), 0), 2) AS receita_total
FROM perfis p
LEFT JOIN cotacoes c ON c.perfil_id = p.id
WHERE p.ativo = 1
GROUP BY p.id
ORDER BY taxa_fechamento_pct DESC;

-- ============================================================================
-- TRIGGER: atualiza updated_at automaticamente
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS trg_perfis_updated
    AFTER UPDATE ON perfis
    FOR EACH ROW
BEGIN
    UPDATE perfis SET atualizado_em = datetime('now', 'localtime') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_cotacoes_updated
    AFTER UPDATE ON cotacoes
    FOR EACH ROW
BEGIN
    UPDATE cotacoes SET data_atualizacao = datetime('now', 'localtime') WHERE id = OLD.id;
END;

-- ============================================================================
-- VERIFICACAO RAPIDA
-- ============================================================================

-- SELECT 'Perfis cadastrados:' AS info, COUNT(*) AS qtd FROM perfis
-- UNION ALL
-- SELECT 'Pacotes cadastrados:', COUNT(*) FROM pacotes
-- UNION ALL
-- SELECT 'Total seguidores:', SUM(seguidores) FROM perfis WHERE ativo = 1;
