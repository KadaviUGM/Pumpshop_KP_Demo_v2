from __future__ import annotations
import uuid
from datetime import date
import streamlit as st
import auth, db

st.set_page_config(page_title='Pumpshop Demo',page_icon='🛠️',layout='wide')
st.markdown('''<style>
.stApp{background:#f6f8f6;color:#26332a}.block-container{max-width:1320px;padding-top:1.2rem}
[data-testid=stMetric]{background:#fff;border:1px solid #e4ebe5;border-top:3px solid #0086c9;border-radius:12px;padding:14px}
[data-testid=stSidebar]{background:#eef4ef}h1,h2,h3{color:#24372b}
.demo{background:#fff5df;border-left:4px solid #e31b23;padding:12px;border-radius:8px;margin:8px 0 16px}
@media(max-width:700px){.block-container{padding:1rem .75rem}}
</style>''',unsafe_allow_html=True)

def seed_data():
    with db.session() as c:
        for row in [('IT-SRP','Pompa SRP 20-175','SRP','unit','POOL'),('IT-ESP','Pompa ESP IND-450','ESP','unit','POOL'),('IT-CBL','Kabel ESP AWG #4','Kabel ESP','meter','POOL')]:
            c.execute('INSERT INTO items(item_id,name,category,unit,tracking_mode) VALUES(?,?,?,?,?) ON CONFLICT(item_id) DO NOTHING',row)
        if not c.execute('SELECT 1 FROM stock_batches LIMIT 1').fetchone():
            for row in [('B-001','IT-SRP','EJP','Pumpshop Cepu','NEW',8),('B-002','IT-SRP','EJP','Pumpshop Cepu','USED_READY',4),('B-003','IT-ESP','Pertamina','Pumpshop Cepu','INSPECTION',2),('B-004','IT-CBL','Pertamina','Pumpshop Cepu','USED_READY',1500)]:
                c.execute('INSERT INTO stock_batches(batch_id,item_id,owner,location,condition,qty,source_note,updated_by) VALUES(?,?,?,?,?,?,?,?)',(*row,'Fixture sintetis','USR-DEMO-SUPERADMIN'))
        for p in [('POL-SRP','IT-SRP',3,8,45,'USR-DEMO-SUPERADMIN'),('POL-ESP','IT-ESP',2,5,60,'USR-DEMO-SUPERADMIN')]:
            c.execute('INSERT INTO reorder_policies(policy_id,item_id,minimum_qty,target_qty,lead_time_days,updated_by) VALUES(?,?,?,?,?,?) ON CONFLICT(item_id) DO NOTHING',p)
        if not c.execute('SELECT 1 FROM well_plans LIMIT 1').fetchone():
            c.execute("INSERT INTO well_plans(plan_id,well_name,item_id,required_date,qty,preference,entered_by) VALUES('PLAN-01','DEMO-KWG-05','IT-SRP','2026-11-20',2,'USED_READY','USR-DEMO-TECH')")
        if not c.execute('SELECT 1 FROM pump_events LIMIT 1').fetchone():
            for eid,well,mode,status in [('EV-001','DEMO-KWG-01','Seal wear','SUSPECTED'),('EV-002','DEMO-KWG-01','Electrical','UNKNOWN'),('EV-003','DEMO-SMG-02','Unknown','UNKNOWN'),('EV-004','DEMO-KWG-03','Seal wear','CONFIRMED')]:
                c.execute("INSERT INTO pump_events(event_id,event_date,well_name,item_id,event_type,pull_reason,condition,runlife_days,symptoms,cause_status,failure_mode,entered_by) VALUES(?,?,?,'IT-SRP','PULL','FAILURE','DAMAGED',300,?,?,?,'USR-DEMO-TECH')",(eid,'2026-10-01',well,'Fixture sintetik',status,mode))

def require(user,*roles):
    if user.get('role') not in roles: raise PermissionError('Aksi tidak diizinkan untuk role ini.')

def add_stock(user,item,owner,location,condition,qty):
    require(user,'admin','superadmin')
    bid='B-'+uuid.uuid4().hex[:10].upper()
    with db.session() as c:
        c.execute('INSERT INTO stock_batches(batch_id,item_id,owner,location,condition,qty,source_note,updated_by) VALUES(?,?,?,?,?,?,?,?)',(bid,item,owner,location,condition,qty,'Input stok demo',user['user_id']))
        db.audit(c,user,'CREATE','stock_batch',bid,{'item':item,'qty':qty,'condition':condition,'location':location})

def set_account_active(user,target,active):
    require(user,'superadmin')
    if target==user['user_id']: raise ValueError('Superadmin tidak dapat menonaktifkan akunnya sendiri.')
    with db.session() as c:
        c.execute('UPDATE demo_users SET active=? WHERE user_id=?',(active,target))
        db.audit(c,user,'UPDATE','demo_user',target,{'active':active})

def main():
    try:
        db.init_db(); password=db.setting('DEMO_PASSWORD')
        if len(password)<12: raise RuntimeError('Secret DEMO_PASSWORD belum diatur atau kurang dari 12 karakter.')
        auth.seed_accounts(password); seed_data()
    except Exception as exc:
        st.error(f'Koneksi/database belum siap: {exc}'); st.stop()
    if 'user' not in st.session_state:
        st.title('Pumpshop Operations'); st.caption('Demo KP · data sintetis')
        with st.form('login'):
            name=st.text_input('Username',placeholder='demo-tech'); pwd=st.text_input('Sandi demo',type='password'); submitted=st.form_submit_button('Masuk',type='primary',use_container_width=True)
        if submitted:
            u=auth.login(name,pwd)
            if u: st.session_state.user=u; st.rerun()
            st.error('Username atau sandi tidak cocok.')
        st.info('Akun simulasi: demo-tech · demo-admin · demo-superadmin · demo-viewer. Sandi diatur pemilik app melalui Secret.')
        return
    u=st.session_state.user
    st.sidebar.image('assets/pertamina_ep_cepu_light_transparent.png',use_container_width=True)
    st.sidebar.caption(f"{u['username']} · {auth.ROLES[u['role']]}")
    pages=['Ringkasan','Inventori','Kejadian pompa','Operasi harian','Audit']
    if u['role']=='superadmin': pages.append('Kelola akun')
    page=st.sidebar.radio('Menu',pages)
    if st.sidebar.button('Keluar'): del st.session_state.user; st.rerun()
    st.markdown('<div class="demo"><b>SIMULASI · DATA DUMMY</b> — jangan gunakan untuk keputusan operasi.</div>',unsafe_allow_html=True)
    if page=='Ringkasan':
        events=db.fetchall("SELECT * FROM pump_events WHERE event_type='PULL' AND pull_reason='FAILURE'")
        stock=db.fetchall('SELECT i.name,b.condition,SUM(b.qty) qty FROM stock_batches b JOIN items i ON i.item_id=b.item_id GROUP BY i.name,b.condition')
        total=sum(float(r['qty']) for r in stock); damaged=sum(float(r['qty']) for r in stock if r['condition']=='DAMAGED'); ready=sum(float(r['qty']) for r in stock if r['condition'] in {'NEW','USED_READY'})
        a,b,c,d=st.columns(4); a.metric('Pull rusak tercatat',len(events)); b.metric('Sumur terdampak',len({e['well_name'] for e in events})); c.metric('Stok siap pakai',f'{ready:g}'); d.metric('Stok rusak',f'{damaged:g}')
        x,y=st.columns(2); counts={}; modes={}
        for e in events:
            counts[e['well_name']]=counts.get(e['well_name'],0)+1; mode=e['failure_mode'] or 'Belum diketahui'; modes[mode]=modes.get(mode,0)+1
        x.subheader('Pull rusak per sumur'); x.bar_chart(dict(sorted(counts.items(),key=lambda v:v[1],reverse=True)))
        y.subheader('Mode tercatat'); y.bar_chart(modes)
        st.caption('Indikasi untuk ditinjau; data dummy tidak membuktikan akar sebab atau treatment sumur.')
        st.subheader('Kesiapan stok & rencana sumur')
        policies=db.fetchall('SELECT i.name,p.minimum_qty,p.target_qty,p.lead_time_days,COALESCE(SUM(b.qty),0) stock FROM reorder_policies p JOIN items i ON i.item_id=p.item_id LEFT JOIN stock_batches b ON b.item_id=p.item_id AND b.condition IN (\'NEW\',\'USED_READY\') GROUP BY i.name,p.minimum_qty,p.target_qty,p.lead_time_days ORDER BY i.name')
        st.dataframe([dict(r,alert='TINJAU ORDER' if float(r['stock'])<=float(r['minimum_qty']) else 'Aman') for r in policies],width='stretch',hide_index=True)
        st.caption('Alert membandingkan stok demo dengan minimum yang ditetapkan; bukan pemesanan otomatis.')
        st.dataframe(db.fetchall('SELECT p.well_name,i.name,p.required_date,p.qty,p.preference,p.status FROM well_plans p JOIN items i ON i.item_id=p.item_id ORDER BY p.required_date'),width='stretch',hide_index=True)
    elif page=='Inventori':
        if u['role'] in {'admin','superadmin'}:
            with st.expander('Tambah stok kelompok'):
                with st.form('stock_add'):
                    item=st.selectbox('Barang',db.fetchall('SELECT item_id,name FROM items WHERE active=TRUE ORDER BY name'),format_func=lambda x:x['name'])
                    owner=st.text_input('Pemilik'); location=st.text_input('Lokasi'); condition=st.selectbox('Kondisi',['NEW','USED_READY','DAMAGED','INSPECTION']); qty=st.number_input('Jumlah',min_value=0.01,value=1.0); save=st.form_submit_button('Simpan stok',type='primary')
                if save:
                    add_stock(u,item['item_id'],owner,location,condition,qty); st.success('Stok tersimpan dan diaudit.')
        st.dataframe(db.fetchall('SELECT i.name,b.owner,b.location,b.condition,SUM(b.qty) qty,i.unit FROM stock_batches b JOIN items i ON i.item_id=b.item_id GROUP BY i.name,b.owner,b.location,b.condition,i.unit ORDER BY i.name'),width='stretch',hide_index=True)
        st.caption('Barang tanpa serial dibukukan sebagai kelompok kondisi/lokasi; identitas database bukan label fisik.')
        if u['role'] in {'admin','superadmin'}:
            with st.expander('Rencana kebutuhan sumur'):
                with st.form('plan_add'):
                    well=st.text_input('Sumur tujuan'); item=st.selectbox('Barang rencana',db.fetchall('SELECT item_id,name FROM items WHERE active=TRUE ORDER BY name'),format_func=lambda x:x['name']); need=st.date_input('Tanggal dibutuhkan'); qty=st.number_input('Jumlah',min_value=1,value=1); pref=st.selectbox('Preferensi kondisi',['NEW','USED_READY','EITHER']); saved=st.form_submit_button('Simpan rencana',type='primary')
                if saved and well.strip():
                    pid='PLAN-'+uuid.uuid4().hex[:8].upper()
                    with db.session() as c:
                        c.execute('INSERT INTO well_plans(plan_id,well_name,item_id,required_date,qty,preference,entered_by) VALUES(?,?,?,?,?,?,?)',(pid,well,item['item_id'],need.isoformat(),qty,pref,u['user_id']))
                        db.audit(c,u,'CREATE','well_plan',pid,{'well':well,'qty':qty,'preference':pref})
    elif page=='Kejadian pompa':
        if u['role'] in {'technician','admin','superadmin'}:
            with st.form('event'):
                st.subheader('Form teknisi · satu kejadian'); well=st.text_input('Sumur'); kind=st.selectbox('Kejadian',['PULL','INSTALL']); reason=st.selectbox('Alasan pull',['FAILURE','SCHEDULED','OTHER','UNKNOWN']); runlife=st.number_input('Runlife (hari)',min_value=0,value=0); symptoms=st.text_input('Gejala singkat'); mode=st.text_input('Mode (opsional)'); cause=st.selectbox('Status sebab',['UNKNOWN','SUSPECTED','CONFIRMED']); save=st.form_submit_button('Simpan kejadian',type='primary')
            if save and well.strip():
                require(u,'technician','admin','superadmin'); eid='EV-'+uuid.uuid4().hex[:10].upper()
                with db.session() as c:
                    c.execute('INSERT INTO pump_events(event_id,event_date,well_name,item_id,event_type,pull_reason,condition,runlife_days,symptoms,cause_status,failure_mode,entered_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(eid,date.today().isoformat(),well,'IT-SRP',kind,reason,'DAMAGED' if kind=='PULL' else 'USED',runlife,symptoms,cause,mode,u['user_id']))
                    db.audit(c,u,'CREATE','pump_event',eid,{'well':well,'kind':kind,'cause_status':cause})
                st.success('Tersimpan dan masuk audit.')
        st.dataframe(db.fetchall('SELECT event_date,well_name,event_type,pull_reason,runlife_days,symptoms,cause_status,failure_mode FROM pump_events ORDER BY event_date DESC'),width='stretch',hide_index=True)
    elif page=='Operasi harian':
        if u['role'] in {'technician','admin','superadmin'}:
            with st.form('daily'):
                team=st.text_input('Tim/shift'); people=st.number_input('Jumlah hadir',min_value=0,value=0); req=st.number_input('Medical wajib',min_value=0,value=0); done=st.number_input('Medical selesai',min_value=0,value=0); meet=st.checkbox('Daily meeting terlaksana'); save=st.form_submit_button('Simpan log',type='primary')
            if save:
                if done>req: st.error('Jumlah selesai melebihi jumlah wajib.')
                else:
                    require(u,'technician','admin','superadmin'); lid='LOG-'+uuid.uuid4().hex[:10].upper()
                    with db.session() as c:
                        c.execute('INSERT INTO daily_ops(log_id,work_date,shift,team,present_count,medical_required,medical_completed,meeting_held,meeting_participants,entered_by) VALUES(?,?,?,?,?,?,?,?,?,?)',(lid,date.today().isoformat(),'Demo',team,people,req,done,meet,people if meet else 0,u['user_id']))
                        db.audit(c,u,'CREATE','daily_ops',lid,{'team':team,'people':people,'medical':done})
        st.dataframe(db.fetchall('SELECT work_date,shift,team,present_count,medical_required,medical_completed,meeting_held,entered_by FROM daily_ops ORDER BY work_date DESC'),width='stretch',hide_index=True)
    elif page=='Audit':
        if u['role']=='technician': st.warning('Audit tidak tersedia untuk role teknisi.'); return
        st.dataframe(db.fetchall('SELECT occurred_at,actor_username,actor_role,action,entity,entity_id,details_json FROM audit_log ORDER BY occurred_at DESC LIMIT 300'),width='stretch',hide_index=True)
    elif page=='Kelola akun':
        require(u,'superadmin')
        accounts=db.fetchall('SELECT user_id,username,role,active FROM demo_users ORDER BY username')
        st.dataframe(accounts,width='stretch',hide_index=True)
        target=st.selectbox('Pilih akun',accounts,format_func=lambda x:f"{x['username']} · {auth.ROLES[x['role']]} · {'aktif' if x['active'] else 'nonaktif'}")
        active=st.toggle('Akun aktif',value=bool(target['active']),key='account_toggle')
        if st.button('Simpan status akun',type='primary'):
            try: set_account_active(u,target['user_id'],active); st.success('Status akun diperbarui dan diaudit.'); st.rerun()
            except Exception as exc: st.error(str(exc))

if __name__=='__main__': main()
