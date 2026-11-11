from __future__ import annotations
import json, os, re, sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SCHEMA=(ROOT/'schema.sql').read_text(encoding='utf-8')

def setting(key, default=''):
    try:
        import streamlit as st
        v=st.secrets.get(key, '')
        if v: return str(v)
    except Exception: pass
    return os.environ.get(key, default)

def _sqlite_schema():
    s=SCHEMA.split('CREATE OR REPLACE FUNCTION deny_audit_mutation')[0]
    s=s.replace('BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY','INTEGER PRIMARY KEY AUTOINCREMENT')
    s=s.replace('TIMESTAMPTZ NOT NULL DEFAULT now()','TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP')
    s=s.replace('DATE NOT NULL','TEXT NOT NULL').replace('JSONB NOT NULL DEFAULT \'{}\'::jsonb',"TEXT NOT NULL DEFAULT '{}'")
    s += "\nCREATE TRIGGER IF NOT EXISTS audit_deny_update BEFORE UPDATE ON audit_log BEGIN SELECT RAISE(ABORT,'audit_log is append-only'); END;\nCREATE TRIGGER IF NOT EXISTS audit_deny_delete BEFORE DELETE ON audit_log BEGIN SELECT RAISE(ABORT,'audit_log is append-only'); END;\n"
    return s

class PG:
    def __init__(self,url):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        self.driver=psycopg2; self.c=psycopg2.connect(url,sslmode='require',connect_timeout=10,cursor_factory=RealDictCursor)
    def execute(self,q,args=()):
        cur=self.c.cursor()
        try: cur.execute(re.sub(r'\?', '%s', q),args)
        except self.driver.Error as e:
            self.c.rollback(); raise RuntimeError('Database PostgreSQL menolak operasi; periksa skema dan koneksi.') from e
        return cur
    def commit(self): self.c.commit()
    def close(self): self.c.close()

def connect():
    url=setting('SUPABASE_DB_URL')
    if url: return PG(url)
    if setting('ALLOW_LOCAL_SQLITE')!='1':
        raise RuntimeError('Supabase belum dikonfigurasi. Hosted app tidak boleh memakai fallback SQLite.')
    path=Path(os.environ.get('PUMPSHOP_LOCAL_DB',str(ROOT/'local_demo.sqlite3')))
    c=sqlite3.connect(path,timeout=10); c.row_factory=sqlite3.Row; return c

def init_db():
    c=connect()
    if isinstance(c,PG):
        # Hosted schema is applied explicitly in Supabase SQL Editor, never auto-created by the app.
        c.execute('SELECT 1 FROM demo_users LIMIT 1'); c.commit()
    else:
        c.executescript(_sqlite_schema()); c.commit()
    c.close()

@contextmanager
def session():
    c=connect()
    try:
        yield c
        c.commit()
    finally: c.close()

def fetchall(q,args=()):
    with session() as c:
        cur=c.execute(q,args); return [dict(r) for r in cur.fetchall()]

def audit(c,user,action,entity,entity_id,details):
    payload=json.dumps(details,ensure_ascii=False)
    cast='?::jsonb' if isinstance(c,PG) else '?'
    c.execute(f'INSERT INTO audit_log(actor_id,actor_username,actor_role,action,entity,entity_id,details_json) VALUES(?,?,?,?,?,?,'+cast+')',
              (user['user_id'],user['username'],user['role'],action,entity,entity_id,payload))
