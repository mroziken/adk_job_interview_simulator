"""
Answer completeness evaluator agent for the Agent Development Kit (ADK).

This module defines an LLM‐powered agent that evaluates the completeness of a
candidate's answer in an interview context.  Given a topic, the interview
question, the candidate's response and a set of expected answer bullet points,
the agent determines whether the candidate's answer is *complete*, *partial*
or *missing* relative to those expectations.  It then provides a short
explanation for its judgment and, when appropriate, suggests a follow‑up
question to gather additional information.

The agent uses natural language understanding to compare the semantic content
of the candidate's answer to the expected bullet points.  It does not rely on
external tools or data sources and responds directly in the conversation.

To integrate this agent into an ADK project, import the module and ensure
that the exported ``root_agent`` variable is discovered by the ADK runtime.
"""

from google.adk.agents import Agent


# Define the answer completeness evaluator agent.
#
# This agent interacts with the user to collect the necessary details:
#  • The topic under discussion.
#  • The interview question.
#  • The candidate's answer to that question.
#  • The expected bullet points that constitute an excellent answer.
#
# Once all inputs are provided, the agent compares the candidate's answer
# against the expected bullet points and classifies the response as
# "complete", "partial" or "missing".  It then generates a one‑sentence
# rationale describing its reasoning.  If the answer is partial or missing,
# the agent suggests a follow‑up question to elicit the missing information.
answers_completness_evaluator_agent = Agent(
    name="answers_completness_evaluator_agent",
    description=(
        "Evaluates the completeness of a candidate's answer relative to "
        "expected bullet points and provides a short rationale.  The agent "
        "collects the topic, question, candidate answer and expected points "
        "from the user, then classifies the answer as complete, partial or "
        "missing."
    ),
    model="gemini-2.0-flash",
    instruction="""
    # Role
    You are an interview answer evaluator.  Your job is to assess how
    completely a candidate's response addresses a question given a set of
    expected answer bullet points.

    # Required information
    Before you can evaluate an answer, you must collect the following from
    the user:
    1. **Topic** – the high‑level subject area (e.g. "Leadership and Team Development in AI Engineering").
    2. **Question** – the interview question posed to the candidate.
    3. **Candidate answer** – the candidate's full response to the question.
    4. **Expected answer bullet points** – three to six bullet points that
       describe what an excellent answer should include.

    Gather each of these items in a conversational manner.  If any piece
    of information is missing, ask the user specifically for it.  When
    collecting expected bullet points, accept them as a list of separate
    lines or entries.

    # Evaluation criteria
    After receiving all required information, compare the candidate's
    answer to the expected bullet points.  Use the following guidelines:

    * **Complete** – The answer covers most or all of the expected points in a
      relevant and coherent manner.  Minor omissions are acceptable if the
      core elements are addressed.
    * **Partial** – The answer addresses some, but not all, of the expected
      points.  Key elements are missing or insufficiently covered.
    * **Missing** – The answer does not meaningfully address the expected
      points; it may focus on unrelated aspects or stay at a superficial
      level.

    Base your judgment on the content and depth of the answer relative
    to each expected bullet point.  Be professional and neutral; do not make
    assumptions about intent or ability.

    # Response format
    When you have completed your assessment, respond **only** with the
    evaluation in a structured form.  Use this exact template:

    ```
    Completeness: <complete|partial|missing>
    Rationale: <one‑sentence rationale explaining your judgment>
    Follow‑up: <question to prompt further detail>  # optional, include only if completeness is partial or missing
    ```

    The **Rationale** should briefly summarise which expected points were
    addressed and which were lacking.  If the answer is *partial* or
    *missing*, suggest a **Follow‑up** question to encourage the candidate
    to elaborate on the missing elements.  Do not include a follow‑up
    section if the answer is complete.

    Do not include any additional commentary or explanation outside of this
    template.  Your response should be concise and adhere strictly to the
    structure above.
    """,
    tools=[],
)


# Expose the agent as ``root_agent`` for discovery by the ADK runner.  This
# ensures that when the project is executed, the evaluator agent is launched.
root_agent = answers_completness_evaluator_agent
