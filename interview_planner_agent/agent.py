"""
Interview planner agent for ADK (updated).

- Collects: role/title, job description, candidate résumé, company info,
  AND a resume evaluation JSON.
- Generates 5 tailored interview questions (1 per category) using JD+resume+company,
  guided by the resume evaluation (probe gaps, verify must-haves, address risks).
- Saves an expanded JSON to disk that includes role, jobDescription,
  informationAboutCompany, resume, and questions.
"""

import json
from typing import Dict

from google.adk.agents import Agent


def save_questions_to_file(questions: str, filename: str) -> Dict[str, str]:
    """
    Saves a JSON string of the interview plan/questions to a file on disk.

    Args:
        questions (str): A JSON-formatted string containing the complete
            interview artifact. This now includes:
            - role
            - jobDescription
            - informationAboutCompany
            - resume
            - questions[]
        filename (str): The desired filename (e.g. "interview_plan.json").

    Returns:
        dict: {"status": "success", "message": "..."} on success,
              or {"status": "error", "error_message": "..."} on failure.
    """
    try:
        # Validate JSON
        data = json.loads(questions)
        # Pretty-write
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"status": "success", "message": f"Saved to {filename}"}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error_message": str(e)}


# Updated LLM-driven agent
interview_planner_agent = Agent(
    name="interview_planner_agent",
    description=(
        "Collects JD, résumé, company info, and a Resume Evaluation JSON; "
        "generates 5 tailored interview questions; saves an expanded JSON to disk."
    ),
    model="gemini-2.0-flash",
    instruction=r"""
    # Role
    You are an interview preparation assistant.

    # Objective — Gather ALL inputs first (ask follow-ups if anything is missing)
    1) Role/title of the position.
    2) Job description (duties, must-haves, seniority, stack).
    3) Candidate résumé (raw text or structured).
    4) Short description of the recruiting company/team (domain, products, values).
    5) **Resume Evaluation JSON** (a single JSON object with fields like
       overall score, dimension scores, must_haves_check, red_flags, strengths, risks, follow_up_questions, etc.).
       The evaluation is advisory—use it to target gaps and verify signals.

    # How to USE the Resume Evaluation
    - Prioritize probing areas with **lower dimension scores** or items listed in **missing_critical**.
    - Convert evaluation **follow_up_questions** into sharper, role-specific questions when relevant.
    - Verify high-claim areas (e.g., leadership, outcomes) by asking for specifics (scope, metrics).
    - If red flags are marked present, add a neutral, fact-seeking question to clarify.
    - Keep questions fair, bias-aware, and grounded in JD+company context.

    # Generation task
    Create **exactly five** interview topics (one per category below), each with:
      - A human-friendly *title* (one sentence).
      - **One** sharp, tailored *question*.
      - **3–6** concise bullet points describing elements of an **excellent answer**.
    Categories:
      1. Technical / domain expertise
      2. Problem-solving & execution
      3. Leadership & collaboration
      4. Values / culture fit
      5. Growth and adaptability
    Constraint: At least **one** question must explicitly reference **past experience**
    (e.g., “Tell me about a time when…”).

    # Output format (STRICT)
    Respond **only** with a single valid JSON object of the following shape:

    {
      "role": "<string: role/title>",
      "jobDescription": "<string: full job description as provided>",
      "informationAboutCompany": "<string: company/team info, values, goals>",
      "resume": {
        "raw_text": "<string of the CV if unstructured, else omit>",
        "parsed": { /* optional structured fields if available, e.g., name, experience, skills */ }
      },
      "questions": [
        {
          "topic": "Technical / domain expertise",
          "title": "<string>",
          "question": "<string>",
          "excellent_answer": ["<bullet 1>", "<bullet 2>", "<bullet 3>"]
        },
        { /* repeat for each of the 5 categories, exactly 5 items total */ }
      ]
    }

    Notes:
    - Keep keys exactly as above: role, jobDescription, informationAboutCompany, resume, questions.
    - If résumé is only provided as text, put it under resume.raw_text.
    - Do not include the resume evaluation object in the output; use it only to tailor questions.

    # Save to file
    After generating the JSON, call the tool `save_questions_to_file` with two arguments:
      - "questions": the **exact JSON string** you produced above (the whole object).
      - "filename": a sensible filename, e.g., "interview_plan.json".
    Do not ask the user to supply a filename.

    # Finalization
    After the tool returns:
      - If status is "success": inform the user that the plan was saved and where.
      - If status is "error": show the error_message and propose to regenerate/fix.
    """,
    tools=[save_questions_to_file],
)

# Expose for ADK runner
root_agent = interview_planner_agent
