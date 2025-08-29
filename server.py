# server.py
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import agents
from resume_evaluator_agent.agent import root_agent as resume_evaluator_agent
from main_interviewer_agent.agent import root_agent as main_interviewer_agent
from interview_planner_agent.agent import root_agent as interview_planner_agent
from answers_completness_evaluator_agent.agent import root_agent as completeness_agent
from answers_rating_evaluator_agent.agent import root_agent as rating_agent
from candidate_evaluator_agent.agent import root_agent as candidate_agent

# Map app_name → agent
agents = {
    "resume_evaluator_agent": resume_evaluator_agent,
    "main_interviewer_agent": main_interviewer_agent,
    "interview_planner_agent": interview_planner_agent,
    "answers_completness_evaluator_agent": completeness_agent,
    "answer_rating_evaluator_agent": rating_agent,
    "candidate_evaluator_agent": candidate_agent,
}

# Create a session service and runner for each
session_services = {name: InMemorySessionService() for name in agents}
runners = {
    name: Runner(agent=agent, app_name=name, session_service=session_services[name])
    for name, agent in agents.items()
}

# Pydantic models for request bodies
class Part(BaseModel):
    text: str

class NewMessage(BaseModel):
    role: str = Field("user")
    parts: list[Part]

class RunBody(BaseModel):
    app_name: str
    userId: str
    sessionId: str
    newMessage: NewMessage

async def ensure_session(app_name: str, user_id: str, session_id: str):
    service = session_services[app_name]
    try:
        await service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    except Exception as e:
        # ignore “already exists” errors from in‑memory backend
        if "exist" not in str(e).lower():
            raise

app = FastAPI()

@app.post("/run")
async def run(body: RunBody):
    if body.app_name not in runners:
        raise HTTPException(status_code=400, detail=f"Unknown app_name {body.app_name}")
    await ensure_session(body.app_name, body.userId, body.sessionId)
    content = types.Content(role=body.newMessage.role,
                            parts=[types.Part(text=p.text) for p in body.newMessage.parts])
    events = []
    async for ev in runners[body.app_name].run_async(
        user_id=body.userId,
        session_id=body.sessionId,
        new_message=content,
    ):
        events.append(ev.model_dump())  # collect or return only final
    return {"events": events}

@app.post("/run_sse")
async def run_sse(body: RunBody):
    if body.app_name not in runners:
        raise HTTPException(status_code=400, detail=f"Unknown app_name {body.app_name}")
    await ensure_session(body.app_name, body.userId, body.sessionId)
    content = types.Content(role=body.newMessage.role,
                            parts=[types.Part(text=p.text) for p in body.newMessage.parts])
    async def event_stream():
        async for ev in runners[body.app_name].run_async(
            user_id=body.userId,
            session_id=body.sessionId,
            new_message=content,
        ):
            yield f"data: {ev.model_dump_json()}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
