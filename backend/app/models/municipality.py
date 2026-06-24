from sqlmodel import Field, SQLModel


class Municipality(SQLModel, table=True):
    """Veterinary authority resolved by city/locality."""
    __tablename__ = "municipalities"

    id: int | None = Field(default=None, primary_key=True)
    city_name: str = Field(index=True)
    authority_name: str | None = None
    district: str | None = None
    vet_department_name: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    notes: str | None = None
    is_active: bool = Field(default=True)
