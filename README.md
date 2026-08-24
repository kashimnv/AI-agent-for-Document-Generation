# Autonomous Document Agent

A small autonomous AI agent that:
1. **Understands** a natural-language request (`POST /agent`)
2. **Plans** its own task list (classifies document type, picks a title, outlines sections)
3. **Executes** each task (generates content for every section)
4. **Produces** a polished Word (`.docx`) document as the final deliverable
5. **Reports back** a plain-language summary of what it did

It uses [Groq's free-tier API](https://console.groq.com) as the LLM by default. If no
API key is configured, it automatically falls back to a built-in offline "mock LLM"
so you can run and demo the entire pipeline with zero setup and no internet.

```
ai_agent_docgen/
├── main.py                 # FastAPI app (POST /agent, GET /download/{file})
├── agent/
│   ├── orchestrator.py     # Plan -> Execute -> Build -> Report pipeline
│   ├── planner.py          # Autonomous planning (LLM produces task list + outline)
│   ├── executor.py         # Executes each task, generates section content
│   ├── doc_generator.py    # Builds the final .docx with python-docx
│   ├── llm_client.py       # Groq client wrapper + fallback switch
│   └── mock_llm.py         # Offline deterministic fallback (no API key needed)
├── requirements.txt
├── .env.example
└── outputs/                # Generated .docx files land here
```

## 1. Setup (Windows + VS Code, Python 3.10)

Open the project folder in VS Code, then open a terminal (`` Ctrl+` ``) and run:

```powershell
# Create and activate a virtual environment
py -3.10 -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

In VS Code, select the interpreter: `Ctrl+Shift+P` → **Python: Select Interpreter** →
choose `.\venv\Scripts\python.exe`.

## 2. (Optional) Add a free LLM key

The agent works out of the box with **no key** (offline mock mode). For real,
request-specific writing quality, get a **free** Groq API key:

1. Go to https://console.groq.com/keys and sign up (free tier).
2. Copy `.env.example` to `.env`.
3. Paste your key into `GROQ_API_KEY=` in `.env`.

If `.env` is missing or the key is blank, the agent automatically uses the
offline mock LLM — the API still works end-to-end, just with generic
placeholder content instead of tailored writing.

> Want to use Ollama / LM Studio / Gemini instead? Edit `agent/llm_client.py` —
> add a `_call_ollama` (or similar) method that hits your local model's API
> and swap it in inside `complete()`. Everything else (planner, executor,
> doc_generator) stays the same since they only talk to `llm_client`.

## 3. Run the API

```powershell
uvicorn main:app --reload
```

The API is now live at http://127.0.0.1:8000 and interactive docs (Swagger UI)
are at **http://127.0.0.1:8000/docs**.

## 4. Call it

### Via Swagger UI
Go to http://127.0.0.1:8000/docs → expand `POST /agent` → **Try it out** → enter:
```json
{ "request": "Create a project plan for launching a mobile banking app in Q4" }
```
→ **Execute**.

### Via curl (PowerShell)
```powershell
curl -X POST "http://127.0.0.1:8000/agent" `
  -H "Content-Type: application/json" `
  -d '{\"request\": \"Draft a proposal to redesign our company website\"}'
```

### Via Python
```python
import requests
r = requests.post("http://127.0.0.1:8000/agent", json={
    "request": "Write meeting minutes for our Q3 planning call with 5 attendees"
})
data = r.json()
print(data["summary"])
print(data["plan"])

# Download the generated Word doc
docx = requests.get(f"http://127.0.0.1:8000{data['download_url']}")
with open("output.docx", "wb") as f:
    f.write(docx.content)
```

## 5. Example response shape

```json
{
  "summary": "The agent classified this as a project_plan, generated 7 sections...",
  "plan": {
    "doc_type": "project_plan",
    "title": "Mobile Banking App Launch Plan",
    "reasoning": "...",
    "tasks": [
      {"step": 1, "action": "Analyze user request and classify document type", "status": "done"},
      {"step": 2, "action": "Define document title and outline sections", "status": "done"},
      {"step": 3, "action": "Generate content for each section", "status": "done"},
      {"step": 4, "action": "Assemble and format the Word document", "status": "done"},
      {"step": 5, "action": "Summarize final output for the user", "status": "done"}
    ],
    "sections": ["Project Overview", "Objectives & Success Criteria", "..."]
  },
  "document_path": "outputs/mobile_banking_app_launch_plan_a1b2c3d4.docx",
  "download_url": "/download/mobile_banking_app_launch_plan_a1b2c3d4.docx"
}
```

## Supported document types

The planner autonomously classifies each request into one of:
`proposal`, `meeting_minutes`, `project_plan`, `business_report`,
`technical_design`, `sop`, `product_spec` — each with its own default
section outline (see `agent/mock_llm.py` for the reference structures used
when the LLM doesn't specify its own).

## How this demonstrates autonomous agent behavior

- **Planning**: the agent itself decides the document type, title, and
  section structure from an open-ended request — nothing is hardcoded per-request.
- **Decision-making**: it selects between 7 different document schemas and
  invents reasonable mock data when the request lacks specifics.
- **Execution**: it walks a generated task list, updating each task's status
  as it completes real work (content generation per section).
- **End-to-end delivery**: it assembles everything into a real, styled `.docx`
  file including a title page, TOC, sectioned content, and an appendix
  logging its own execution trace — and returns both a JSON summary and a
  downloadable file.

## Troubleshooting

- **`ModuleNotFoundError`**: make sure the venv is activated (`venv\Scripts\activate`)
  and you ran `pip install -r requirements.txt` inside it.
- **Port already in use**: run `uvicorn main:app --reload --port 8001` instead.
- **Groq errors**: the agent will automatically fall back to the offline mock
  LLM for that call — check the console log line "Groq call failed... Falling
  back to mock LLM" for details.
