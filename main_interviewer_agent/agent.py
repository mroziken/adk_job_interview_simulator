"""
main_interviewer_agent.py

Coordinator agent for the interview workflow in ADK.

Flow:
1) Try loading an interview plan JSON from disk (role, JD, company, topics with
   questions and expected bullets).
2) If not found, call the interview planner agent to create one, then save it.
3) For each topic:
   - Ask the question to the candidate (send as the agent's reply).
   - On next user turn (candidate's answer), call the completeness evaluator.
   - If completeness != "complete", ask ONE follow-up (per topic) suggested by
     the completeness evaluator; append follow-up answer to the original answer.
   - Call the rating evaluator on the final (original or augmented) answer.
4) After all topics are completed and rated, call the candidate evaluator agent
   (optionally the resume evaluator if needed) to produce a final verdict.

This agent uses function tools to load/save JSON files for plan/session and
AgentTool wrappers to call the other sub-agents.

References:
- Agent-as-a-Tool (wrapping agents so one can call another). 
- LLM agents, state & memory, and structured outputs best practices.
"""

import json
import os
from typing import Dict, Any, Optional

from google.adk.agents import Agent  # LLM agent base; ADK aliases are acceptable.
from google.adk.tools.agent_tool import AgentTool

# === Import sub-agents (ensure these modules are in your PYTHONPATH) ===
# Planner that creates the plan (role, JD, company, topics+questions+expected bullets)
from interview_planner_agent.agent import root_agent as interview_planner_agent
# Completeness evaluator
from answers_completness_evaluator_agent.agent import root_agent as completeness_agent
# Rating evaluator
from answers_rating_evaluator_agent.agent import root_agent as rating_agent
# Final candidate evaluator
from candidate_evaluator_agent.agent import root_agent as candidate_eval_agent
# Optional: resume evaluator (used if resume evaluation is not provided elsewhere)
try:
    from resume_evaluator_agent.agent import root_agent as resume_eval_agent
except Exception:  # Optional, don't hard-fail if not present
    resume_eval_agent = None


# =========================
# File I/O function tools
# =========================

def load_json_file(path: str) -> Dict[str, Any]:
    """
    Load a JSON file from disk.

    Args:
        path (str): Absolute or relative file path to a JSON file.

    Returns:
        dict: {
          "status": "success" | "error",
          "data": <parsed JSON or None>,
          "error_message": <str if error else "">
        }

    Notes:
        Used to fetch the interview plan (e.g., "interview_plan.json")
        and the running session state (e.g., "interview_session.json").
    """
    try:
        if not os.path.exists(path):
            return {"status": "error", "data": None, "error_message": f"File not found: {path}"}
        with open(path, "r", encoding="utf-8") as f:
            return {"status": "success", "data": json.load(f), "error_message": ""}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "data": None, "error_message": str(e)}


def save_json_file(data_json: str, path: str) -> Dict[str, str]:
    """
    Save JSON content (string) to a file on disk.

    Args:
        data_json (str): A JSON-formatted string to be saved.
        path (str): Destination filename, e.g., "interview_plan.json" or "interview_session.json".

    Returns:
        dict: {"status": "success"|"error", "message"?: str, "error_message"?: str}

    Guidance for the LLM:
        - Always pass a valid JSON string (not Python dict repr).
        - Use this to persist the plan (after generating via planner agent)
          and to persist the evolving interview session.
    """
    try:
        parsed = json.loads(data_json)  # validate
        with open(path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        return {"status": "success", "message": f"Saved to {path}"}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error_message": str(e)}


def update_session_append_answer(session_path: str, topic_id: str, question_id: str,
                                 original_answer: str, followup_answer: Optional[str],
                                 completeness: Dict[str, Any], rating: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Append or update an answer record in the session JSON.

    Args:
        session_path (str): Path to the session JSON file (e.g., "interview_session.json").
        topic_id (str): Identifier for the topic.
        question_id (str): Identifier for the question within the topic.
        original_answer (str): Candidate's initial answer text.
        followup_answer (Optional[str]): Candidate's follow-up answer (if asked).
        completeness (dict): Result from answers_completeness_evaluator_agent.
        rating (Optional[dict]): Result from answer_rating_evaluator_agent (may be None on first pass).

    Returns:
        dict: {"status": "success"|"error", "data"?: dict, "error_message"?: str}

    Behavior:
        - If session file doesn't exist, create a new one with minimal structure.
        - Maintain a list under session["answers"] with per-question records.
    """
    try:
        session: Dict[str, Any]
        if os.path.exists(session_path):
            with open(session_path, "r", encoding="utf-8") as f:
                session = json.load(f)
        else:
            session = {
                "current_topic_index": 0,
                "asked_followup_for_topic": {},  # topic_id -> bool
                "answers": []
            }

        def _find_idx():
            for i, rec in enumerate(session["answers"]):
                if rec.get("topic_id") == topic_id and rec.get("question_id") == question_id:
                    return i
            return None

        idx = _find_idx()
        record = {
            "topic_id": topic_id,
            "question_id": question_id,
            "original_answer": original_answer,
            "followup_answer": followup_answer,
            "final_answer": (original_answer if not followup_answer else (original_answer + "\n\n" + followup_answer)).strip(),
            "completeness": completeness,
            "rating": rating
        }
        if idx is None:
            session["answers"].append(record)
        else:
            session["answers"][idx] = record

        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

        return {"status": "success", "data": session}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error_message": str(e)}


# =========================
# Wrap sub-agents as tools
# =========================

interview_planner_tool = AgentTool(
    agent=interview_planner_agent,
)

completeness_tool = AgentTool(
    agent=completeness_agent,
)

rating_tool = AgentTool(
    agent=rating_agent,
)

candidate_eval_tool = AgentTool(
    agent=candidate_eval_agent,
)

resume_eval_tool = None
if resume_eval_agent is not None:
    resume_eval_tool = AgentTool(
        agent=resume_eval_agent,
    )


# =========================
# Main coordinator agent
# =========================

main_interviewer_agent = Agent(
    name="main_interviewer_agent",
    description=(
        "Coordinates the interview: loads/creates plan, asks questions, evaluates "
        "completeness and ratings, and finalizes with a candidate verdict."
    ),
    model="gemini-2.0-flash",
    instruction=r"""
# Role
You are the **Main Interviewer** coordinator. You manage the whole interview lifecycle. You can:
- Load/save JSON files via tools.
- Call other agents via tools (planner, completeness, rating, candidate evaluation, optional resume evaluation).

# Inputs & files
- Plan file path: by default use "interview_plan.json". 
  The plan must include: role, job_description, company_info, and topics[] where each topic has:
    { "id": "...", "title": "...", "question": "...", "expected_bullets": ["...", ...] }
- Session file path: use "interview_session.json" to store progress:
    { "current_topic_index": int, "asked_followup_for_topic": {topic_id: bool}, "answers": [ ... ] }

# Startup behavior
1) Try `load_json_file("interview_plan.json")`.
   - If success, keep it as the active plan.
   - If not found or invalid:
       a) Call `InterviewPlanner` to gather missing inputs and generate the plan as JSON.
       b) Save via `save_json_file(plan_json, "interview_plan.json")`.
2) Initialize or load session:
   - Try `load_json_file("interview_session.json")`. If missing, create default session:
     {"current_topic_index": 0, "asked_followup_for_topic": {}, "answers": []} and save it.

# Iterative interview loop (across turns)
- You operate one question per **conversation turn** with the candidate.
- Use the session to track progress and decide the next action.

## Turn types

### Turn A: Asking a question
- If no unanswered question is pending:
  1) Select the current topic by index from plan.topics[current_topic_index].
  2) Send the **topic title** and the **question** to the candidate as your reply, clearly formatted.
  3) Do **not** call tools in this turn aside from updating session file if needed.
  4) Wait for the candidate's answer (next user turn).

### Turn B: Processing the candidate's answer
- When the user responds with an answer to the last question you asked:
  1) Call `CompletenessEvaluator` with:
     - topic (string), question (string), candidate answer (string), expected bullets (array)
  2) If completeness == "complete":
     - Set followup_answer = None.
     - Immediately call `AnswerRatingEvaluator` on the final answer (the original).
     - Call `update_session_append_answer(...)` to persist (include completeness & rating).
     - Increment current_topic_index, save session, and if more topics remain, proceed to Turn A next turn.
     - Complement user for complete answer and check if there is any other to cover in the interview
  3) If completeness != "complete":
     - If asked_followup_for_topic[topic_id] != True:
         * Ask the **single follow-up question** suggested by the completeness evaluator (ONE per topic).
         * Mark asked_followup_for_topic[topic_id] = True in session and save.
         * Wait for the candidate's follow-up (next user turn).
       Else:
         * Treat as final; call `AnswerRatingEvaluator` on the original answer; save; increment index.
         * Express gratitude for the effort and check if there is any other to cover in the interview

### Turn C: Processing the candidate's follow-up
- When the user provides the follow-up answer:
  1) Append the follow-up to the original answer.
  2) Call `AnswerRatingEvaluator` on the augmented final answer.
  3) `update_session_append_answer(...)` with follow-up and rating.
  4) Increment current_topic_index and save.
  5) xpress gratitude for the effort and check if there is any other to cover in the interview

# Completion
- When current_topic_index reaches len(plan.topics):
  1) Ensure you have arrays ready to pass into `CandidateEvaluator`:
     - company_info, role_title, job_description from the plan
     - interview_plan: [{topic, question}] derived from plan
     - answer_completeness: transform from session["answers"][i]["completeness"]
     - answer_ratings: transform from session["answers"][i]["rating"]
     - resume_eval: if provided externally or, if missing and tool available, call `ResumeEvaluator`.
  2) Call `CandidateEvaluator` with the full payload.
  3) Return ONLY the candidate evaluator's JSON verdict as your final response.

# Guardrails & style
- Be concise and professional when asking questions.
- Never ask more than one follow-up per topic.
- Never reveal internal reasoning; only ask the current question or return JSON results.
- Do not use output_schema so that you can call tools freely.

# Notes on file tools
- Use `load_json_file`/`save_json_file` for plan/session I/O.
- Use `update_session_append_answer` to persist answers (original/follow-up) with completeness & rating.


""",
    tools=[
        load_json_file,
        save_json_file,
        update_session_append_answer,
        interview_planner_tool,
        completeness_tool,
        rating_tool,
        candidate_eval_tool,
    ] + ([resume_eval_tool] if resume_eval_tool else []),
)

# Expose for ADK discovery
root_agent = main_interviewer_agent
