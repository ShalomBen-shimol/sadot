"""Seed data: first admin, veterinary authorities + localities (national), demo dogs.

Authorities and localities are loaded from the committed data files in
`app/db/data/` (built from the national municipal-vet list joined to the CBS
locality list). Demo dogs are only seeded outside production.
"""
import json
from pathlib import Path

from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import hash_password
from app.models.dog import Dog, DogPhoto
from app.models.enums import DogGender, DogSize, DogStatus, LocationType, UserRole
from app.models.municipality import Locality, Municipality
from app.models.user import User
from app.services.municipality import normalize_name

DATA_DIR = Path(__file__).parent / "data"

DEMO_DOGS = [
    {"name": "לונה", "breed": "מעורב", "age": 2.0, "gender": DogGender.female, "size": DogSize.medium,
     "good_with_children": True, "good_with_dogs": True, "suitable_for_apartment": True,
     "public_description": "כלבה מתוקה ואוהבת, מתאימה למשפחה.", "public_area": "אזור חיפה",
     "status": DogStatus.available_for_adoption, "current_location_type": LocationType.home},
    {"name": "רקס", "breed": "לברדור מעורב", "age": 4.0, "gender": DogGender.male, "size": DogSize.large,
     "good_with_children": True, "good_with_dogs": False, "suitable_for_apartment": False,
     "public_description": "כלב נאמן ואנרגטי שאוהב מרחבים.", "public_area": "אזור יקנעם",
     "status": DogStatus.available_for_adoption, "current_location_type": LocationType.facility},
]


def _load(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def seed_authorities(session: Session) -> int:
    """Load the national list of veterinary authorities (idempotent)."""
    if session.exec(select(Municipality)).first():
        return 0
    rows = _load("authorities.json")
    for r in rows:
        session.add(Municipality(
            city_name=r["city_name"],
            authority_name=r.get("authority_body"),
            district=r.get("district"),
            vet_name=r.get("vet_name"),
            license_number=r.get("license_number"),
            email=r.get("email"),
            phone=r.get("phone"),
            is_active=True,
        ))
    session.commit()
    return len(rows)


def seed_localities(session: Session) -> int:
    """Load every Israeli locality and link it to its authority (idempotent)."""
    if session.exec(select(Locality)).first():
        return 0
    # Map authority city_name -> id for linking.
    by_name = {m.city_name: m.id for m in session.exec(select(Municipality)).all()}
    rows = _load("localities.json")
    for r in rows:
        muni_id = by_name.get(r.get("authority_city_name")) if r.get("authority_city_name") else None
        session.add(Locality(
            name=r["name"],
            name_normalized=normalize_name(r["name"]),
            symbol=r.get("symbol") or None,
            subdistrict=r.get("subdistrict"),
            district=r.get("district"),
            municipality_id=muni_id,
            needs_review=bool(r.get("needs_review")) or muni_id is None,
        ))
    session.commit()
    return len(rows)


def seed_bot_config(session: Session) -> None:
    """Seed a starter (editable) chatbot config if none exists."""
    from app.models.chat import BotConfig

    if session.exec(select(BotConfig)).first():
        return
    session.add(
        BotConfig(
            version=1,
            is_active=True,
            persona=(
                "דבר/י בעברית, בגובה העיניים ובחום. הדגש/י שהמטרה היא למצוא לכלב בית טוב, "
                "ושיש גם אפשרות של \"מסירה מהבית\" שבה הכלב נשאר עם הבעלים בינתיים."
            ),
            knowledgebase=(
                "מסלולים: מסירה לפנסיון, או 'מסירה מהבית' — מנוי חודשי של 1,000 ₪ שבו הכלב נשאר "
                "בבית הבעלים ומוצג לאימוץ; לאחר כ-7 חודשים אפשר להמיר למסירה מלאה לפנסיון."
            ),
            model="claude-opus-4-8",
        )
    )
    session.commit()


def seed(session: Session) -> None:
    # First admin
    admin = session.exec(select(User).where(User.email == settings.first_admin_email)).first()
    if not admin:
        session.add(
            User(
                name=settings.first_admin_name,
                email=settings.first_admin_email,
                role=UserRole.admin,
                password_hash=hash_password(settings.first_admin_password),
            )
        )
        session.commit()

    seed_authorities(session)
    seed_localities(session)
    seed_bot_config(session)

    from app.services.workflow import seed_workflows

    seed_workflows(session)

    # Demo dogs only outside production.
    if settings.environment != "production" and not session.exec(select(Dog)).first():
        for d in DEMO_DOGS:
            dog = Dog(**d)
            session.add(dog)
            session.commit()
            session.refresh(dog)
            session.add(DogPhoto(dog_id=dog.id, file_url="https://placedog.net/600/400", is_primary=True))
        session.commit()


def seed_default() -> None:
    from app.core.database import engine

    with Session(engine) as session:
        seed(session)
