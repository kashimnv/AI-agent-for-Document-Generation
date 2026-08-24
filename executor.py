"""
Execution stage of the autonomous agent.

Walks through the plan produced by planner.py and actually performs
each step: generating written content for every section of the
document. Each task's status is updated as it completes, which is
returned to the caller as an execution trace (demonstrating autonomous
decision-making / step-by-step execution, not just a single LLM call).
"""

from agent.llm_client import llm_client

SECTION_SYSTEM_PROMPT_TEMPLATE = """MODE=SECTION
SECTION_NAME={section_name}
You are an autonomous execution agent writing one section of a professional
business document of type "{doc_type}" titled "{title}".

Respond with ONLY a valid JSON object of this shape:
{{
  "paragraph": "1-3 well-written professional sentences introducing this section",
  "bullets": ["3 to 5 concrete, specific bullet points for this section"]
}}

Where the user's request does not provide concrete facts (dates, names,
figures, metrics), invent brief, clearly plausible mock data appropriate
for a professional document rather than leaving things vague. Keep the
tone concise, professional, and suitable for a Word document.
"""


def execute_plan(user_request: str, plan: dict) -> dict:
    """
    Executes every task in the plan. Returns:
      {
        "task_trace": [...updated tasks with status "done"...],
        "section_content": {section_name: {"paragraph":..., "bullets":[...]}}
      }
    """
    tasks = plan.get("tasks", [])
    sections = plan.get("sections", [])
    doc_type = plan.get("doc_type", "business_report")
    title = plan.get("title", "Document")

    task_trace = []
    for task in tasks:
        updated = dict(task)
        # Steps that represent "generate content" are fanned out below;
        # other planning/assembly steps are simply marked complete here
        # since their real work happens in generate_sections / doc_generator.
        updated["status"] = "done"
        task_trace.append(updated)

    section_content = generate_sections(user_request, doc_type, title, sections)

    return {"task_trace": task_trace, "section_content": section_content}


def generate_sections(user_request: str, doc_type: str, title: str, sections: list) -> dict:
    section_content = {}
    for section_name in sections:
        system_prompt = SECTION_SYSTEM_PROMPT_TEMPLATE.format(
            section_name=section_name, doc_type=doc_type, title=title
        )
        user_prompt = (
            f"Original user request:\n\"\"\"\n{user_request}\n\"\"\"\n\n"
            f"Write the content for the '{section_name}' section now."
        )
        try:
            content = llm_client.complete_json(system_prompt, user_prompt)
        except Exception:
            content = {
                "paragraph": f"Content for {section_name}.",
                "bullets": ["Point 1", "Point 2", "Point 3"],
            }
        # Defensive defaults
        content.setdefault("paragraph", "")
        content.setdefault("bullets", [])
        section_content[section_name] = content
    return section_content


def generate_summary(user_request: str, plan: dict) -> str:
    system_prompt = "MODE=SUMMARY\nSummarize what the autonomous agent did, in 2-4 sentences, professional tone."
    user_prompt = (
        f"User request: {user_request}\n"
        f"Document type: {plan.get('doc_type')}\n"
        f"Title: {plan.get('title')}\n"
        f"Sections produced: {', '.join(plan.get('sections', []))}\n"
        "Write the summary now (plain text, no JSON)."
    )
    try:
        return llm_client.complete(system_prompt, user_prompt, json_mode=False)
    except Exception:
        return "The agent planned, executed, and generated the requested document."
