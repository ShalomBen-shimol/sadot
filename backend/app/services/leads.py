"""Public lead intake: create the Person and open the relevant case/lead."""
from sqlmodel import Session, select

from app.models.dog import Dog
from app.models.enums import DogStatus, LocationType, SurrenderStatus
from app.models.person import Person
from app.schemas.entities import AdoptionLeadIn, SurrenderLeadIn
from app.services import adoption as adoption_service
from app.services import surrender as surrender_service
from app.services.notifications import send_whatsapp


def _get_or_create_person(session: Session, *, first_name, last_name, phone, email=None, city=None) -> Person:
    person = None
    if phone:
        person = session.exec(select(Person).where(Person.phone == phone)).first()
    if not person:
        person = Person(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            city=city,
        )
        session.add(person)
        session.commit()
        session.refresh(person)
    return person


def intake_surrender(session: Session, data: SurrenderLeadIn):
    person = _get_or_create_person(
        session,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        city=data.city,
    )

    dog = Dog(
        name=data.dog_name,
        breed=data.dog_breed,
        age=data.dog_age,
        gender=data.dog_gender,
        size=data.dog_size,
        chip_number=data.chip_number,
        is_neutered=data.is_neutered,
        is_vaccinated=data.is_vaccinated,
        medical_notes=data.medical_notes,
        behavior_notes=data.behavior_notes,
        good_with_children=data.good_with_children,
        good_with_dogs=data.good_with_dogs,
        status=DogStatus.draft,
        current_location_type=LocationType.home,
        current_owner_person_id=person.id,
        public_area=data.city,
    )
    session.add(dog)
    session.commit()
    session.refresh(dog)

    case = surrender_service.create_case(
        session,
        {
            "dog_id": dog.id,
            "surrenderer_person_id": person.id,
            "surrender_type": data.surrender_type,
            "reason": data.reason,
            "privacy_required": data.privacy_required,
            "allow_direct_contact": data.allow_direct_contact,
            "status": SurrenderStatus.new_lead,
        },
    )

    # Sensitive, empathetic first contact (mock WhatsApp).
    send_whatsapp(
        session,
        person,
        "שלום, הגעתם לפנסיון בשדות. אנחנו כאן כדי ללוות אתכם ברגישות בתהליך. "
        "נשמח להסביר את האפשרויות: מסירה לפנסיון, מסירה מהבית במנוי חודשי, או שיחה עם נציג.",
        intent="surrender_intro",
    )
    return person, case


def intake_adoption(session: Session, data: AdoptionLeadIn):
    person = _get_or_create_person(
        session,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        email=data.email,
        city=data.city,
    )
    lead = adoption_service.create_lead(
        session,
        {
            "person_id": person.id,
            "dog_id": data.dog_id,
            "preferred_size": data.preferred_size,
            "preferred_breed": data.preferred_breed,
            "has_children": data.has_children,
            "has_other_dogs": data.has_other_dogs,
            "home_type": data.home_type,
            "experience_level": data.experience_level,
            "hours_alone": data.hours_alone,
            "consent_messages": data.consent_messages,
            "consent_privacy": data.consent_privacy,
            "source": data.source,
            "notes": data.notes,
        },
    )
    if data.consent_messages:
        send_whatsapp(
            session,
            person,
            "תודה שפניתם לאמץ דרך פנסיון בשדות! נחזור אליכם עם פרטים על הכלב וסל האימוץ 🐾",
            intent="adoption_intro",
        )
    return person, lead
