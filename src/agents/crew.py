"""CrewAI Crew definition — wires all PolitOS agents together."""

from crewai import Crew, Process, Task

from src.agents.advocate import create_advocate_agent
from src.agents.compliance import create_compliance_agent
from src.agents.moderator import create_moderator_agent
from src.agents.representative import create_representative_agent
from src.agents.summarizer import create_summarizer_agent
def run_chat(message: str) -> dict:
    """Run the citizen chat workflow.

    Flow: Message → Representative (with KB search) → Compliance check → Response
    Returns dict with response, sources, and compliance info.
    """
    representative = create_representative_agent()
    compliance = create_compliance_agent()

    respond_task = Task(
        description=(
            f"A citizen asks: \"{message}\"\n\n"
            "Search the knowledge base for relevant positions. "
            "Respond based on what you find. If no position exists, use the fallback response. "
            "Cite all sources using [KB: id], [GOV: id], or [CONST: name] format."
        ),
        expected_output="A response to the citizen with proper source citations.",
        agent=representative,
    )

    validate_task = Task(
        description=(
            "Validate the representative's response against the constitution. "
            "Check for any violations of core principles, ethical boundaries, or legal constraints. "
            "If the response is compliant, approve it. If not, flag the violations."
        ),
        expected_output=(
            "A compliance report in this format:\n"
            "compliant: true/false\n"
            "response: <the original or corrected response>\n"
            "violations: <list of violations if any>"
        ),
        agent=compliance,
        context=[respond_task],
    )

    crew = Crew(
        agents=[representative, compliance],
        tasks=[respond_task, validate_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    return {
        "response": str(result),
        "sources": [],  # Extracted from response text by caller
    }


def run_proposal_workflow(
    title: str,
    description: str,
    rationale: str,
    affected_domains: list[str],
) -> dict:
    """Run the proposal workflow.

    Flow: Proposal → Compliance check → Advocate counter-arguments → Summary
    Returns dict with compliance result, counter-arguments, and summary.
    """
    compliance = create_compliance_agent()
    advocate = create_advocate_agent()
    summarizer = create_summarizer_agent()

    proposal_text = (
        f"# Proposal: {title}\n\n"
        f"## Description\n{description}\n\n"
        f"## Rationale\n{rationale}\n\n"
        f"## Affected Domains\n{', '.join(affected_domains)}"
    )

    compliance_task = Task(
        description=(
            f"Check this proposal against the constitution:\n\n{proposal_text}\n\n"
            "Validate against core principles, ethical boundaries, and legal constraints. "
            "Report whether it is compliant and list any violations."
        ),
        expected_output=(
            "A compliance report:\n"
            "compliant: true/false\n"
            "violations: <list>\n"
            "sources: <constitutional sources checked>"
        ),
        agent=compliance,
    )

    advocate_task = Task(
        description=(
            f"Generate counter-arguments for this proposal:\n\n{proposal_text}\n\n"
            "Provide:\n"
            "1. At least 3 counter-arguments\n"
            "2. Potential unintended consequences\n"
            "3. Groups that may be negatively affected\n"
            "4. Questions the proposer should answer"
        ),
        expected_output="Structured counter-arguments with sections as specified.",
        agent=advocate,
    )

    summary_task = Task(
        description=(
            f"Create a citizen-facing summary of this proposal:\n\n{proposal_text}\n\n"
            "Include the compliance check result and counter-arguments from the previous tasks. "
            "Write in plain language, accessible to all members."
        ),
        expected_output=(
            "A plain-language summary with:\n"
            "1. What is being proposed\n"
            "2. Key arguments for\n"
            "3. Key arguments against (from advocate)\n"
            "4. Compliance status\n"
            "5. What happens next"
        ),
        agent=summarizer,
        context=[compliance_task, advocate_task],
    )

    crew = Crew(
        agents=[compliance, advocate, summarizer],
        tasks=[compliance_task, advocate_task, summary_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    return {
        "compliance": str(compliance_task.output) if compliance_task.output else "",
        "counter_arguments": str(advocate_task.output) if advocate_task.output else "",
        "summary": str(result),
    }
