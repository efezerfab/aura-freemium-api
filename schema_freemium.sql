CREATE TABLE IF NOT EXISTS freemium_leads (
    id              SERIAL PRIMARY KEY,
    email           TEXT NOT NULL,
    full_name       TEXT,
    current_job_title    TEXT,
    location        TEXT,
    career_goal     TEXT,
    salary_expectation TEXT,
    tiktok_lead_id  TEXT UNIQUE,
    tiktok_form_id  TEXT,
    tiktok_ad_id    TEXT,
    tiktok_campaign_id TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    report_sent_at  TIMESTAMPTZ,
    upsell_sent_at  TIMESTAMPTZ,
    raw_payload     JSONB
);

CREATE INDEX IF NOT EXISTS idx_freemium_email      ON freemium_leads (email);
CREATE INDEX IF NOT EXISTS idx_freemium_status     ON freemium_leads (status);
CREATE INDEX IF NOT EXISTS idx_freemium_created_at ON freemium_leads (created_at);
CREATE INDEX IF NOT EXISTS idx_freemium_lead_id    ON freemium_leads (tiktok_lead_id);
