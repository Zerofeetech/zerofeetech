import os
import sqlite3
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('DATABASE_PATH', str(BASE_DIR / 'zerofeetech.db')))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-this-secret-before-deployment')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE', 'false').lower() == 'true'
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@zerofeetech.com').strip().lower()
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT 'user',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          name TEXT NOT NULL,
          email TEXT NOT NULL,
          service TEXT NOT NULL,
          budget TEXT DEFAULT 'Not specified',
          details TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'New',
          created_at TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS saved_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          title TEXT NOT NULL,
          kind TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        ''')
        # Promote only the configured admin account if its existing password hash matches
        # the configured secret. Never promote based on email address alone.
        if ADMIN_PASSWORD:
            existing = con.execute('SELECT id, password_hash FROM users WHERE email=?', (ADMIN_EMAIL,)).fetchone()
            if existing and check_password_hash(existing['password_hash'], ADMIN_PASSWORD):
                con.execute("UPDATE users SET role='admin' WHERE id=?", (existing['id'],))


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    with db() as con:
        row = con.execute('SELECT id,name,email,role,created_at FROM users WHERE id=?', (user_id,)).fetchone()
    if not row:
        session.pop('user_id', None)
        return None
    return dict(row)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('Please sign in to open your workspace.', 'info')
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


@app.context_processor
def inject_globals():
    return {
        'site_user': current_user(),
        'admin_email': ADMIN_EMAIL,
        'current_year': datetime.now().year,
        'whatsapp_url': os.environ.get('WHATSAPP_URL', '').strip(),
        'line_url': os.environ.get('LINE_URL', '').strip(),
    }


@app.before_request
def make_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)


def check_csrf():
    sent = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    return bool(sent and secrets.compare_digest(sent, session.get('csrf_token', '')))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'ZeroFeeTech'})


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if not check_csrf():
            abort(400, 'Security token expired. Refresh and try again.')
        name = request.form.get('name', '').strip()[:80]
        email = request.form.get('email', '').strip().lower()[:254]
        password = request.form.get('password', '')
        if len(name) < 2 or '@' not in email or '.' not in email.split('@')[-1]:
            flash('Enter your name and a valid email address.', 'error')
        elif len(password) < 10:
            flash('Use a password with at least 10 characters.', 'error')
        else:
            try:
                with db() as con:
                    con.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                                (name, email, generate_password_hash(password), ('admin' if email == ADMIN_EMAIL and ADMIN_PASSWORD and secrets.compare_digest(password, ADMIN_PASSWORD) else 'user'), now_iso()))
                with db() as con:
                    user = con.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
                session.clear()
                session['user_id'] = user['id']
                session['csrf_token'] = secrets.token_urlsafe(32)
                flash('Your ZeroFeeTech workspace is ready.', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                flash('An account with that email already exists. Sign in instead.', 'error')
    return render_template('auth.html', mode='signup')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if not check_csrf():
            abort(400, 'Security token expired. Refresh and try again.')
        email = request.form.get('email', '').strip().lower()[:254]
        password = request.form.get('password', '')
        with db() as con:
            user = con.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['csrf_token'] = secrets.token_urlsafe(32)
            flash('Welcome back.', 'success')
            dest = request.args.get('next', '')
            return redirect(dest if dest.startswith('/') and not dest.startswith('//') else url_for('dashboard'))
        flash('Email or password is incorrect.', 'error')
    return render_template('auth.html', mode='login')


@app.route('/logout', methods=['POST'])
def logout():
    if not check_csrf():
        abort(400)
    session.clear()
    flash('You have signed out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    with db() as con:
        projects = con.execute('SELECT * FROM projects WHERE user_id=? ORDER BY id DESC LIMIT 20', (user['id'],)).fetchall()
        saved = con.execute('SELECT * FROM saved_items WHERE user_id=? ORDER BY id DESC LIMIT 20', (user['id'],)).fetchall()
    return render_template('dashboard.html', user=user, projects=projects, saved=saved)


@app.route('/admin')
@admin_required
def admin_dashboard():
    with db() as con:
        users = con.execute('SELECT id,name,email,role,created_at FROM users ORDER BY id DESC LIMIT 100').fetchall()
        projects = con.execute('SELECT * FROM projects ORDER BY id DESC LIMIT 100').fetchall()
        counts = {
            'users': con.execute('SELECT COUNT(*) FROM users').fetchone()[0],
            'projects': con.execute('SELECT COUNT(*) FROM projects').fetchone()[0],
            'new': con.execute("SELECT COUNT(*) FROM projects WHERE status='New'").fetchone()[0],
        }
    return render_template('admin.html', users=users, projects=projects, counts=counts)


@app.route('/admin/project/<int:project_id>/status', methods=['POST'])
@admin_required
def update_project_status(project_id):
    if not check_csrf():
        abort(400)
    status = request.form.get('status', 'New')
    if status not in {'New', 'Reviewing', 'In progress', 'Completed', 'Archived'}:
        abort(400)
    with db() as con:
        con.execute('UPDATE projects SET status=? WHERE id=?', (status, project_id))
    flash('Project status updated.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/api/tool', methods=['POST'])
def tool_api():
    data = request.get_json(silent=True) or {}
    tool = str(data.get('tool', ''))[:40]
    prompt = str(data.get('prompt', '')).strip()[:3000]
    if len(prompt) < 4:
        return jsonify({'error': 'Add a few details first.'}), 400
    tool_specs = {
      'website': ('Website starter brief', 'Create a responsive, accessible website starter using semantic HTML, modern CSS, and vanilla JavaScript. Include desktop, tablet, and mobile layouts. Explain how to run it locally. Avoid external paid services.'),
      'app': ('App product brief', 'Turn the idea into a clear app product plan: target users, core screens, main user flows, data model, accessibility, security, and an MVP build plan.'),
      'software': ('Software build plan', 'Produce a practical software engineering plan: requirements, architecture, folder structure, dependencies, error handling, testing, setup instructions, and limitations.'),
      'ai': ('AI project plan', 'Design a responsible AI project plan with the use case, input/output, free-tier options where available, privacy considerations, evaluation, fallback behavior, and a realistic cost note.'),
      'automation': ('Automation workflow', 'Map this repetitive task into a workflow with trigger, steps, decision points, error handling, human approval, privacy, and free tools to investigate.'),
      'uiux': ('UI/UX design brief', 'Create a UI/UX brief with target audience, user journey, information architecture, wireframe descriptions, accessibility, and a cohesive design system.'),
      'graphic': ('Graphic design brief', 'Create a graphic design brief with composition, hierarchy, color palette, typography direction, layout, and export sizes. Do not claim an image has been rendered.'),
      'logo': ('Logo concept brief', 'Generate three original logo directions with symbol idea, typography, colors, usage notes, and a simple SVG concept if possible.'),
      'social': ('Social content planner', 'Build a useful social content plan with hooks, formats, calls to action, and a publishing checklist. Avoid false claims.'),
      'email': ('Professional email draft', 'Draft a concise, courteous professional email with a clear subject, purpose, and next step.'),
      'business': ('Business launch plan', 'Create a lean launch plan with audience, value proposition, MVP, distribution, simple metrics, and realistic risks.'),
      'code': ('Coding assistant prompt', 'Act as a careful software engineer. Clarify assumptions, provide runnable code, setup steps, tests, and security notes. Do not invent API keys or claim untested code was executed.'),
    }
    if tool not in tool_specs:
        return jsonify({'error': 'Choose one of the available tools.'}), 400
    title, instruction = tool_specs[tool]
    result = f"{instruction}\n\nProject details:\n{prompt}\n\nRequirements:\n- Prefer free and open-source options where practical.\n- State any paid service or external API requirement clearly.\n- Do not fabricate results, credentials, or capabilities.\n- Give a beginner-friendly step-by-step output."
    return jsonify({'title': title, 'result': result, 'notice': 'Free local prompt builder: this creates a reusable prompt, not an AI-generated finished project. No paid AI API is connected.'})


@app.route('/api/save', methods=['POST'])
@login_required
def save_item():
    data = request.get_json(silent=True) or {}
    if not check_csrf():
        return jsonify({'error': 'Refresh the page and try again.'}), 400
    title = str(data.get('title', 'Saved item')).strip()[:120]
    kind = str(data.get('kind', 'prompt')).strip()[:40]
    content = str(data.get('content', '')).strip()[:12000]
    if not content:
        return jsonify({'error': 'Nothing to save.'}), 400
    with db() as con:
        con.execute('INSERT INTO saved_items(user_id,title,kind,content,created_at) VALUES(?,?,?,?,?)',
                    (current_user()['id'], title, kind, content, now_iso()))
    return jsonify({'ok': True})


def send_project_notification(name, email, service, budget, details):
    """Send an optional email notification when valid SMTP settings are configured."""
    host = os.environ.get('SMTP_HOST', '').strip()
    username = os.environ.get('SMTP_USERNAME', '').strip()
    password = os.environ.get('SMTP_PASSWORD', '')
    sender = os.environ.get('SMTP_FROM', '').strip() or username
    recipient = os.environ.get('MAIL_TO', os.environ.get('CONTACT_EMAIL', 'waynepradip10@gmail.com')).strip()
    if not (host and sender and recipient):
        return False
    try:
        message = EmailMessage()
        message['Subject'] = f'New ZeroFeeTech project request: {service}'
        message['From'] = sender
        message['To'] = recipient
        message['Reply-To'] = email
        message.set_content(
            f'New project request received on ZeroFeeTech\n\n'
            f'Name: {name}\nEmail: {email}\nService: {service}\nBudget: {budget}\n\n'
            f'Project details:\n{details}\n'
        )
        port = int(os.environ.get('SMTP_PORT', '587'))
        use_tls = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
        with smtplib.SMTP(host, port, timeout=12) as server:
            if use_tls:
                server.starttls()
            if username:
                server.login(username, password)
            server.send_message(message)
        return True
    except Exception:
        app.logger.exception('ZeroFeeTech SMTP notification failed; project request remains saved.')
        return False


@app.route('/contact', methods=['POST'])
def contact():
    if not check_csrf():
        abort(400, 'Refresh the page and try again.')
    name = request.form.get('name', '').strip()[:100]
    email = request.form.get('email', '').strip()[:254]
    service = request.form.get('service', 'General enquiry').strip()[:100]
    budget = request.form.get('budget', 'Not specified').strip()[:50]
    details = request.form.get('details', '').strip()[:4000]
    if len(name) < 2 or '@' not in email or len(details) < 10:
        flash('Please complete your name, valid email, and project details.', 'error')
        return redirect(url_for('index') + '#contact')
    user = current_user()
    with db() as con:
        con.execute('INSERT INTO projects(user_id,name,email,service,budget,details,status,created_at) VALUES(?,?,?,?,?,?,?,?)',
                    (user['id'] if user else None, name, email, service, budget, details, 'New', now_iso()))
    notified = send_project_notification(name, email, service, budget, details)
    if notified:
        flash('Your project request was saved and an email notification was sent to the configured studio inbox.', 'success')
    else:
        flash('Your project request was saved successfully. Email notifications are not configured yet, so the request is available in the admin dashboard.', 'success')
    return redirect(url_for('dashboard') if user else (url_for('index') + '#contact'))


@app.errorhandler(403)
def forbidden(_error):
    return render_template('error.html', code=403, heading='Access restricted', message='This page is only available to the ZeroFeeTech administrator.'), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template('error.html', code=404, heading='Page not found', message='That page may have moved. Return to the ZeroFeeTech home page.'), 404


init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
