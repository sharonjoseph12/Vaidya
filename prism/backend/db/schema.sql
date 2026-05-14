-- PRISM Platform Database Schema
-- Supabase PostgreSQL (run in Supabase SQL Editor)

-- ============================================================
-- PATIENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    abha_id TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    encrypted_demographics BYTEA NOT NULL,
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    consent_timestamp TIMESTAMPTZ,
    consent_purpose TEXT,
    device_info JSONB
);

-- ============================================================
-- DIAGNOSTIC SESSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_type TEXT NOT NULL CHECK (session_type IN ('full','audio_only','visual_only','rppg_only')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','sensing','reasoning','projecting','optimizing','complete','error')),

    -- Layer 1: SENSE results
    sense_results JSONB,

    -- Layer 2: REASON results
    causal_results JSONB,

    -- Layer 3: PROJECT results
    twin_trajectory JSONB,

    -- Layer 4: ACT results
    intervention_plan JSONB,

    -- Final outputs
    disease_probabilities JSONB,
    primary_diagnosis TEXT,
    confidence_score FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
    uncertainty_bounds JSONB,
    model_version TEXT,
    processing_time_ms INT,

    -- Clinical validation
    doctor_validated BOOLEAN NOT NULL DEFAULT FALSE,
    doctor_id UUID,
    ground_truth_diagnosis TEXT,
    ground_truth_source TEXT
);

-- ============================================================
-- CLINICAL REPORTS
-- ============================================================
CREATE TABLE IF NOT EXISTS clinical_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    report_pdf_url TEXT,
    report_fhir_json JSONB,
    abdm_push_status TEXT NOT NULL DEFAULT 'not_requested' CHECK (abdm_push_status IN ('not_requested','pending','success','failed')),
    abdm_record_id TEXT,
    abdm_push_error TEXT
);

-- ============================================================
-- FEDERATED LEARNING ROUNDS
-- ============================================================
CREATE TABLE IF NOT EXISTS fl_rounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    round_number INT NOT NULL UNIQUE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    participating_nodes INT NOT NULL DEFAULT 0,
    rejected_nodes INT NOT NULL DEFAULT 0,
    global_model_version TEXT NOT NULL,
    dp_epsilon_spent FLOAT NOT NULL DEFAULT 0.0,
    metrics JSONB
);

-- ============================================================
-- HOSPITAL NODES (Federated Learning)
-- ============================================================
CREATE TABLE IF NOT EXISTS hospital_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_name TEXT NOT NULL,
    location TEXT,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    local_sample_count INT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','suspended'))
);

-- ============================================================
-- AUDIT LOG (append-only, no UPDATE/DELETE)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID NOT NULL,
    ip_address INET,
    details JSONB
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_sessions_patient ON diagnostic_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON diagnostic_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON diagnostic_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_session ON clinical_reports(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_fl_rounds_number ON fl_rounds(round_number);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostic_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Patients: users can only see their own data
CREATE POLICY patients_own_data ON patients FOR ALL
    USING (auth.uid()::TEXT = id::TEXT);

-- Sessions: users can only see sessions for their own patient records
CREATE POLICY sessions_own_data ON diagnostic_sessions FOR ALL
    USING (patient_id IN (SELECT id FROM patients WHERE auth.uid()::TEXT = id::TEXT));

-- Reports: same as sessions
CREATE POLICY reports_own_data ON clinical_reports FOR ALL
    USING (session_id IN (
        SELECT ds.id FROM diagnostic_sessions ds
        JOIN patients p ON ds.patient_id = p.id
        WHERE auth.uid()::TEXT = p.id::TEXT
    ));

-- Audit log: only service role can read/write
CREATE POLICY audit_service_only ON audit_log FOR ALL
    USING (auth.role() = 'service_role');

-- FL rounds and hospital nodes: public read, service role write
CREATE POLICY fl_rounds_read ON fl_rounds FOR SELECT USING (true);
CREATE POLICY hospital_nodes_read ON hospital_nodes FOR SELECT USING (true);
