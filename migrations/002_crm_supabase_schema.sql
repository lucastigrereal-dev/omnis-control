-- =============================================================================
-- MIGRATION: 002_crm_supabase_schema.sql
-- FASE 14 M4 — CRM Supabase Tables
-- Target: Supabase PostgreSQL 15 (sa-east-1, project qrcgedbuppodfbfqzocj)
-- Idempotente: CREATE IF NOT EXISTS — sem DROP, sem dados destrutivos
-- Dry-run safe: não dispara ações externas, não requer conexão real
-- =============================================================================

-- =============================================================================
-- EXTENSIONS (Supabase defaults + uuid generation)
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- TABLE 1: crm_leads
-- Origem: src/sales/leads.py + src/commercial/hotel_lead.py + src/sales_crm/models.py
-- =============================================================================
CREATE TABLE IF NOT EXISTS crm_leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id     TEXT UNIQUE,
    name            TEXT NOT NULL,
    company         TEXT,
    phone           TEXT,
    email           TEXT,
    source          TEXT NOT NULL DEFAULT 'manual',
    contact_channel TEXT,
    instagram_handle TEXT,
    status          TEXT NOT NULL DEFAULT 'novo',
    current_stage   TEXT NOT NULL DEFAULT 'novo',
    segment         TEXT,
    interest        TEXT,
    bant_score          INTEGER DEFAULT 0,
    bant_tier           TEXT,
    bant_budget_score   INTEGER DEFAULT 0,
    bant_authority_score INTEGER DEFAULT 0,
    bant_need_score     INTEGER DEFAULT 0,
    bant_timing_score   INTEGER DEFAULT 0,
    hotel_niche     TEXT,
    hotel_tier      TEXT,
    city            TEXT,
    state           TEXT,
    region          TEXT,
    fit_score       INTEGER DEFAULT 0,
    priority_tier   TEXT DEFAULT 'warm',
    score           INTEGER DEFAULT 0,
    tags            TEXT[] DEFAULT '{}',
    notes           TEXT,
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_leads_status CHECK (
        status IN ('novo', 'qualificado', 'em_negociacao', 'convertido', 'perdido')
    ),
    CONSTRAINT chk_leads_source CHECK (
        source IN ('instagram', 'indicacao', 'site', 'evento', 'prospeccao', 'manual', 'whatsapp', 'email', 'instagram_dm', 'parceria', 'outro')
    ),
    CONSTRAINT chk_leads_priority CHECK (
        priority_tier IN ('hot', 'warm', 'cold', 'disqualified')
    ),
    CONSTRAINT chk_leads_bant_tier CHECK (
        bant_tier IS NULL OR bant_tier IN ('qualified', 'nurture', 'low_fit', 'disqualified', 'missing_information')
    )
);

-- Indexes: crm_leads
CREATE INDEX IF NOT EXISTS idx_leads_status ON crm_leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_source ON crm_leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_priority ON crm_leads(priority_tier);
CREATE INDEX IF NOT EXISTS idx_leads_bant_tier ON crm_leads(bant_tier);
CREATE INDEX IF NOT EXISTS idx_leads_company ON crm_leads(company);
CREATE INDEX IF NOT EXISTS idx_leads_city ON crm_leads(city);
CREATE INDEX IF NOT EXISTS idx_leads_state ON crm_leads(state);
CREATE INDEX IF NOT EXISTS idx_leads_segment ON crm_leads(segment);
CREATE INDEX IF NOT EXISTS idx_leads_current_stage ON crm_leads(current_stage);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON crm_leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_tags ON crm_leads USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_leads_metadata ON crm_leads USING GIN(metadata_json);

-- =============================================================================
-- TABLE 2: crm_deals
-- Origem: src/sales/deals.py + src/sales/pipeline.py + src/commercial/pipeline_sync.py
-- =============================================================================
CREATE TABLE IF NOT EXISTS crm_deals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
    title           TEXT,
    product         TEXT NOT NULL DEFAULT 'Growth',
    value           DECIMAL(10,2) NOT NULL DEFAULT 0,
    currency        TEXT NOT NULL DEFAULT 'BRL',
    status          TEXT NOT NULL DEFAULT 'novo',
    stage           TEXT NOT NULL DEFAULT 'novo',
    probability     DECIMAL(3,2) DEFAULT 0.10,
    expected_close_date DATE,
    sold_at         TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    payment_method  TEXT,
    lost_reason     TEXT,
    owner           TEXT,
    sync_bant_score     INTEGER,
    sync_bant_tier      TEXT,
    sync_priority_tier  TEXT,
    sync_fit_score      INTEGER,
    package_rationale   TEXT[] DEFAULT '{}',
    recommended_channels TEXT[] DEFAULT '{}',
    transition_log  JSONB DEFAULT '[]',
    notes           TEXT,
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_deals_status CHECK (
        status IN ('novo', 'qualificado', 'proposta', 'negociacao', 'fechado', 'perdido', 'arquivado')
    ),
    CONSTRAINT chk_deals_product CHECK (
        product IN ('Starter', 'Growth', 'Premium')
    ),
    CONSTRAINT chk_deals_currency CHECK (
        currency IN ('BRL', 'USD', 'EUR')
    ),
    CONSTRAINT chk_deals_probability CHECK (
        probability >= 0 AND probability <= 1
    ),
    CONSTRAINT chk_deals_value CHECK (
        value >= 0
    )
);

-- Indexes: crm_deals
CREATE INDEX IF NOT EXISTS idx_deals_lead_id ON crm_deals(lead_id);
CREATE INDEX IF NOT EXISTS idx_deals_status ON crm_deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON crm_deals(stage);
CREATE INDEX IF NOT EXISTS idx_deals_product ON crm_deals(product);
CREATE INDEX IF NOT EXISTS idx_deals_owner ON crm_deals(owner);
CREATE INDEX IF NOT EXISTS idx_deals_expected_close ON crm_deals(expected_close_date);
CREATE INDEX IF NOT EXISTS idx_deals_sold_at ON crm_deals(sold_at DESC);
CREATE INDEX IF NOT EXISTS idx_deals_value ON crm_deals(value DESC);
CREATE INDEX IF NOT EXISTS idx_deals_created_at ON crm_deals(created_at DESC);

-- =============================================================================
-- TABLE 3: crm_followups
-- Origem: src/sales/followups.py + src/commercial/followup_schedule.py + src/commercial/outreach_sequence.py
-- =============================================================================
CREATE TABLE IF NOT EXISTS crm_followups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
    deal_id         UUID REFERENCES crm_deals(id) ON DELETE SET NULL,
    sequence_id     TEXT,
    step_number     INTEGER DEFAULT 1,
    step_label      TEXT,
    cadence         TEXT NOT NULL DEFAULT 'sales',
    delay_days      INTEGER DEFAULT 0,
    scheduled_for   DATE NOT NULL,
    due_date        DATE,
    channel         TEXT NOT NULL DEFAULT 'whatsapp',
    action_type     TEXT,
    message_template TEXT,
    call_to_action  TEXT,
    status          TEXT NOT NULL DEFAULT 'scheduled',
    urgency         TEXT,
    sent_at         TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    notes           TEXT,
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_followups_status CHECK (
        status IN ('scheduled', 'due', 'completed', 'skipped', 'cancelled', 'pending', 'in_progress', 'ready')
    ),
    CONSTRAINT chk_followups_channel CHECK (
        channel IN ('whatsapp', 'email', 'ligacao', 'instagram_dm', 'telegram', 'manual', 'note')
    ),
    CONSTRAINT chk_followups_cadence CHECK (
        cadence IN ('sales', 'outreach', 'custom')
    )
);

-- Indexes: crm_followups
CREATE INDEX IF NOT EXISTS idx_followups_lead_id ON crm_followups(lead_id);
CREATE INDEX IF NOT EXISTS idx_followups_deal_id ON crm_followups(deal_id);
CREATE INDEX IF NOT EXISTS idx_followups_status ON crm_followups(status);
CREATE INDEX IF NOT EXISTS idx_followups_scheduled_for ON crm_followups(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_followups_due_date ON crm_followups(due_date);
CREATE INDEX IF NOT EXISTS idx_followups_urgency ON crm_followups(urgency);
CREATE INDEX IF NOT EXISTS idx_followups_channel ON crm_followups(channel);
CREATE INDEX IF NOT EXISTS idx_followups_sequence ON crm_followups(sequence_id);
CREATE INDEX IF NOT EXISTS idx_followups_created_at ON crm_followups(created_at DESC);

-- =============================================================================
-- TABLE 4: crm_objections
-- Origem: src/sales_crm/models.py + src/commercial/proposal_brief.py
-- =============================================================================
CREATE TABLE IF NOT EXISTS crm_objections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id         UUID NOT NULL REFERENCES crm_leads(id) ON DELETE RESTRICT,
    deal_id         UUID REFERENCES crm_deals(id) ON DELETE SET NULL,
    objection_type  TEXT NOT NULL,
    category        TEXT,
    raw_text        TEXT,
    response_used   TEXT,
    response_source TEXT DEFAULT 'standard',
    outcome         TEXT,
    resolved        BOOLEAN DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_objections_type CHECK (
        objection_type IN ('preco', 'timing', 'concorrencia', 'necessidade', 'autoridade', 'confianca', 'orcamento', 'resultado', 'urgencia', 'outro')
    ),
    CONSTRAINT chk_objections_outcome CHECK (
        outcome IS NULL OR outcome IN ('resolved', 'unresolved', 'pending')
    )
);

-- Indexes: crm_objections
CREATE INDEX IF NOT EXISTS idx_objections_lead_id ON crm_objections(lead_id);
CREATE INDEX IF NOT EXISTS idx_objections_deal_id ON crm_objections(deal_id);
CREATE INDEX IF NOT EXISTS idx_objections_type ON crm_objections(objection_type);
CREATE INDEX IF NOT EXISTS idx_objections_outcome ON crm_objections(outcome);
CREATE INDEX IF NOT EXISTS idx_objections_resolved ON crm_objections(resolved);
CREATE INDEX IF NOT EXISTS idx_objections_created_at ON crm_objections(created_at DESC);

-- =============================================================================
-- TABLE 5: crm_commissions
-- Origem: src/sales/commissions.py (CommissionRule + CommissionResult + CommissionCalculator)
-- =============================================================================
CREATE TABLE IF NOT EXISTS crm_commissions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id         UUID NOT NULL REFERENCES crm_deals(id) ON DELETE RESTRICT,
    role            TEXT NOT NULL DEFAULT 'operador',
    tier            TEXT NOT NULL,
    base_value      DECIMAL(10,2) NOT NULL,
    base_rate       DECIMAL(3,2) NOT NULL,
    base_commission DECIMAL(10,2) NOT NULL,
    bonus_rate      DECIMAL(3,2) DEFAULT 0,
    bonus_commission DECIMAL(10,2) DEFAULT 0,
    threshold       DECIMAL(10,2) DEFAULT 0,
    cap_applied     BOOLEAN DEFAULT FALSE,
    cap_value       DECIMAL(10,2) DEFAULT 0,
    commission_value DECIMAL(10,2) NOT NULL,
    percentage      DECIMAL(3,2),
    expected_payment_date DATE,
    payment_status  TEXT NOT NULL DEFAULT 'pending',
    explanation     TEXT,
    metadata_json   JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_commissions_tier CHECK (
        tier IN ('Starter', 'Growth', 'Premium')
    ),
    CONSTRAINT chk_commissions_role CHECK (
        role IN ('operador', 'closer', 'sdr', 'parceiro')
    ),
    CONSTRAINT chk_commissions_payment CHECK (
        payment_status IN ('pending', 'paid', 'cancelled')
    ),
    CONSTRAINT chk_commissions_value CHECK (
        commission_value >= 0
    )
);

-- Indexes: crm_commissions
CREATE INDEX IF NOT EXISTS idx_commissions_deal_id ON crm_commissions(deal_id);
CREATE INDEX IF NOT EXISTS idx_commissions_tier ON crm_commissions(tier);
CREATE INDEX IF NOT EXISTS idx_commissions_role ON crm_commissions(role);
CREATE INDEX IF NOT EXISTS idx_commissions_payment ON crm_commissions(payment_status);
CREATE INDEX IF NOT EXISTS idx_commissions_expected_payment ON crm_commissions(expected_payment_date);
CREATE INDEX IF NOT EXISTS idx_commissions_created_at ON crm_commissions(created_at DESC);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Pipeline summary: agrega deals por status
CREATE OR REPLACE VIEW vw_pipeline_summary AS
SELECT
    d.status,
    COUNT(*) AS deal_count,
    COALESCE(SUM(d.value), 0) AS total_value,
    COALESCE(SUM(d.value * d.probability), 0) AS weighted_value,
    AVG(d.value) AS avg_deal_value
FROM crm_deals d
GROUP BY d.status;

-- Leads qualificados: visão consolidada lead + deals + followups pendentes
CREATE OR REPLACE VIEW vw_leads_qualificados AS
SELECT
    l.id,
    l.name,
    l.company,
    l.source,
    l.bant_score,
    l.bant_tier,
    l.priority_tier,
    l.status,
    l.current_stage,
    COUNT(DISTINCT d.id) AS total_deals,
    COUNT(DISTINCT f.id) FILTER (
        WHERE f.status IN ('scheduled', 'due', 'pending', 'in_progress', 'ready')
    ) AS pending_followups,
    l.created_at
FROM crm_leads l
LEFT JOIN crm_deals d ON d.lead_id = l.id
LEFT JOIN crm_followups f ON f.lead_id = l.id
WHERE l.status <> 'perdido'
GROUP BY l.id;

-- Comissões mensais: agregação por mês/role/tier
CREATE OR REPLACE VIEW vw_comissoes_mensal AS
SELECT
    DATE_TRUNC('month', c.created_at) AS mes,
    c.role,
    c.tier,
    COUNT(*) AS total_deals,
    COALESCE(SUM(c.commission_value), 0) AS total_commissions,
    COALESCE(SUM(c.base_value), 0) AS total_base_value
FROM crm_commissions c
GROUP BY DATE_TRUNC('month', c.created_at), c.role, c.tier;

-- =============================================================================
-- TRIGGER: auto-update updated_at
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_leads_updated_at') THEN
        CREATE TRIGGER trg_leads_updated_at
            BEFORE UPDATE ON crm_leads
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_deals_updated_at') THEN
        CREATE TRIGGER trg_deals_updated_at
            BEFORE UPDATE ON crm_deals
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_followups_updated_at') THEN
        CREATE TRIGGER trg_followups_updated_at
            BEFORE UPDATE ON crm_followups
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_objections_updated_at') THEN
        CREATE TRIGGER trg_objections_updated_at
            BEFORE UPDATE ON crm_objections
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_commissions_updated_at') THEN
        CREATE TRIGGER trg_commissions_updated_at
            BEFORE UPDATE ON crm_commissions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END;
$$;

-- =============================================================================
-- RLS POLICIES — DOCUMENTED, NOT ACTIVATED
-- Uncomment below when operator authorizes Supabase real connection:
--
-- ALTER TABLE crm_leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE crm_deals ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE crm_followups ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE crm_objections ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE crm_commissions ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY "Operador acesso total" ON crm_leads
--     FOR ALL TO authenticated
--     USING (auth.uid() IN (SELECT id FROM operator_users WHERE role = 'operador'));
-- =============================================================================

-- MIGRATION COMPLETE
-- Tables: 5 | Indexes: 38 | Views: 3 | Triggers: 5 | CHECKs: 15
-- Next: Run 002_crm_seed.sql for demo data (optional, manual only)
