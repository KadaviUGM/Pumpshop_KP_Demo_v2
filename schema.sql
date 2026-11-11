-- Fresh, synthetic-only Pumpshop demo schema. Apply once to an empty Supabase project.
CREATE TABLE demo_users (
  user_id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('technician','admin','superadmin','viewer')),
  password_hash TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE items (
  item_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  category TEXT NOT NULL,
  unit TEXT NOT NULL,
  tracking_mode TEXT NOT NULL CHECK(tracking_mode IN ('POOL','INDIVIDUAL')),
  active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE stock_batches (
  batch_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL REFERENCES items(item_id),
  owner TEXT NOT NULL,
  location TEXT NOT NULL,
  condition TEXT NOT NULL CHECK(condition IN ('NEW','USED_READY','DAMAGED','INSPECTION')),
  qty NUMERIC(12,2) NOT NULL CHECK(qty >= 0),
  physical_label TEXT NOT NULL DEFAULT '',
  source_note TEXT NOT NULL DEFAULT '',
  updated_by TEXT NOT NULL REFERENCES demo_users(user_id),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE pump_events (
  event_id TEXT PRIMARY KEY,
  event_date DATE NOT NULL,
  well_name TEXT NOT NULL,
  item_id TEXT NOT NULL REFERENCES items(item_id),
  event_type TEXT NOT NULL CHECK(event_type IN ('INSTALL','PULL')),
  pull_reason TEXT NOT NULL DEFAULT 'UNKNOWN',
  condition TEXT NOT NULL,
  runlife_days INTEGER,
  symptoms TEXT NOT NULL DEFAULT '',
  cause_status TEXT NOT NULL CHECK(cause_status IN ('UNKNOWN','SUSPECTED','CONFIRMED')),
  failure_mode TEXT NOT NULL DEFAULT '',
  report_ref TEXT NOT NULL DEFAULT '',
  entered_by TEXT NOT NULL REFERENCES demo_users(user_id),
  entered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE repair_reports (
  report_id TEXT PRIMARY KEY,
  event_id TEXT REFERENCES pump_events(event_id),
  source_well TEXT NOT NULL,
  received_date DATE NOT NULL,
  analysis TEXT NOT NULL DEFAULT '',
  disposition TEXT NOT NULL DEFAULT 'PENDING',
  entered_by TEXT NOT NULL REFERENCES demo_users(user_id),
  entered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE well_plans (
  plan_id TEXT PRIMARY KEY, well_name TEXT NOT NULL, item_id TEXT NOT NULL REFERENCES items(item_id),
  required_date DATE NOT NULL, qty NUMERIC(12,2) NOT NULL CHECK(qty > 0),
  preference TEXT NOT NULL CHECK(preference IN ('NEW','USED_READY','EITHER')),
  status TEXT NOT NULL DEFAULT 'PROPOSED', entered_by TEXT NOT NULL REFERENCES demo_users(user_id),
  entered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE reorder_policies (
  policy_id TEXT PRIMARY KEY, item_id TEXT NOT NULL UNIQUE REFERENCES items(item_id),
  minimum_qty NUMERIC(12,2) NOT NULL CHECK(minimum_qty >= 0), target_qty NUMERIC(12,2) NOT NULL CHECK(target_qty >= minimum_qty),
  lead_time_days INTEGER NOT NULL CHECK(lead_time_days >= 0), updated_by TEXT NOT NULL REFERENCES demo_users(user_id),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE daily_ops (
  log_id TEXT PRIMARY KEY,
  work_date DATE NOT NULL,
  shift TEXT NOT NULL,
  team TEXT NOT NULL,
  present_count INTEGER NOT NULL DEFAULT 0 CHECK(present_count >= 0),
  medical_required INTEGER NOT NULL DEFAULT 0 CHECK(medical_required >= 0),
  medical_completed INTEGER NOT NULL DEFAULT 0 CHECK(medical_completed BETWEEN 0 AND medical_required),
  meeting_held BOOLEAN NOT NULL DEFAULT FALSE,
  meeting_participants INTEGER NOT NULL DEFAULT 0 CHECK(meeting_participants >= 0),
  notes TEXT NOT NULL DEFAULT '',
  entered_by TEXT NOT NULL REFERENCES demo_users(user_id),
  entered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE audit_log (
  audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_id TEXT NOT NULL,
  actor_username TEXT NOT NULL,
  actor_role TEXT NOT NULL,
  action TEXT NOT NULL,
  entity TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_stock_item_location ON stock_batches(item_id,location,condition);
CREATE INDEX ix_event_well_date ON pump_events(well_name,event_date);
CREATE INDEX ix_audit_time ON audit_log(occurred_at DESC);
CREATE OR REPLACE FUNCTION deny_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'audit_log is append-only'; END; $$;
CREATE TRIGGER audit_no_update BEFORE UPDATE OR DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION deny_audit_mutation();
