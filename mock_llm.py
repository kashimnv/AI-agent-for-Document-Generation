"""
A tiny rule-based "mock LLM" so the whole autonomous agent pipeline
(planning -> execution -> document generation) can be run and tested
completely offline, with no API key. It looks for a `MODE=` marker
that the planner/executor place in the system prompt to know what
kind of response to synthesize, and does simple keyword matching on
the user's original request to pick a plausible document type.
"""

import json
import re


DOC_TYPE_KEYWORDS = {
    "proposal": ["proposal", "pitch", "bid"],
    "meeting_minutes": ["minutes", "meeting notes", "meeting summary"],
    "project_plan": ["project plan", "roadmap", "timeline"],
    "business_report": ["report", "quarterly", "analysis", "market"],
    "technical_design": ["technical design", "design doc", "architecture", "system design"],
    "sop": ["sop", "standard operating procedure", "procedure", "process document"],
    "product_spec": ["product spec", "requirements", "prd", "feature spec"],
}


def _guess_doc_type(text: str) -> str:
    text_l = text.lower()
    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_l:
                return doc_type
    return "business_report"


def _default_sections(doc_type: str) -> list:
    sections_by_type = {
        "proposal": [
            "Executive Summary", "Problem Statement", "Proposed Solution",
            "Scope of Work", "Timeline", "Budget & Pricing", "Why Choose Us",
            "Next Steps",
        ],
        "meeting_minutes": [
            "Meeting Details", "Attendees", "Agenda", "Discussion Summary",
            "Decisions Made", "Action Items", "Next Meeting",
        ],
        "project_plan": [
            "Project Overview", "Objectives & Success Criteria", "Scope",
            "Milestones & Timeline", "Resource Plan", "Risks & Mitigations",
            "Communication Plan",
        ],
        "business_report": [
            "Executive Summary", "Background", "Key Findings", "Data & Analysis",
            "Recommendations", "Conclusion",
        ],
        "technical_design": [
            "Overview", "Goals & Non-Goals", "System Architecture",
            "Detailed Design", "Data Model", "Risks & Trade-offs",
            "Rollout Plan",
        ],
        "sop": [
            "Purpose", "Scope", "Roles & Responsibilities", "Procedure Steps",
            "Tools & Resources", "Exceptions", "Revision History",
        ],
        "product_spec": [
            "Overview", "Problem & Opportunity", "Goals & Non-Goals",
            "User Stories", "Functional Requirements", "Non-Functional Requirements",
            "Open Questions",
        ],
    }
    return sections_by_type.get(doc_type, sections_by_type["business_report"])


def mock_respond(system_prompt: str, user_prompt: str, json_mode: bool) -> str:
    mode_match = re.search(r"MODE=(\w+)", system_prompt)
    mode = mode_match.group(1) if mode_match else "GENERIC"

    if mode == "PLAN":
        return _mock_plan(user_prompt)
    if mode == "SECTION":
        return _mock_section(system_prompt, user_prompt)
    if mode == "SUMMARY":
        return _mock_summary(user_prompt)

    return json.dumps({"note": "mock LLM: no handler for this mode"}) if json_mode else "Mock response."


def _mock_plan(user_prompt: str) -> str:
    doc_type = _guess_doc_type(user_prompt)

    # Pull the actual request text out from between the triple-quoted block
    # that planner.py wraps it in, rather than using the wrapper text itself.
    match = re.search(r'"""\s*(.*?)\s*"""', user_prompt, re.DOTALL)
    request_text = match.group(1).strip() if match else user_prompt.strip()
    title_guess = request_text.split("\n")[0][:80].strip()
    title_guess = re.sub(r"^(create|write|draft|generate|make|prepare)\s+(an|a|the)?\s*", "", title_guess, flags=re.IGNORECASE)

    sections = _default_sections(doc_type)

    plan = {
        "doc_type": doc_type,
        "title": f"{title_guess.capitalize()}" if title_guess else "Untitled Document",
        "reasoning": (
            f"Detected this request maps best to a '{doc_type}' style document "
            f"based on keywords in the request. Selected a standard section "
            f"structure for that document type."
        ),
        "tasks": [
            {"step": 1, "action": "Analyze user request and classify document type", "status": "planned"},
            {"step": 2, "action": "Define document title and outline sections", "status": "planned"},
            {"step": 3, "action": "Generate content for each section", "status": "planned"},
            {"step": 4, "action": "Assemble and format the Word document", "status": "planned"},
            {"step": 5, "action": "Summarize final output for the user", "status": "planned"},
        ],
        "sections": sections,
    }
    return json.dumps(plan)


def _mock_section(system_prompt: str, user_prompt: str) -> str:
    section_match = re.search(r"SECTION_NAME=(.+)", system_prompt)
    section_name = section_match.group(1).strip() if section_match else "Section"

    bullets = [
        f"Key point one relevant to {section_name.lower()}, derived from the request context.",
        f"Key point two outlining practical considerations for {section_name.lower()}.",
        f"Key point three describing expected impact or next actions for {section_name.lower()}.",
    ]
    paragraph = (
        f"This section, '{section_name}', addresses the relevant aspects of the request "
        f"in a structured way. (Note: generated by the offline mock LLM using illustrative "
        f"placeholder/mock content — connect a real LLM via GROQ_API_KEY for tailored content.)"
    )
    return json.dumps({"paragraph": paragraph, "bullets": bullets})


def _mock_summary(user_prompt: str) -> str:
    return (
        "The autonomous agent analyzed your request, built a step-by-step execution plan, "
        "generated content for each section, and compiled everything into a formatted Word "
        "document. (Offline mock LLM was used — set GROQ_API_KEY for higher-quality, "
        "request-specific writing.)"
    )
