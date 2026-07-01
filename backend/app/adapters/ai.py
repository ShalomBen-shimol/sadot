"""Conversation-engine AI abstraction.

Phase-1 default = a deterministic Mock that runs a scripted surrender intake, so
the whole chatbot works (and is tested) without an API key. A real Claude
provider (Opus 4.8 + tool use) is selected when ANTHROPIC_API_KEY is set.

Tools are executed by the caller via an ``execute_tool(name, input) -> str``
callback, so tool side-effects (DB writes) stay in the service layer and both
providers share one execution path.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from app.core.config import settings
from app.core.logging import logger

# The fields the intake gathers, in order, toward a "well-cooked" lead.
LEAD_FIELDS = ["owner_name", "owner_phone", "dog_name", "reason", "surrender_type"]

_QUESTIONS = {
    "owner_name": "מה שמך המלא?",
    "owner_phone": "מה מספר הטלפון שאפשר לחזור אליו?",
    "dog_name": "מה שם הכלב ואיזה גזע הוא?",
    "reason": "מה הביא אותך לשקול מסירה? חשוב לנו להבין כדי ללוות אותך בצורה הטובה ביותר.",
    "surrender_type": "האם נוח לך יותר במסירה לפנסיון, או ב\"מסירה מהבית\" (מנוי חודשי שבו הכלב נשאר איתך בינתיים)?",
}
_GREETING = (
    "שלום, אני כאן כדי ללוות אותך בעדינות בתהליך מסירת הכלב, ללא שיפוטיות. "
    + _QUESTIONS["owner_name"]
)

ExecuteTool = Callable[[str, dict], str]


@dataclass
class AIResult:
    reply: str
    done: bool = False


class AIProvider(ABC):
    name: str

    @abstractmethod
    def respond(
        self,
        system_prompt: str,
        history: list[dict],
        collected: dict,
        execute_tool: ExecuteTool,
    ) -> AIResult: ...


class MockAIProvider(AIProvider):
    """Scripted, deterministic intake — no LLM. `history` is the full turn list
    ([{role, content}, ...]); the newest entry is the user's latest message."""

    name = "mock"

    def respond(self, system_prompt, history, collected, execute_tool) -> AIResult:
        users = [m["content"] for m in history if m.get("role") == "user"]
        if len(users) <= 1:
            return AIResult(reply=_GREETING)

        answered_idx = len(users) - 2  # users[1] answers LEAD_FIELDS[0], etc.
        if 0 <= answered_idx < len(LEAD_FIELDS):
            execute_tool(
                "collect_lead_field",
                {"field": LEAD_FIELDS[answered_idx], "value": users[answered_idx + 1]},
            )

        next_idx = answered_idx + 1
        if next_idx < len(LEAD_FIELDS):
            return AIResult(reply=_QUESTIONS[LEAD_FIELDS[next_idx]])

        execute_tool("create_surrender_lead", {})
        return AIResult(
            reply=(
                "תודה רבה ששיתפת. פתחתי עבורך פנייה וצוות הפנסיון יחזור אליך בהקדם. "
                "אם נוח לך, אפשר כבר עכשיו לצרף צילום תעודת זהות כדי לזרז את התהליך."
            ),
            done=True,
        )


class ClaudeProvider(AIProvider):
    """Real conversation engine on Claude Opus 4.8 with tool use."""

    name = "claude"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def _tools(self) -> list[dict]:
        return [
            {
                "name": "collect_lead_field",
                "description": "Store one gathered detail about the surrenderer/dog.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string", "enum": LEAD_FIELDS},
                        "value": {"type": "string"},
                    },
                    "required": ["field", "value"],
                },
            },
            {
                "name": "create_surrender_lead",
                "description": "Create the surrender lead once name + phone are known.",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "escalate_to_human",
                "description": "Hand off to a human on distress or an animal-welfare emergency.",
                "input_schema": {
                    "type": "object",
                    "properties": {"reason": {"type": "string"}},
                    "required": ["reason"],
                },
            },
        ]

    def respond(self, system_prompt, history, collected, execute_tool) -> AIResult:
        import anthropic  # lazy: only needed when a real key is configured

        client = anthropic.Anthropic(api_key=self.api_key)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        tools = self._tools()
        reply_parts: list[str] = []
        done = False

        for _ in range(6):  # bounded tool loop
            resp = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                tools=tools,
                thinking={"type": "adaptive"},
                messages=messages,
            )
            tool_results = []
            for block in resp.content:
                if block.type == "text":
                    reply_parts.append(block.text)
                elif block.type == "tool_use":
                    if block.name == "create_surrender_lead":
                        done = True
                    out = execute_tool(block.name, dict(block.input or {}))
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": out}
                    )
            if resp.stop_reason == "tool_use" and tool_results:
                messages.append({"role": "assistant", "content": resp.content})
                messages.append({"role": "user", "content": tool_results})
                continue
            break

        return AIResult(reply="\n".join(p for p in reply_parts if p).strip(), done=done)


def get_ai_provider(model: str = "claude-opus-4-8") -> AIProvider:
    key = getattr(settings, "anthropic_api_key", "") or ""
    if key:
        return ClaudeProvider(api_key=key, model=model)
    logger.info("[AI] no ANTHROPIC_API_KEY — using MockAIProvider")
    return MockAIProvider()
