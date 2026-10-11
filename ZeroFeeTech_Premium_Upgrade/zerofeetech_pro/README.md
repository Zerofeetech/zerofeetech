# ZeroFeeTech — Premium Digital Studio

A responsive Flask website for **ZeroFeeTech** with a premium dark-tech visual system, service catalogue, featured capabilities, about/process/why-us/portfolio sections, a prompt-building studio, email/password accounts, a user workspace, project-request storage, and an administrator dashboard.

## Included

- Premium responsive design for desktop, tablet and mobile; accessible navigation, reduced-motion support, scroll reveal, metadata, Open Graph tags and a branded SVG favicon.
- Nine service categories: Coding, Design, Media, Writing, Marketing, Business Support, Data, E-commerce and Technical Solutions.
- Four featured service panels and an honest portfolio section with no invented clients, reviews or project outcomes.
- Phone and email links from the supplied brief. WhatsApp and LINE buttons clearly remain unconfigured until their official URLs are added.
- Contact form with server-side validation that stores project requests in SQLite.
- Optional email notification can be configured using SMTP environment variables (see below). Without SMTP configuration, requests are stored but no email is sent.
- Email/password signup and login; passwords are stored as secure Werkzeug hashes.
- User workspace with project request history and saved prompts.
- Admin dashboard for viewing requests and users and updating project status.
- Twelve prompt-building tools. These create reusable prompts/briefs; they do not pretend to be connected to a paid AI model.
- CSRF protection for form and save endpoints, secure session cookie options, server-side admin role checks.

## Run locally (Windows)

1. Install Python 3.11 or newer.
2. Extract this ZIP into a folder such as `Desktop\\ZeroFeeTech`.
3. Open Command Prompt in that folder and run:

   ```bat
   py -m venv .venv
   .venv\\Scripts\\activate
   py -m pip install -r requirements.txt
   set SECRET_KEY=replace-with-a-long-random-secret
   set ADMIN_EMAIL=admin@zerofeetech.com
   set ADMIN_PASSWORD=choose-a-unique-strong-password
   py app.py
   ```

4. Open `http://127.0.0.1:5000`.
5. Choose **Create free account** and sign up with the exact `ADMIN_EMAIL` and `ADMIN_PASSWORD` values to create the first admin account. Keep the password private. If an account with that email already exists as a normal user, this starter does not automatically promote it; promote it securely in the database or reset the database only if you do not need its records.
6. Open `/admin` while signed in as admin.

## Render deployment

Build command:

```sh
pip install -r requirements.txt
```

Start command:

```sh
gunicorn app:app --bind 0.0.0.0:$PORT
```

Environment variables to set in Render:

- `SECRET_KEY`: unique random secret; keep private.
- `ADMIN_EMAIL`: `admin@zerofeetech.com` (the login identifier for the configured admin account).
- `ADMIN_PASSWORD`: a unique strong password; never put it in source control.
- `COOKIE_SECURE`: `true`.
- Optional `DATABASE_PATH`: path to a persistent mounted disk if your hosting plan supports one.
- Optional SMTP variables if you want email notifications: `SMTP_HOST`, `SMTP_PORT` (usually 587), `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and optionally `SMTP_USE_TLS=true`. Use credentials from a real email provider; do not use your account password.
- Optional `CONTACT_EMAIL` or `MAIL_TO` to choose where contact notifications are delivered (defaults to the supplied `waynepradip10@gmail.com` address).
- Optional `WHATSAPP_URL` and `LINE_URL` if you later configure official contact URLs. These are not automatically fabricated or enabled by the current UI.

The included `render.yaml` requests `ADMIN_PASSWORD` as a secret. Set it in the Render dashboard when prompted.

## Important production limitations

- **SQLite persistence:** local SQLite is a real working database. However, Render's free web service filesystem is ephemeral, so data can be lost on restarts/redeploys/spin-downs. Before relying on this for customer records, configure persistent storage or migrate to a managed database and backups.
- **Email address:** showing `admin@zerofeetech.com` does not create a real inbox or verify domain ownership. You must own/control the domain and configure a mailbox provider. Email/password login uses accounts stored in this app; it is not the same as having a mailbox at that address.
- **Contact email notifications:** project requests are stored even if SMTP is absent. Automatic notification only works after valid SMTP settings are configured and tested.
- **Admin setup:** `admin@zerofeetech.com` is not an admin account just because the email matches. The account gets the admin role only when the email and configured `ADMIN_PASSWORD` both match during signup.
- **AI studio:** prompt tools generate structured prompts, not completed AI output. A real AI generation feature requires a model/API integration and careful review of cost and privacy.
- **Security checklist:** before collecting real customer data, add rate limiting, email verification, password reset, database backups, audit logging, and a full production security review. Never commit secrets to GitHub.
- **Free tiers:** hosting, domain registration, mailbox, databases and third-party AI plans are separate services with their own limits.

## Main routes

- `/` — public site and prompt studio
- `/signup` — create account
- `/login` — sign in
- `/dashboard` — private workspace and project history
- `/admin` — administrator dashboard
- `/health` — health check

## Project structure

```text
app.py
requirements.txt
render.yaml
.env.example
templates/
  base.html
  index.html
  studio_section.html
  auth.html
  dashboard.html
  admin.html
  error.html
static/
  css/style.css
  css/premium.css
  js/main.js
  js/premium.js
  favicon.svg
```
