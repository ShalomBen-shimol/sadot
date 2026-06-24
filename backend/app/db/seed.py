"""Seed data: first admin, sample veterinary authorities, demo dogs."""
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import hash_password
from app.models.dog import Dog, DogPhoto
from app.models.enums import DogGender, DogSize, DogStatus, LocationType, UserRole
from app.models.municipality import Municipality
from app.models.user import User

# Partial / demo authority data — manageable from the back-office later.
MUNICIPALITIES = [
    {"city_name": "חיפה", "authority_name": "עיריית חיפה", "district": "צפון",
     "vet_department_name": "השירות הווטרינרי העירוני", "email": "vet@haifa.example", "phone": "04-0000000"},
    {"city_name": "יקנעם", "authority_name": "עיריית יקנעם עילית", "district": "צפון",
     "vet_department_name": "וטרינר רשותי", "email": "vet@yokneam.example", "phone": "04-1111111"},
    {"city_name": "תל אביב", "authority_name": "עיריית תל אביב-יפו", "district": "מרכז",
     "vet_department_name": "השירות הווטרינרי", "email": "vet@tlv.example", "phone": "03-2222222"},
    {"city_name": "ירושלים", "authority_name": "עיריית ירושלים", "district": "ירושלים",
     "vet_department_name": "המחלקה הווטרינרית", "email": "vet@jlm.example", "phone": "02-3333333"},
    {"city_name": "באר שבע", "authority_name": "עיריית באר שבע", "district": "דרום",
     "vet_department_name": "וטרינר עירוני", "email": "vet@bs.example", "phone": "08-4444444"},
]

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

    # Municipalities
    for m in MUNICIPALITIES:
        exists = session.exec(select(Municipality).where(Municipality.city_name == m["city_name"])).first()
        if not exists:
            session.add(Municipality(**m))

    # Demo dogs (only if there are none yet)
    has_dogs = session.exec(select(Dog)).first()
    if not has_dogs:
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
