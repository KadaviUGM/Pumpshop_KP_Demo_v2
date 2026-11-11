import hashlib, hmac, secrets
from db import session

ROLES={'technician':'Teknisi / client','admin':'Admin','superadmin':'Superadmin','viewer':'Viewer'}
ACCOUNTS={'demo-tech':'technician','demo-admin':'admin','demo-superadmin':'superadmin','demo-viewer':'viewer'}
def _hash(password,salt):
    salt_bytes=bytes.fromhex(salt) if isinstance(salt,str) else salt
    return hashlib.pbkdf2_hmac('sha256',password.encode(),salt_bytes,240_000).hex()
def seed_accounts(password):
    if len(password)<12: raise ValueError('Sandi demo minimal 12 karakter.')
    with session() as c:
        for username,role in ACCOUNTS.items():
            old=c.execute('SELECT user_id FROM demo_users WHERE username=?',(username,)).fetchone()
            if old: continue
            salt=secrets.token_hex(16); uid='USR-'+username.upper()
            c.execute('INSERT INTO demo_users(user_id,username,role,password_hash) VALUES(?,?,?,?)',(uid,username,role,salt+':'+_hash(password,salt)))
def login(username,password):
    with session() as c: row=c.execute('SELECT * FROM demo_users WHERE username=? AND active=TRUE',(username.strip(),)).fetchone()
    if not row: return None
    row=dict(row); salt,digest=row['password_hash'].split(':',1)
    return row if hmac.compare_digest(_hash(password,salt),digest) else None
def require(user,*roles):
    if not user or user.get('role') not in roles: raise PermissionError('Aksi tidak diizinkan untuk role ini.')
