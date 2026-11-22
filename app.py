import os, sqlite3, secrets
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('DATABASE_PATH', str(BASE_DIR / 'zerofeetech.db')))
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@zerofeetech.com').strip().lower()
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', 'true').lower() == 'true', MAX_CONTENT_LENGTH=2 * 1024 * 1024)


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT 'user', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
          name TEXT NOT NULL, email TEXT NOT NULL, service TEXT NOT NULL,
          details TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'New', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS saved_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          title TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL);
        ''')


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    with db() as con:
        row = con.execute('SELECT id,name,email,role,created_at FROM users WHERE id=?', (uid,)).fetchone()
    if not row:
        session.pop('user_id', None)
        return None
    return dict(row)


def csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = csrf_token
app.jinja_env.globals['site_user'] = current_user

@app.before_request
def protect_posts():
    # Stateless prompt generation does not modify account or project data.
    if request.endpoint == 'build_prompt':
        return
    if request.method == 'POST':
        sent = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not sent or not secrets.compare_digest(sent, session.get('csrf_token', '')):
            abort(400, 'Security token expired. Refresh the page and try again.')


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('Please sign in to continue.', 'info')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user['role'] != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped

@app.get('/')
def index():
    return render_template('index.html', title='ZeroFeeTech')

@app.get('/health')
def health():
    return jsonify(status='ok', service='ZeroFeeTech')

@app.get('/tools')
def tools():
    return render_template('tools.html', title='Free tools')

@app.post('/api/prompt')
def build_prompt():
    data = request.get_json(silent=True) or {}
    category = str(data.get('category', 'Website')).strip()[:80]
    idea = str(data.get('idea', '')).strip()[:3000]
    audience = str(data.get('audience', 'general users')).strip()[:200]
    style = str(data.get('style', 'modern, accessible and professional')).strip()[:200]
    if len(idea) < 5:
        return jsonify(error='Please describe your idea in a little more detail.'), 400
    prompt = (f'Act as an experienced {category} specialist. Create a practical project brief for this idea: {idea}. '
              f'Target audience: {audience}. Style: {style}. Include goals, requirements, user journey, responsive design, '
              'accessibility, technical approach, testing, deployment steps, risks, and any paid services required. '
              'Do not claim anything has been built or tested unless it has.')
    return jsonify(prompt=prompt, notice='This free tool creates a reusable prompt. It does not itself generate an AI answer.')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()[:80]
        email = request.form.get('email', '').strip().lower()[:254]
        password = request.form.get('password', '')
        if len(name) < 2 or '@' not in email or len(password) < 10:
            flash('Enter your name, a valid email, and a password of at least 10 characters.', 'error')
        else:
            role = 'admin' if email == ADMIN_EMAIL and ADMIN_PASSWORD and secrets.compare_digest(password, ADMIN_PASSWORD) else 'user'
            try:
                with db() as con:
                    con.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                                (name, email, generate_password_hash(password), role, now_iso()))
                flash('Account created. You can now sign in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('An account with that email already exists. Please sign in.', 'error')
    return render_template('auth.html', title='Create account', mode='signup')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()[:254]
        password = request.form.get('password', '')
        with db() as con:
            user = con.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if email == ADMIN_EMAIL and ADMIN_PASSWORD and secrets.compare_digest(password, ADMIN_PASSWORD):
            with db() as con:
                if user:
                    con.execute("UPDATE users SET role='admin', password_hash=? WHERE id=?", (generate_password_hash(password), user['id']))
                    user = con.execute('SELECT * FROM users WHERE id=?', (user['id'],)).fetchone()
                else:
                    con.execute("INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,'admin',?)", ('ZeroFeeTech Admin', ADMIN_EMAIL, generate_password_hash(password), now_iso()))
                    user = con.execute('SELECT * FROM users WHERE email=?', (ADMIN_EMAIL,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['csrf_token'] = secrets.token_urlsafe(32)
            dest = request.args.get('next', '')
            return redirect(dest if dest.startswith('/') and not dest.startswith('//') else url_for('admin' if user['role'] == 'admin' else 'dashboard'))
        flash('Email or password is incorrect.', 'error')
    return render_template('auth.html', title='Sign in', mode='login')

@app.post('/logout')
@login_required
def logout():
    session.clear()
    flash('You have signed out.', 'info')
    return redirect(url_for('index'))

@app.get('/dashboard')
@login_required
def dashboard():
    user = current_user()
    with db() as con:
        projects = con.execute('SELECT * FROM projects WHERE user_id=? ORDER BY id DESC LIMIT 30', (user['id'],)).fetchall()
        saved = con.execute('SELECT * FROM saved_items WHERE user_id=? ORDER BY id DESC LIMIT 30', (user['id'],)).fetchall()
    return render_template('dashboard.html', title='Your workspace', user=user, projects=projects, saved=saved)

@app.post('/save')
@login_required
def save_item():
    title = request.form.get('title', 'Saved prompt').strip()[:120]
    content = request.form.get('content', '').strip()[:12000]
    if not content:
        flash('There is nothing to save yet.', 'error')
    else:
        with db() as con:
            con.execute('INSERT INTO saved_items(user_id,title,content,created_at) VALUES(?,?,?,?)',
                        (current_user()['id'], title, content, now_iso()))
        flash('Saved to your workspace.', 'success')
    return redirect(url_for('dashboard'))

@app.post('/contact')
def contact():
    name = request.form.get('name', '').strip()[:100]
    email = request.form.get('email', '').strip()[:254]
    service = request.form.get('service', 'General enquiry').strip()[:100]
    details = request.form.get('details', '').strip()[:4000]
    if len(name) < 2 or '@' not in email or len(details) < 10:
        flash('Please complete your name, valid email and project details.', 'error')
        return redirect(url_for('index') + '#contact')
    user = current_user()
    with db() as con:
        con.execute('INSERT INTO projects(user_id,name,email,service,details,status,created_at) VALUES(?,?,?,?,?,?,?)',
                    (user['id'] if user else None, name, email, service, details, 'New', now_iso()))
    flash('Your project enquiry has been received. Email notifications are not configured in this starter.', 'success')
    return redirect(url_for('dashboard') if user else url_for('index') + '#contact')

@app.get('/admin')
@admin_required
def admin():
    with db() as con:
        users = con.execute('SELECT id,name,email,role,created_at FROM users ORDER BY id DESC LIMIT 200').fetchall()
        projects = con.execute('SELECT * FROM projects ORDER BY id DESC LIMIT 200').fetchall()
        stats = {'users': con.execute('SELECT COUNT(*) FROM users').fetchone()[0],
                 'projects': con.execute('SELECT COUNT(*) FROM projects').fetchone()[0],
                 'new': con.execute("SELECT COUNT(*) FROM projects WHERE status='New'").fetchone()[0]}
    return render_template('admin.html', title='Admin dashboard', users=users, projects=projects, stats=stats)

@app.post('/admin/project/<int:project_id>/status')
@admin_required
def update_status(project_id):
    status = request.form.get('status', 'New')
    if status not in {'New', 'Reviewing', 'In progress', 'Completed', 'Archived'}:
        abort(400)
    with db() as con:
        con.execute('UPDATE projects SET status=? WHERE id=?', (status, project_id))
    flash('Project status updated.', 'success')
    return redirect(url_for('admin'))

@app.errorhandler(400)
def bad_request(error):
    return render_template('error.html', title='Request error', code=400, message=getattr(error, 'description', 'Please refresh and try again.')), 400

@app.errorhandler(403)
def forbidden(_error):
    return render_template('error.html', title='Access restricted', code=403, message='This area is only available to the administrator.'), 403

@app.errorhandler(404)
def not_found(_error):
    return render_template('error.html', title='Page not found', code=404, message='The page could not be found. Return to the homepage.'), 404

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
