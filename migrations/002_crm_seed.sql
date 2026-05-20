-- =============================================================================
-- SEED: 002_crm_seed.sql
-- FASE 14 M4 — CRM Demo Data
-- NÃO aplicar automaticamente — apenas manual com autorização do operador
-- Usa ON CONFLICT DO NOTHING para ser idempotente
-- =============================================================================

-- =============================================================================
-- DEMO LEADS (3 leads de exemplo — hotel, restaurante, agência)
-- =============================================================================
INSERT INTO crm_leads (id, name, company, phone, email, source, contact_channel, instagram_handle,
    status, current_stage, segment, interest, bant_score, bant_tier,
    hotel_niche, hotel_tier, city, state, region, fit_score, priority_tier, tags)
VALUES
(
    'a1000000-0000-0000-0000-000000000001',
    'Maria Silva', 'Hotel Serra Azul', '(11) 9****-****', 'maria@serraazul.com.br',
    'instagram', 'instagram_dm', '@hotelserraazul',
    'novo', 'novo', 'hotel', 'publi',
    72, 'qualified', 'resort', 'Growth', 'Campos do Jordao', 'SP', 'sudeste',
    78, 'hot', ARRAY['vip', 'resort', 'sp']
),
(
    'a1000000-0000-0000-0000-000000000002',
    'João Santos', 'Restaurante Sabor Nordestino', '(84) 9****-****', NULL,
    'indicacao', 'whatsapp', '@sabornordestino',
    'novo', 'novo', 'restaurante', 'collab',
    55, 'nurture', NULL, 'Starter', 'Natal', 'RN', 'nordeste',
    45, 'warm', ARRAY['gastronomia', 'natal']
),
(
    'a1000000-0000-0000-0000-000000000003',
    'Ana Costa', 'Agência Viaje Mais', '(21) 9****-****', 'ana@viajemais.com.br',
    'prospeccao', 'email', '@viajemais',
    'qualificado', 'qualificado', 'agencia', 'pacote',
    85, 'qualified', NULL, 'Premium', 'Rio de Janeiro', 'RJ', 'sudeste',
    92, 'hot', ARRAY['agencia', 'pacote', 'premium', 'rj']
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- DEMO DEALS (1 deal por lead)
-- =============================================================================
INSERT INTO crm_deals (id, lead_id, title, product, value, status, stage,
    probability, owner, package_rationale, sync_bant_score, sync_bant_tier, sync_priority_tier, sync_fit_score)
VALUES
(
    'b1000000-0000-0000-0000-000000000001',
    'a1000000-0000-0000-0000-000000000001',
    'Collab Resort Serra Azul — Pacote Growth',
    'Growth', 990.00, 'proposta', 'proposta',
    0.40, 'lucas',
    ARRAY['Resort em Campos do Jordao', 'Alta taxa de engajamento', 'Perfil familia'],
    72, 'qualified', 'hot', 78
),
(
    'b1000000-0000-0000-0000-000000000002',
    'a1000000-0000-0000-0000-000000000002',
    'Collab Restaurante Sabor Nordestino — Starter',
    'Starter', 350.00, 'qualificado', 'qualificado',
    0.25, 'lucas',
    ARRAY['Gastronomia em Natal', 'Primeiro contato via indicacao', 'Potencial de upsell'],
    55, 'nurture', 'warm', 45
),
(
    'b1000000-0000-0000-0000-000000000003',
    'a1000000-0000-0000-0000-000000000003',
    'Pacote Premium — Agência Viaje Mais',
    'Premium', 1200.00, 'negociacao', 'negociacao',
    0.60, 'lucas',
    ARRAY['Agencia com portfolio', 'Pacote completo 4 collabs + 3 stories', 'Alto fit score 92'],
    85, 'qualified', 'hot', 92
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- DEMO FOLLOWUPS (1-2 followups por lead)
-- =============================================================================
INSERT INTO crm_followups (id, lead_id, deal_id, sequence_id, step_number, step_label,
    cadence, delay_days, scheduled_for, channel, message_template, status)
VALUES
(
    'c1000000-0000-0000-0000-000000000001',
    'a1000000-0000-0000-0000-000000000001',
    'b1000000-0000-0000-0000-000000000001',
    'seq-serra-azul', 1, 'D+1 — Primeiro follow-up',
    'sales', 1, CURRENT_DATE + 1, 'whatsapp',
    'Ola Maria! Como ficou a analise da nossa proposta Growth? Fique a vontade para tirar duvidas!',
    'scheduled'
),
(
    'c1000000-0000-0000-0000-000000000002',
    'a1000000-0000-0000-0000-000000000002',
    'b1000000-0000-0000-0000-000000000002',
    'seq-sabor-nordestino', 1, 'D+1 — Primeiro follow-up',
    'sales', 1, CURRENT_DATE + 1, 'whatsapp',
    'Ola Joao! Pensei no seu restaurante e montei uma proposta Starter. Posso te enviar?',
    'scheduled'
),
(
    'c1000000-0000-0000-0000-000000000003',
    'a1000000-0000-0000-0000-000000000003',
    'b1000000-0000-0000-0000-000000000003',
    'seq-viaje-mais', 2, 'D+3 — Reforco',
    'sales', 3, CURRENT_DATE + 3, 'email',
    'Ana, reforcando a proposta Premium que enviamos. Os slots de calendario estao preenchendo rapido!',
    'scheduled'
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- DEMO OBJECTIONS (1 objeção no deal em negociação)
-- =============================================================================
INSERT INTO crm_objections (id, lead_id, deal_id, objection_type, category,
    raw_text, response_used, response_source, outcome)
VALUES
(
    'd1000000-0000-0000-0000-000000000001',
    'a1000000-0000-0000-0000-000000000003',
    'b1000000-0000-0000-0000-000000000003',
    'preco', 'price',
    'Achei o valor um pouco acima do nosso orcamento de marketing',
    'Entendo Ana! O Premium entrega 4 collabs + SEOgram + 3 stories em 3+ perfis. Nosso CPM medio e R$0,15 — 98%% mais barato que Meta Ads. O ROI medio dos nossos clientes e 5x em alcance organico.',
    'standard', 'pending'
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- DEMO COMMISSIONS (1 comissão por deal fechado simulado)
-- =============================================================================
INSERT INTO crm_commissions (id, deal_id, role, tier, base_value, base_rate,
    base_commission, bonus_rate, bonus_commission, threshold, cap_applied, cap_value,
    commission_value, payment_status, explanation)
VALUES
(
    'e1000000-0000-0000-0000-000000000001',
    'b1000000-0000-0000-0000-000000000001',
    'operador', 'Growth',
    990.00, 0.20, 198.00,
    0.00, 0.00, 2000.00, FALSE, 0.00,
    198.00, 'pending',
    'Comissao base 20%% sobre Growth R$990 = R$198,00. Bonus nao atingido (threshold R$2000). Sem cap.'
),
(
    'e1000000-0000-0000-0000-000000000002',
    'b1000000-0000-0000-0000-000000000003',
    'operador', 'Premium',
    1200.00, 0.25, 300.00,
    0.00, 0.00, 3000.00, FALSE, 0.00,
    300.00, 'pending',
    'Comissao base 25%% sobre Premium R$1200 = R$300,00. Bonus nao atingido (threshold R$3000). Cap R$800 nao aplicado.'
)
ON CONFLICT (id) DO NOTHING;

-- SEED COMPLETE
-- 3 leads | 3 deals | 3 followups | 1 objection | 2 commissions
