"""
FastAPI entrypoint for the Autonomous Document Agent.

Run with:
    uvicorn main:app --reload

Then POST to http://127.0.0.1:8000/agent with JSON:
    {"request": "Create a project plan for launching a mobile banking app"}

Interactive docs (Swagger UI) at:
    http://127.0.0.1:8000/docs
"""

from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from agent.orchestrator import AgentOrchestrator

app = FastAPI(
    title="Autonomous Document Agent",
    description=(
        "Accepts a natural language request, autonomously plans the tasks "
        "required, executes them, and returns a generated Word (.docx) "
        "business document."
    ),
    version="1.0.0",
)

orchestrator = AgentOrchestrator()
OUTPUT_DIR = Path("outputs")


class AgentRequest(BaseModel):
    request: str = Field(..., min_length=3, description="Natural language request, e.g. 'Create meeting minutes for our Q3 planning call'")


class TaskItem(BaseModel):
    step: int
    action: str
    status: str


class PlanInfo(BaseModel):
    doc_type: str
    title: str
    reasoning: str
    tasks: List[TaskItem]
    sections: List[str]


class AgentResponse(BaseModel):
    summary: str
    plan: PlanInfo
    document_path: str
    download_url: str


@app.get("/")
def root():
    return {
        "service": "Autonomous Document Agent",
        "endpoints": {
            "POST /agent": "Submit a natural language request",
            "GET /download/{filename}": "Download a generated .docx file",
            "GET /docs": "Interactive API documentation",
        },
    }


@app.post("/agent", response_model=AgentResponse)
async def run_agent(payload: AgentRequest) -> Dict[str, Any]:
    if not payload.request or not payload.request.strip():
        raise HTTPException(status_code=400, detail="'request' field cannot be empty")

    try:
        result = orchestrator.run(payload.request.strip())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent failed: {exc}") from exc

    return result


@app.get("/download/{filename}")
async def download(filename: str):
    # Basic path-traversal guard
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
