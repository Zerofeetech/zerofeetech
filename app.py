import os, sqlite3, secrets
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'zerofeetech.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','false').lower() == 'true', MAX_CONTENT_LENGTH=2 * 1024 * 1024)
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@zerofeetech.com').lower().strip()

SERVICES = [
 ('AI & Automation','Practical AI workflows, chat assistants, and repetitive-task automation.','✳'),
 ('Web & App Development','Responsive websites, landing pages, dashboards, and app prototypes.','⌘'),
 ('Brand & Design','Brand identity, social graphics, presentations, and clean UI concepts.','◈'),
 ('Content & Writing','Website copy, product descriptions, captions, and content planning.','✎'),
 ('Marketing Support','Campaign planning, SEO foundations, and social media systems.','↗'),
 ('Data & Business Support','Spreadsheet cleanup, reporting templates, research, and admin workflows.','▦'),
 ('E-commerce Support','Store setup guidance, product listings, and catalog organization.','◇'),
 ('QA & Technical Support','Website checks, documentation, and practical technical guidance.','⌁')]

TOOLS = [
 {'id':'prompt','name':'Prompt Builder','desc':'Turn a rough idea into a clear, reusable AI prompt.','tag':'Writing'},
 {'id':'bio','name':'Bio & About Generator','desc':'Draft a concise professional bio for a person or brand.','tag':'Brand'},
 {'id':'caption','name':'Social Caption Studio','desc':'Create caption ideas with a hook and call to action.','tag':'Marketing'},
 {'id':'brief','name':'Project Brief Builder','desc':'Organize a project idea into a useful creative brief.','tag':'Business'}]

def db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_=None):
    conn = g.pop('db', None)
    if conn: conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, service TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL)')
    conn.commit(); conn.close()

@app.before_request
def prepare():
    init_db()
    g.user = None
    if session.get('user_id'):
        g.user = db().execute('SELECT id,name,email FROM users WHERE id=?',(session['user_id'],)).fetchone()

@app.context_processor
def inject_globals():
    return {'current_user': getattr(g,'user',None), 'year': datetime.utcnow().year}

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not g.user:
            flash('Please sign in to open your dashboard.','info'); return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not g.user or g.user['email'].lower() != ADMIN_EMAIL:
            flash('Admin access is restricted.','error'); return redirect(url_for('index'))
        return fn(*args, **kwargs)
    return wrapped

@app.route('/')
def index(): return render_template('index.html', services=SERVICES[:4], tools=TOOLS)

@app.route('/services')
def services(): return render_template('services.html', services=SERVICES)

@app.route('/tools')
def tools_page(): return render_template('tools.html', tools=TOOLS)

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        if len(name)<2 or '@' not in email or len(password)<8:
            flash('Enter your name, a valid email, and a password with at least 8 characters.','error')
        else:
            try:
                cur=db().execute('INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)',(name,email,generate_password_hash(password),datetime.utcnow().isoformat()))
                db().commit(); session['user_id']=cur.lastrowid; flash('Your account is ready. Welcome to ZeroFeeTech!','success'); return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError: flash('An account with this email already exists. Please sign in.','error')
    return render_template('auth.html', mode='signup')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        user=db().execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if user and check_password_hash(user['password_hash'],password):
            session.clear(); session['user_id']=user['id']; flash('You are signed in.','success'); return redirect(url_for('dashboard'))
        flash('Email or password is incorrect.','error')
    return render_template('auth.html', mode='login')

@app.route('/logout')
def logout(): session.clear(); flash('You have been signed out.','info'); return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=g.user, requests=db().execute('SELECT * FROM requests WHERE email=? ORDER BY id DESC',(g.user['email'],)).fetchall())

@app.route('/admin')
@admin_required
def admin():
    users=db().execute('SELECT id,name,email,created_at FROM users ORDER BY id DESC LIMIT 100').fetchall()
    requests=db().execute('SELECT * FROM requests ORDER BY id DESC LIMIT 100').fetchall()
    return render_template('admin.html', users=users, requests=requests)

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip(); service=request.form.get('service','General enquiry').strip(); message=request.form.get('message','').strip()
        if len(name)<2 or '@' not in email or len(message)<10:
            flash('Please complete all fields and write a message of at least 10 characters.','error')
        else:
            db().execute('INSERT INTO requests(name,email,service,message,created_at) VALUES(?,?,?,?,?)',(name,email,service,message,datetime.utcnow().isoformat())); db().commit()
            flash('Your project enquiry has been saved. We will review it soon.','success'); return redirect(url_for('contact'))
    return render_template('contact.html')

@app.errorhandler(404)
def not_found(_): return render_template('404.html'),404

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=False)
