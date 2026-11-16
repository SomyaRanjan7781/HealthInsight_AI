# HealthInsight AI

A Python + Streamlit assessment prototype for patient-record CRUD, input validation, SQLite persistence, and AI-generated non-diagnostic health remarks using the Gemini API.

> **Safety notice:** This is an educational software prototype, not a medical device or diagnostic service. AI output is informational only and must be reviewed by a qualified healthcare professional. Do not enter real patient information. The assessment's sample names and measurements should be treated as fictional test data.

## Features

- Create, read, update (email field), and delete patient records.
- Validate names, email format, dates of birth, and positive finite numeric test values.
- Accept DOB as `DD.MM.YYYY` or `DD/MM/YYYY`; reject impossible and future dates.
- Store records in SQLite with unique numeric IDs. Duplicate names and emails are permitted because the assessment includes a repeated record.
- Call the Gemini API to generate cautious, non-diagnostic remarks.
- Do not send patient name, email address, or full date of birth to Gemini. The API receives age and numeric measurements only.
- Retry AI generation if the external API is temporarily unavailable.

## Technology stack

- Python 3.10+
- Streamlit
- SQLite (`sqlite3`, built into Python)
- Google Gen AI Python SDK (`google-genai`)
- Pandas

## Project structure

```text
HealthInsight_AI/
├── app.py
├── ai_service.py
├── database.py
├── validation.py
├── requirements.txt
├── test_data.csv
├── README.md
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
└── tests/
    └── test_validation.py
```

## Run locally on Windows PowerShell

1. Extract the ZIP file.
2. Open the project folder in VS Code.
3. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

4. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Configure the Gemini API key. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, then replace the placeholder with your own key:

```toml
GEMINI_API_KEY = "YOUR_REAL_KEY"
GEMINI_MODEL = "gemini-3.8-flash"
```

Alternatively, set environment variables in PowerShell for the current terminal session:

```powershell
$env:GEMINI_API_KEY = "YOUR_REAL_KEY"
$env:GEMINI_MODEL = "gemini-3.8-flash"
```

6. Start the application:

```powershell
streamlit run app.py
```

The app normally opens at `http://localhost:8501`.

## Run validation tests

```powershell
python -m unittest discover -s tests -v
```

The tests cover the assessment's invalid email, impossible calendar date, future DOB, duplicate record allowance, date parsing, and age calculation.

## Gemini API configuration

Create or view an API key in [Google AI Studio](https://aistudio.google.com/api-keys). The app uses the official `google-genai` Python SDK and the Gemini Interactions API. The default model is `gemini-3.8-flash`; set `GEMINI_MODEL` to another model available to your API key if needed.

**Never commit `.streamlit/secrets.toml`, `.env`, API keys, passwords, or credentials to GitHub.** The `.gitignore` excludes local secrets and local database files.

## Assessment test dataset

`test_data.csv` reproduces the 10 rows supplied in the Task 2 PDF. Do not modify the source values. Enter each row into the application and explain validation failures:

- Test 2: `hunter@gmail` is rejected because the domain has no dot-separated suffix.
- Test 4: `31.11.2001` is rejected because November has 30 days.
- Test 8: `19.10.2030` is a future DOB (relative to November 2026), and `Kris.wu.gmail.com` is not a valid email address.
- Test 6 repeats Test 1. It is allowed as a separate record with its own database ID.

Expected result: 7 valid rows are saved and 3 rows are rejected by validation, while all 10 supplied values remain unchanged in the demonstration.

## Important note about measurement units

The Task 2 PDF supplies numeric glucose, haemoglobin, and cholesterol values but does not specify their units, fasting status, sex, or laboratory reference ranges. For demonstration only, the AI prompt explicitly assumes glucose in mg/dL, haemoglobin in g/dL, and total cholesterol in mg/dL. These assumptions are clearly disclosed in the app and in each AI request. Confirm the actual units and clinical context before interpreting any real laboratory results.

The generated remarks are risk considerations only. The model is instructed not to diagnose, prescribe, or calculate a clinical risk score.

## Storage and deployment

SQLite stores records in `data/healthinsight.db` by default. This is persistent on the local computer between app runs. Some hosted app platforms use ephemeral filesystems; local SQLite records may be lost on a host restart unless persistent storage is configured. For the assessment, demonstrate local persistence or choose a managed persistent database before relying on hosted storage.

## Limitations

- This is a prototype and has no user authentication or role-based access control.
- It is not intended for real patient records or clinical use.
- Gemini availability, quotas, and API billing depend on the Google AI Studio project and account.
- AI-generated remarks can be incomplete or incorrect; human review is mandatory.
