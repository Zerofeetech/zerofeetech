# ZeroFeeTech — free-first AI agency & tools starter

Responsive Flask website with service cards, transparent pricing, four prompt-building tools, and a contact section.

## Honest limitations
- Python and Flask are free to use. This project is intended to run locally without paid services.
- The AI tools create reusable prompts; they do **not** pretend to generate AI answers themselves and do not call a paid API. Copy the prompt into an AI service with a free tier of your choice. Its limits and terms are separate.
- The contact form opens the visitor's email app. It does not store messages or send email from a server.
- No domain is purchased or registered, and this ZIP does not deploy the site publicly.
- Free tiers and domain offers can change. Do not promise lifetime-free hosting, AI, email, or a custom domain.

## Run on Windows
1. Install Python from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Extract this ZIP to a folder such as `Desktop\\ZeroFeeTech`.
3. Open Command Prompt in that folder.
4. Run:
   ```bat
   py -m venv .venv
   .venv\\Scripts\\activate
   py -m pip install -r requirements.txt
   py app.py
   ```
5. Open http://127.0.0.1:5000 in your browser.
6. Stop the server with `Ctrl+C` in Command Prompt.

## Public hosting and email
You can investigate free hosting providers, but terms, limits, and account requirements may change. Public deployment is not included. `admin@zerofeetech.com` requires control of `zerofeetech.com` and a compatible email service; a promotional domain offer may require a paid site plan and renew at a cost.

## Before using with customers
Add a real contact address and privacy policy, test everything, review AI output, and do not put passwords or private client data into prompts. Add a secure backend and spam protection before collecting form submissions.
