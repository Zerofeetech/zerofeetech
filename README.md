# ZeroFeeTech — Free-first digital studio

A responsive Flask starter for a digital services studio and browser-based productivity tools.

## Included
- Responsive homepage, services, contact, authentication, dashboard and admin pages
- SQLite signup/login with Werkzeug password hashing
- Project enquiry form saved to SQLite and visible in the admin dashboard
- Four browser-based text-template tools (no AI API key or paid AI service required)
- Render Blueprint configuration

## Local run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Render deployment
1. Upload the contents of this folder to the repository root (keep a backup of the old version first).
2. In Render, confirm the service root directory is blank and the start command is `gunicorn app:app --workers 2 --threads 4 --timeout 120`.
3. Set `ADMIN_EMAIL=admin@zerofeetech.com` and a strong `SECRET_KEY`. `render.yaml` provides defaults for the other settings.
4. Deploy and test the homepage, signup, login, contact form and admin route.

## Important free-tier limitations
- The included tools create structured templates in the browser; they are not connected to a generative AI model.
- Contact form submissions are stored in the app database; outbound email notifications are not configured.
- Render free instances may sleep and their local filesystem is ephemeral. The included `/tmp` SQLite database is suitable for a demo, not durable production data. Use a persistent database before relying on long-term account or enquiry storage.
- Never publish `.env`, database files, passwords, or secret keys.

## Admin access
Create an account using `admin@zerofeetech.com`. The admin page checks the signed-in email against `ADMIN_EMAIL`. Set a strong password and keep account credentials private.
