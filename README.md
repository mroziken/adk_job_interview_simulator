# ADK Job Interview Simulator

An AI-driven, multi-agent system that simulates a full job interview lifecycle: parsing a candidate's resume, planning tailored interview questions, conducting a dynamic multi-round interview, evaluating candidate answers for completeness and quality, and producing an overall candidate assessment.

## Table of Contents
- [Features](#features)
- [Repository Structure](#repository-structure)
- [Conceptual Architecture](#conceptual-architecture)
- [Agents Overview](#agents-overview)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Evaluation Workflow](#evaluation-workflow)
- [Extending the System](#extending-the-system)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Features
- Resume ingestion & semantic profiling
- Interview plan generation (role-specific & adaptive)
- Dynamic interviewer agent that adjusts based on candidate performance
- Independent evaluators for:
  - Resume relevance
  - Candidate overall fitness
  - Answer completeness (checks coverage of required points)
  - Answer rating (qualitative / quantitative scoring)
- Modular, pluggable agent design for easy extension
- Clear separation of planning, execution, and evaluation phases

## Repository Structure
```
.
├── answers_completness_evaluator_agent/
├── answers_rating_evaluator_agent/
├── candidate_evaluator_agent/
├── interview_planner_agent/
├── main_interviewer_agent/
├── resume_evaluator_agent/
├── requirements.txt
└── .gitignore
```

(Each agent directory is expected to contain its own core logic, prompts, and helper utilities. If empty now, they can be progressively filled.)

## Conceptual Architecture

1. resume_evaluator_agent  
   - Parses and scores resume content, extracts skills, experience themes, and potential gaps.

2. interview_planner_agent  
   - Consumes the resume profile + role specification to build an interview blueprint: sections, question pools, difficulty progression.

3. main_interviewer_agent  
   - Orchestrates the live session; selects or generates questions, adapts based on prior answers.

4. answers_completness_evaluator_agent  
   - For each answer, checks whether required conceptual facets were addressed (e.g., constraints, complexity, trade-offs).

5. answers_rating_evaluator_agent  
   - Assigns qualitative & numeric scores (clarity, depth, correctness, communication).

6. candidate_evaluator_agent  
   - Produces an aggregate evaluation: strengths, risks, hire/no-hire recommendation, calibration notes.

Data flows roughly:
Resume → Planner → Interviewer ↔ Candidate Answers → Completeness + Rating Evaluators → Candidate Aggregator

## Agents Overview

| Agent | Primary Input | Output | Key Responsibility |
|-------|---------------|--------|--------------------|
| resume_evaluator_agent | Raw resume text | Structured profile | Normalize and extract candidate signals |
| interview_planner_agent | Role spec + profile | Plan JSON | Question sequence & strategy |
| main_interviewer_agent | Plan + history | Next question / transcript | Adaptive interview control |
| answers_completness_evaluator_agent | Answer + expected facets | Coverage metrics | Gap detection |
| answers_rating_evaluator_agent | Answer + context | Scores | Quality & ranking |
| candidate_evaluator_agent | All partial evaluations | Final report | Holistic decision support |

## Getting Started

### Prerequisites
- Python 3.10+ (recommended)
- Virtual environment tool (venv, poetry, or uv)
- Access keys for chosen LLM provider (e.g., OpenAI, Anthropic, etc.) if applicable.

### Installation
```bash
git clone https://github.com/mroziken/adk_job_interview_simulator.git
cd adk_job_interview_simulator

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### requirements.txt
All runtime and agent dependencies are declared there. (Open the file to see exact versions.)

## Configuration

Create a `.env` (if not already) for secrets:
```
OPENAI_API_KEY=YOUR_KEY
ANTHROPIC_API_KEY=YOUR_KEY
LOG_LEVEL=INFO
MODEL_DEFAULT=gpt-4o
```

Potential configuration patterns:
- Config class (e.g., using pydantic BaseSettings)
- Central `settings.py` consumed by each agent

## Usage Examples

(Replace placeholders with actual module / script names once implemented.)

### 1. Generate Interview Plan
```bash
python -m interview_planner_agent.plan \
  --resume data/resume.txt \
  --role-spec configs/roles/backend_engineer.yaml \
  --out build/plan.json
```

### 2. Run Interview Session (Simulated)
```bash
python -m main_interviewer_agent.run \
  --plan build/plan.json \
  --transcript build/transcript.json
```

### 3. Evaluate Answers
```bash
python -m answers_completness_evaluator_agent.eval \
  --transcript build/transcript.json \
  --out build/completeness.json
python -m answers_rating_evaluator_agent.eval \
  --transcript build/transcript.json \
  --out build/ratings.json
```

### 4. Aggregate Candidate Report
```bash
python -m candidate_evaluator_agent.aggregate \
  --resume-eval build/resume_eval.json \
  --ratings build/ratings.json \
  --completeness build/completeness.json \
  --out build/final_report.md
```

## Evaluation Workflow

1. Ingest resume → produce structured profile.
2. Build interview plan (sections: system design, coding, behavioral, role-specific).
3. Conduct interactive session; log all Q/A pairs.
4. Post-process each answer:
   - Completeness: Which required facets missing?
   - Rating: Score dimensions (accuracy, depth, articulation, reasoning).
5. Aggregate:
   - Weighted scoring matrix
   - Narrative summary
   - Recommendation threshold logic (e.g., must have >= X in core skill areas)
6. Output final decision artifact.

## Extending the System

- Add new evaluator agents by mirroring the pattern:
  - Input schema definition
  - Core evaluation logic (could be rule-based + LLM hybrid)
  - Output contract (JSON)
- Introduce multi-model routing (fast model for easy questions, advanced for complex reasoning)
- Add persistence layer (e.g., SQLite or vector DB for answer embeddings)

## Suggested Data Schemas (Draft)

Example transcript record (JSON):
```json
{
  "id": "q7",
  "question": "Explain optimistic concurrency control.",
  "answer": "It allows multiple transactions...",
  "timestamp": "2025-08-27T21:45:12Z",
  "metadata": {
    "section": "system_design",
    "difficulty": "medium"
  }
}
```

Completeness evaluation entry:
```json
{
  "answer_id": "q7",
  "required_facets": ["definition", "mechanism", "conflict_detection", "tradeoffs"],
  "covered_facets": ["definition", "mechanism"],
  "missing_facets": ["conflict_detection", "tradeoffs"],
  "coverage_score": 0.5
}
```

Rating evaluation entry:
```json
{
  "answer_id": "q7",
  "scores": {
    "technical_accuracy": 4,
    "depth": 3,
    "communication": 4,
    "confidence": 3
  },
  "overall": 3.5,
  "notes": "Missed conflict detection details."
}
```

## Roadmap (Initial)
- [ ] Define concrete data models (pydantic) for each agent I/O
- [ ] Implement baseline rule + LLM hybrid completeness evaluator
- [ ] Implement scoring rubric configuration (YAML)
- [ ] Add streaming interview mode
- [ ] Add CLI wrapper for full pipeline
- [ ] Add persistence/cache for repeated resumes
- [ ] Add front-end (optional)
- [ ] Add test suite & CI integration
- [ ] Add benchmarking harness for evaluator reliability

## Contributing
1. Fork & create feature branch: `git checkout -b feat/my-feature`
2. Follow code style (e.g., ruff / black) and type hints (mypy)
3. Include tests where applicable
4. Open a PR with:
   - Problem statement
   - Design rationale
   - Test evidence

## License
Distributed under the MIT License. See [LICENSE](./LICENSE) for details.

## Acknowledgements
- Inspiration from real-world interview processes
- Multi-agent design patterns in modern LLM orchestration
- Open-source AI tooling community

## Status
Early-stage scaffolding. Core logic to be iteratively implemented. Contributions and design suggestions welcome.

---
