"""
Planning stage of the autonomous agent.

Given a raw natural-language request, ask the LLM to:
  1. Classify what kind of business document is being requested
  2. Propose a title
  3. Break the work into an explicit TODO / task list
  4. Propose the section outline for the document

This is the "autonomous planning" part of the assignment: the agent
decides for itself what needs to be done rather than following a
hardcoded script.
"""

from agent.llm_client import llm_client

VALID_DOC_TYPES = [
    "proposal", "meeting_minutes", "project_plan", "business_report",
    "technical_design", "sop", "product_spec",
]

PLAN_SYSTEM_PROMPT = """MODE=PLAN
You are an autonomous planning agent. Your job is to read a user's request
for a business document and produce a structured execution plan.

You must respond with ONLY a valid JSON object (no markdown, no commentary)
with exactly this shape:

{
  "doc_type": one of ["proposal","meeting_minutes","project_plan","business_report","technical_design","sop","product_spec"],
  "title": "a concise, professional document title",
  "reasoning": "1-2 sentences on why you chose this doc_type and structure",
  "tasks": [
     {"step": 1, "action": "short description of the task", "status": "planned"},
     ... 4 to 7 tasks total, covering: understanding the request, outlining
     sections, generating content per section, assembling the document,
     and producing a final summary ...
  ],
  "sections": ["Section Name 1", "Section Name 2", ...]
}

Pick between 5 and 9 sections appropriate for the chosen doc_type. Use
mock/illustrative data where the request doesn't supply concrete details
(e.g. plausible dates, names, numbers) and note that clearly is fine.
"""


def create_plan(user_request: str) -> dict:
    user_prompt = f"User request:\n\"\"\"\n{user_request}\n\"\"\"\n\nProduce the JSON execution plan now."
    plan = llm_client.complete_json(PLAN_SYSTEM_PROMPT, user_prompt)

    # --- Defensive normalization, in case the LLM deviates slightly ---
    if plan.get("doc_type") not in VALID_DOC_TYPES:
        plan["doc_type"] = "business_report"
    if not plan.get("title"):
        plan["title"] = "Generated Document"
    if not plan.get("sections"):
        plan["sections"] = ["Overview", "Details", "Conclusion"]
    if not plan.get("tasks"):
        plan["tasks"] = [
            {"step": 1, "action": "Analyze request", "status": "planned"},
            {"step": 2, "action": "Generate content", "status": "planned"},
            {"step": 3, "action": "Assemble document", "status": "planned"},
        ]

    return plan
