
# DocIntel — AI Engineer Internship Case Study

An end-to-end Document Intelligence prototype for the four required financial document categories:

- Invoice
- Balance Sheet
- Profit & Loss
- Cash Flow Statement

The implementation follows the assessment's required flow: upload → file validation → text extraction/OCR → structured extraction → financial validation → evidence/metadata → persistent database → dashboard/API.

## Why this design

- **FastAPI**: typed REST API with automatic Swagger/OpenAPI at `/docs`.
- **PyMuPDF**: native PDF text extraction and page counting.
- **Tesseract/Pillow**: OCR path for scanned PDFs and JPG/PNG. Tesseract is optional at runtime; the application fails gracefully if it is unavailable.
- **Optional Gemini**: set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` to enable LLM-assisted extraction. Without a key, the deterministic parser still provides a working local/deployed baseline.
- **SQLite**: zero-configuration local-development database.
- **PostgreSQL**: recommended for deployment because Render web-service filesystems are ephemeral. The same repository layer supports both SQLite and PostgreSQL (for example Supabase).
- **Vanilla HTML/CSS/JS**: directly satisfies the assessment requirement without a separate React/Node frontend.

## Project structure

```text
project-root/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/documents.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── repositories/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── templates/
│   └── static/
├── docs/
├── sample_outputs/
├── .env.example
├── render.yaml
└── README.md
```

## Local setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Open `http://127.0.0.1:8000/dashboard`.

Swagger: `http://127.0.0.1:8000/docs` (includes a **Back to Dashboard** button)

Health: `http://127.0.0.1:8000/api/v1/health`

## OCR setup

The Docker image installs the native **Tesseract OCR** binary and the Python dependency `pytesseract`, so scanned PDFs/JPG/PNG files can use the OCR path after deployment.

For local development, install Tesseract separately and ensure `tesseract` is on PATH. If the binary is missing, the application fails gracefully and logs the OCR issue.

## Optional Gemini extraction

Copy `.env.example` to `.env` and configure:

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-2.5-flash
```

Never commit `.env` or API keys. The application also falls back to the deterministic extraction service if the model request fails.

## API

### POST `/api/v1/documents/process`

Multipart form fields:

- `file`: PDF/JPG/PNG
- `document_type`: `invoice | balance_sheet | profit_and_loss | cash_flow_statement`

Example:

```bash
curl -X POST http://localhost:8000/api/v1/documents/process \
  -F "file=@sample_invoice.pdf" \
  -F "document_type=invoice"
```

### GET `/api/v1/documents/{document_name}`

Returns the latest stored result for the filename.

### GET `/api/v1/documents`

Returns dashboard records.

### GET `/api/v1/health`

Returns service health.

## Structured response

The response contains:

- document name/type
- processing status
- file validation
- complete extracted-data object
- evidence/page number when available
- financial validation checks with formula, operands, calculated value, reported value, variance and status
- processing metadata including OCR/LLM usage and processing time

Missing fields are represented by `null` rather than invented values.

## Financial validation

A tolerance of `1.0` is used for currency reconciliation in this prototype.

Implemented checks:

- Invoice: subtotal + tax − discount ≈ total; line-item sum ≈ subtotal when line items are detected.
- Balance Sheet: liabilities + equity ≈ assets.
- Profit & Loss: revenue − COGS ≈ gross profit; gross profit − operating expenses ≈ operating profit; operating profit − tax ≈ net profit.
- Cash Flow: operating + investing + financing ≈ net change; opening cash + net change ≈ closing cash.

If required source fields are absent, the result is `NOT_APPLICABLE` rather than inventing values.

## Testing

```bash
pytest backend/tests -q
```

The repository includes a test `conftest.py` so this command works from the project root.

Tests cover file validation, financial calculation/extraction and API health.

## Deployment

### Recommended: Render + persistent PostgreSQL

The included `render.yaml` and `backend/Dockerfile` are ready for a Render Docker Web Service. The Docker image also installs Tesseract so scanned documents are supported in the deployed environment.

For persistent evaluation storage, use a managed PostgreSQL database such as Supabase and provide its connection string as `DATABASE_URL`. The application automatically uses PostgreSQL when `DATABASE_URL` starts with `postgres://` or `postgresql://`; otherwise it uses SQLite for local development.

#### Render deployment steps

1. Push the complete repository to a **public GitHub repository**.
2. In Render, create a **New Web Service** and connect the GitHub repository.
3. Select **Docker**. Render can use the included `backend/Dockerfile`.
4. Set the required environment variable:
   - `DATABASE_URL` = your persistent PostgreSQL connection string.
5. Keep these runtime variables as configured by `render.yaml` or set them manually:
   - `OCR_ENABLED=true`
   - `MAX_PAGES=3`
   - `MAX_FILE_SIZE_MB=15`
   - `LLM_PROVIDER=none` (or `gemini` if you add a valid Gemini key)
6. Deploy and wait for the health check to pass.
7. Verify:
   - Dashboard: `https://YOUR-SERVICE.onrender.com/dashboard`
   - Health: `https://YOUR-SERVICE.onrender.com/api/v1/health`
   - Swagger: `https://YOUR-SERVICE.onrender.com/docs`
8. The Swagger page includes a **Back to Dashboard** navigation button.

### Database choice

For a short assessment, Supabase PostgreSQL is a convenient persistent PostgreSQL option. Create a database, copy its connection string, and add it to Render as `DATABASE_URL`. Do not commit the connection string to GitHub.

### Important persistence note

Do not rely on the SQLite file inside a Render web service for evaluation persistence. Render web-service filesystems are ephemeral; PostgreSQL keeps processed-document results available across restarts/redeployments. The assessment requires processed metadata and extraction results to remain available through a persistent store.

### Local fallback

No PostgreSQL is required for local testing. The application defaults to SQLite. Run:

```bash
python run.py
```

Then open `http://127.0.0.1:8000/dashboard`.

## Security / engineering notes

- Secrets are environment variables only.
- File extension, MIME type, readability and page count are validated before extraction.
- Processing exceptions are converted to controlled API errors.
- Stack traces are not returned to clients.
- Logs capture major processing stages and failures.
- Upload size is capped.
- The application does not hardcode sample document answers.

## AI/tool usage declaration

This project is designed to be developed with permitted AI coding assistants such as ChatGPT, Claude, Gemini, Copilot or Cursor. The final candidate should honestly document which tools they personally used and which generated/modified sections they understand.

## Known limitations

1. The deterministic fallback parser is intentionally conservative and depends on readable labels/layouts.
2. OCR quality depends on Tesseract installation and source image quality.
3. Generic table extraction is not a full layout-aware table parser.
4. Comparative-year statement validation is strongest when a model provider is enabled or the source follows recognizable label/value patterns.
5. SQLite is appropriate for a prototype but PostgreSQL is preferable for production.
6. Authentication, rate limiting and antivirus/content scanning would be required for a production public service.

## Production improvements

- Use PostgreSQL with migrations.
- Add object storage for original files and retention policies.
- Use a managed OCR/document AI provider or layout-aware model.
- Add asynchronous job processing for large workloads.
- Add authentication, rate limiting and audit trails.
- Add model-output schema validation and field-level provenance.
- Add evaluation datasets and extraction-quality metrics.
- Add monitoring/tracing and alerting.

## Assessment deliverables

See `docs/architecture.png`, `docs/solution_presentation.pdf` and `sample_outputs/`.
