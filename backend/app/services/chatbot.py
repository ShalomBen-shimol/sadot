"""Conversation engine: owns the system-prompt scaffold, tool execution, and the
per-message handler. Providers (Mock / Claude) only decide what to say/do; all
side-effects (collecting fields, creating leads, escalating) run here."""
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.adapters.ai import get_ai_provider
from app.models.chat import BotConfig, ChatMessage, Conversation
from app.models.dog import Dog
from app.models.enums import (
    ConversationChannel,
    ConversationGoal,
    ConversationStatus,
    SurrenderStatus,
    SurrenderType,
    TaskPriority,
    TaskStatus,
)
from app.models.person import Person
from app.models.support import Task
from app.services import surrender as surrender_service

# Non-editable safety scaffold. The owner-editable persona/knowledgebase are
# composed INTO this — they cannot override it.
SAFETY_SCAFFOLD = (
    "את/ה עוזר/ת וירטואלי/ת של פנסיון בשדות המלווה בעלי כלבים בתהליך מסירה.\n"
    "כללי יסוד שאין לחרוג מהם:\n"
    "- דבר/י באמפתיה, בעדינות וללא שיפוטיות. אנשים שמוסרים כלב לרוב במצוקה.\n"
    "- אל תבטיח/י הבטחות משפטיות/רפואיות/כספיות ואל תמציא/י מחירים או נהלים.\n"
    "- אסוף/אספי הסכמה לפני שמירת פרטים אישיים.\n"
    "- אם עולה מצוקה נפשית או חשש לרווחת בעל חיים — הפנה/י לאדם אנושי מיד "
    "(כלי escalate_to_human).\n"
    "- מטרתך: ללוות בעדינות ולאסוף את הפרטים ההכרחיים (שם, טלפון, פרטי הכלב, "
    "סיבה, סוג מסירה) ואז לפתוח פנייה (כלי create_surrender_lead).\n"
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_active_bot_config(session: Session) -> BotConfig:
    cfg = session.exec(
        select(BotConfig).where(BotConfig.is_active == True)  # noqa: E712
    ).first()
    return cfg or BotConfig(persona="", knowledgebase="", model="claude-opus-4-8")


def build_system_prompt(config: BotConfig) -> str:
    parts = [SAFETY_SCAFFOLD]
    if config.persona.strip():
        parts.append("הנחיות סגנון ומדיניות (מוגדר ע\"י ההנהלה):\n" + config.persona.strip())
    if config.knowledgebase.strip():
        parts.append("מאגר ידע (עובדות שניתן להסתמך עליהן):\n" + config.knowledgebase.strip())
    return "\n\n".join(parts)


def start_conversation(
    session: Session,
    *,
    channel: ConversationChannel = ConversationChannel.web,
    goal: ConversationGoal = ConversationGoal.surrender,
    external_id: str | None = None,
) -> Conversation:
    conv = Conversation(channel=channel, goal=goal, external_id=external_id, collected={})
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return conv


def _load_history(session: Session, conv: Conversation) -> list[dict]:
    msgs = session.exec(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.id)
    ).all()
    return [{"role": m.role, "content": m.content} for m in msgs if m.role in ("user", "assistant")]


def _parse_surrender_type(text: str | None) -> SurrenderType:
    if text and ("בית" in text or "home" in text.lower()):
        return SurrenderType.home_subscription
    return SurrenderType.facility


def _run_tool(session: Session, conv: Conversation, name: str, inp: dict) -> str:
    if name == "collect_lead_field":
        field, value = inp.get("field"), inp.get("value")
        if field:
            # Reassign so SQLAlchemy tracks the JSON change.
            conv.collected = {**(conv.collected or {}), field: value}
            session.add(conv)
            session.commit()
        return "ok"

    if name == "create_surrender_lead":
        return _create_lead(session, conv)

    if name == "escalate_to_human":
        conv.escalated = True
        conv.status = ConversationStatus.escalated
        session.add(conv)
        session.add(
            Task(
                title=f"שיחת צ'אט מוסרת דורשת מענה אנושי — שיחה #{conv.id}",
                description=str(inp.get("reason") or ""),
                status=TaskStatus.open,
                priority=TaskPriority.urgent,
            )
        )
        session.commit()
        return "escalated"

    return f"unknown tool: {name}"


def _create_lead(session: Session, conv: Conversation) -> str:
    c = conv.collected or {}
    full_name = (c.get("owner_name") or "").strip() or "ללא שם"
    first, _, last = full_name.partition(" ")
    person = Person(first_name=first or full_name, last_name=last or None, phone=c.get("owner_phone"))
    session.add(person)
    session.commit()
    session.refresh(person)

    dog_id = None
    if c.get("dog_name"):
        dog = Dog(name=str(c["dog_name"])[:120])
        session.add(dog)
        session.commit()
        session.refresh(dog)
        dog_id = dog.id

    case = surrender_service.create_case(
        session,
        {
            "surrenderer_person_id": person.id,
            "dog_id": dog_id,
            "surrender_type": _parse_surrender_type(c.get("surrender_type")),
            "reason": c.get("reason"),
            "status": SurrenderStatus.new_lead,
        },
    )
    conv.person_id = person.id
    conv.surrender_case_id = case.id
    conv.status = ConversationStatus.lead_created
    session.add(conv)
    session.commit()
    return f"lead created (surrender case #{case.id})"


def handle_message(session: Session, conv: Conversation, text: str) -> ChatMessage:
    """Persist the user's message, run the provider (which may call tools), then
    persist and return the assistant's reply."""
    session.add(ChatMessage(conversation_id=conv.id, role="user", content=text))
    session.commit()

    config = get_active_bot_config(session)
    provider = get_ai_provider(config.model)
    history = _load_history(session, conv)

    def execute_tool(name: str, inp: dict) -> str:
        return _run_tool(session, conv, name, inp)

    result = provider.respond(build_system_prompt(config), history, dict(conv.collected or {}), execute_tool)

    assistant = ChatMessage(conversation_id=conv.id, role="assistant", content=result.reply or "…")
    session.add(assistant)
    conv.updated_at = _utcnow()
    session.add(conv)
    session.commit()
    session.refresh(assistant)
    return assistant
