"""
Top-level orchestrator: this is the "brain" of the autonomous agent.

Pipeline:
  1. PLAN    -> planner.create_plan()          (agent decides what to do)
  2. EXECUTE -> executor.execute_plan()        (agent does each task)
  3. BUILD   -> doc_generator.build_document() (agent produces the .docx)
  4. REPORT  -> executor.generate_summary()    (agent explains what it did)

Each stage is independent and inspectable, which is what makes this an
agent (plan -> act -> observe/report) rather than a single fixed script.
"""

import uuid
import re
from pathlib import Path

from agent.planner import create_plan
from agent.executor import execute_plan, generate_summary
from agent.doc_generator import build_document

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return slug[:40] or "document"


class AgentOrchestrator:
    def run(self, user_request: str) -> dict:
        # 1. Autonomous planning: decide doc type, title, tasks, sections
        plan = create_plan(user_request)

        # 2. Autonomous execution: perform each task, generate section content
        execution = execute_plan(user_request, plan)

        # 3. Assemble the final Word document
        file_id = uuid.uuid4().hex[:8]
        filename = f"{_slugify(plan['title'])}_{file_id}.docx"
        output_path = OUTPUT_DIR / filename

        build_document(
            output_path=output_path,
            title=plan["title"],
            doc_type=plan["doc_type"],
            user_request=user_request,
            sections=plan["sections"],
            section_content=execution["section_content"],
            task_trace=execution["task_trace"],
        )

        # 4. Final natural-language report back to the caller
        summary = generate_summary(user_request, plan)

        return {
            "summary": summary,
            "plan": {
                "doc_type": plan["doc_type"],
                "title": plan["title"],
                "reasoning": plan.get("reasoning", ""),
                "tasks": execution["task_trace"],
                "sections": plan["sections"],
            },
            "document_path": str(output_path),
            "download_url": f"/download/{filename}",
        }
