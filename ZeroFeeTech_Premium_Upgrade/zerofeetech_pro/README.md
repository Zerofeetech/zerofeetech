# ZeroFeeTech Pro — Free-first digital workspace

A responsive Flask website with a premium dark interface, visible sign-up/sign-in, a saved workspace, project intake, an admin control center, and a browser-based utility suite.

## Included tools
- Basic image editor: upload, resize, rotate, brightness, contrast, saturation, export PNG. Processing is done in the browser.
- Writing templates: social caption, professional email, bio, product description, and draft checklist.
- Prompt builder for websites/apps, image generation/editing, software, marketing, writing/research, and business planning.
- Lightweight SEO content checklist.
- JSON format/validate/minify.
- Word, character, sentence and reading-time counter.
- Upper/lower/title/sentence case conversion.
- Base64 encode/decode for text.
- Simple CSV preview.
- HEX/RGB color picker and palette.
- Structured project brief generator.

## Honest capability notes
This package does **not** claim to be a full ChatGPT replacement. The included writing/prompt builders use local templates and do not call a language model. Basic image edits do not include generative fill, object removal, or AI background replacement. Real AI chat, image generation, transcription, and advanced editing require a model/API integration or another service and may have limits or costs. The included utility tools process content locally in the browser wherever indicated.

## Deploy on Render
- Runtime: Python
- Root Directory: `ZeroFeeTech_Premium_Upgrade/zerofeetech_pro` if these files remain inside that folder in the GitHub repository.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Environment variables: `SECRET_KEY` (strong random secret), `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `CONTACT_EMAIL=zerofeetech@gmail.com`, `WHATSAPP_NUMBER` (optional public business number, digits only including country code), `COOKIE_SECURE=true`.

If you move the project files to the repository root, clear Root Directory in Render instead of keeping the subfolder path. Do not store secrets in GitHub.

## Important production tasks
SQLite persistence on free hosting may be ephemeral unless a persistent disk/database is configured. Before relying on customer data, configure persistent storage, backups, email verification, password reset, rate limiting, monitoring, and automated tests. Test registration, sign-in, sign-out, project requests and admin actions after each deploy.

## Local run
Install requirements, set a secure `SECRET_KEY`, configure a private `ADMIN_PASSWORD`, then run `python app.py`.


## Assignment Studio (document upload + AI-assisted study)

- Visit `/assignment` to upload up to 8 files (PDF, DOCX, PPTX, TXT, MD, CSV, JSON, PNG, JPG, WEBP) and choose explain, solve step-by-step, outline, review, summarize, quiz, or citation-check workflow.
- Document text is extracted in memory; uploads are not written to disk by this route. Uploaded content is sent to the configured AI provider only when `GOOGLE_API_KEY` is configured. Do not upload private or confidential material.
- To enable genuine model-generated answers, create a Google AI Studio API key if your account/region has access to an applicable free tier, then add `GOOGLE_API_KEY` in Render → service → Environment. Free quotas, model availability, and provider terms can change; usage may stop when quota is exhausted. Never commit the key to GitHub. Optional `AI_MODEL` defaults to `gemini-2.5-flash`.
- Without `GOOGLE_API_KEY`, the page clearly reports that AI is not connected rather than pretending the template has solved an assignment. Scanned PDFs may not contain selectable text; OCR is not included.
- Assignment support is for learning, explanation, draft feedback and study. It does not promise detector evasion or conceal AI authorship. Students should verify facts, references, calculations, and their institution's submission policy.
