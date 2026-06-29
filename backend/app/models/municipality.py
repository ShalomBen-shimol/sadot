from sqlmodel import Field, SQLModel


class Municipality(SQLModel, table=True):
    """Veterinary authority (רשות וטרינרית). One row per local authority.

    A locality (יישוב) is linked to exactly one authority; the authority holds
    the municipal vet's contact used for ownership-transfer correspondence.
    """
    __tablename__ = "municipalities"

    id: int | None = Field(default=None, primary_key=True)
    city_name: str = Field(index=True)            # רשות (authority key)
    authority_name: str | None = None             # אזור / official body name
    district: str | None = None                   # לשכה (district bureau)
    vet_department_name: str | None = None
    vet_name: str | None = None                   # שם הווטרינר העירוני
    license_number: str | None = None             # מס' רישיון
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    notes: str | None = None
    is_active: bool = Field(default=True)


class Locality(SQLModel, table=True):
    """A locality (יישוב) in Israel, linked to its veterinary authority.

    Built from the CBS locality list joined to the authority list: cities/local
    councils link to themselves; localities inside a regional council link to
    that council's authority. `needs_review` marks ones we couldn't auto-assign.
    """
    __tablename__ = "localities"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)                 # שם יישוב
    name_normalized: str = Field(index=True)      # for tolerant lookup
    symbol: str | None = Field(default=None, index=True)  # סמל יישוב (CBS code)
    subdistrict: str | None = None                # נפה
    district: str | None = None                   # לשכה
    municipality_id: int | None = Field(default=None, foreign_key="municipalities.id", index=True)
    needs_review: bool = Field(default=False, index=True)
