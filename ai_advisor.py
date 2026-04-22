"""
PawPal+ AI Advisor
Agentic workflow that analyzes a pet owner's schedule and returns structured
care advice with a confidence score and guardrail filtering.

Steps in the workflow:
  1. Build a context summary from owner/pet/task data.
  2. Call Claude to produce a structured JSON response (advice + score).
  3. Validate the response format (guardrail).
  4. Return a typed AdvisorResult to the caller.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

import anthropic

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are PawPal+ AI Advisor, a helpful pet care assistant.

You receive a summary of a pet owner's pets and scheduled tasks. Your job is to:
1. Review the schedule for gaps, imbalances, or risky patterns.
2. Suggest 2 to 3 concrete, actionable improvements.
3. Rate your own confidence in the advice from 0.0 to 1.0.

Respond ONLY with a valid JSON object that matches this schema exactly:
{
  "summary": "<one sentence describing what you observed>",
  "suggestions": ["<suggestion 1>", "<suggestion 2>", "<suggestion 3 (optional)>"],
  "confidence": <float between 0.0 and 1.0>,
  "flag": "<none | missing_vet | overloaded | incomplete_data>"
}

Rules:
- Never recommend specific medications or medical dosages.
- If the schedule looks dangerous or the data is too sparse to advise safely, set flag to the relevant value.
- Keep each suggestion under 30 words.
- Do not include any text outside the JSON object.
"""


@dataclass
class AdvisorResult:
    summary: str
    suggestions: list[str]
    confidence: float
    flag: str
    raw_response: str

    @property
    def is_safe(self) -> bool:
        return self.flag == "none"


def _build_context(owner_data: dict[str, Any]) -> str:
    """Convert owner dict to a plain-text context string for the model."""
    lines: list[str] = []
    lines.append(f"Owner: {owner_data.get('name', 'Unknown')}")
    lines.append(f"Daily time available: {owner_data.get('daily_time_available', 0)} minutes")
    prefs = owner_data.get("preferred_task_types", [])
    if prefs:
        lines.append(f"Preferences: {', '.join(prefs)}")

    pets = owner_data.get("pets", [])
    if not pets:
        lines.append("Pets: none registered")
    else:
        for pet in pets:
            lines.append(f"\nPet: {pet.get('name')} ({pet.get('species')})")
            notes = pet.get("care_notes", "")
            if notes:
                lines.append(f"  Notes: {notes}")
            tasks = pet.get("tasks", [])
            if not tasks:
                lines.append("  Tasks: none")
            else:
                for task in tasks:
                    status = "done" if task.get("completed") else "pending"
                    lines.append(
                        f"  - [{status}] {task.get('description')} at {task.get('time')} "
                        f"({task.get('duration_minutes')} min, {task.get('priority')} priority, "
                        f"{task.get('frequency')})"
                    )

    return "\n".join(lines)


def _parse_response(text: str) -> dict[str, Any]:
    """Extract JSON from the model response and validate required keys."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(line for line in lines if not line.startswith("```"))

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned non-JSON response: {exc}") from exc

    required = {"summary", "suggestions", "confidence", "flag"}
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(f"Model response missing keys: {missing}")

    if not isinstance(payload["suggestions"], list) or len(payload["suggestions"]) < 1:
        raise ValueError("suggestions must be a non-empty list")

    confidence = float(payload["confidence"])
    if not (0.0 <= confidence <= 1.0):
        raise ValueError("confidence must be between 0.0 and 1.0")

    valid_flags = {"none", "missing_vet", "overloaded", "incomplete_data"}
    if payload["flag"] not in valid_flags:
        payload["flag"] = "none"

    payload["confidence"] = confidence
    return payload


def get_care_advice(
    owner_data: dict[str, Any],
    user_question: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "claude-haiku-4-5-20251001",
) -> AdvisorResult:
    """
    Run the agentic workflow and return an AdvisorResult.

    Args:
        owner_data: Dict representation of the Owner (matches Owner.to_dict()).
        user_question: Optional free-text question from the user.
        api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        model: Claude model ID to use.

    Returns:
        AdvisorResult with advice, confidence, and guardrail flag.

    Raises:
        ValueError: If the API key is missing or the response is malformed.
    """
    resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not resolved_key:
        raise ValueError(
            "No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable "
            "or pass api_key= to get_care_advice()."
        )

    context = _build_context(owner_data)
    user_content = f"Here is the pet owner's current data:\n\n{context}"
    if user_question:
        user_content += f"\n\nAdditional question from the owner: {user_question}"

    logger.info("Calling Claude model %s for pet care advice", model)

    client = anthropic.Anthropic(api_key=resolved_key)

    message = client.messages.create(
        model=model,
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw_text = message.content[0].text
    logger.debug("Raw model response: %s", raw_text)

    try:
        parsed = _parse_response(raw_text)
    except ValueError as exc:
        logger.error("Guardrail: failed to parse model response: %s", exc)
        return AdvisorResult(
            summary="The AI advisor could not produce a valid response. Please try again.",
            suggestions=["Check that your pets and tasks are set up correctly before asking for advice."],
            confidence=0.0,
            flag="incomplete_data",
            raw_response=raw_text,
        )

    result = AdvisorResult(
        summary=parsed["summary"],
        suggestions=parsed["suggestions"],
        confidence=parsed["confidence"],
        flag=parsed["flag"],
        raw_response=raw_text,
    )
    logger.info("Advice generated. Confidence=%.2f Flag=%s", result.confidence, result.flag)
    return result
