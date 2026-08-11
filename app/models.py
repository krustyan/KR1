from datetime import date, datetime

from sqlmodel import Field, SQLModel


class BudgetEntryBase(SQLModel):
    fecha: date = Field(index=True)
    win_tgm: float = 0
    coin_in: float = 0
    win_mesas: float = 0
    drop_mesas: float = 0
    nota: str | None = Field(default=None, description="Comentario opcional")


class BudgetEntry(BudgetEntryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class BudgetEntryCreate(BudgetEntryBase):
    pass


class BudgetEntryUpdate(SQLModel):
    fecha: date | None = None
    win_tgm: float | None = None
    coin_in: float | None = None
    win_mesas: float | None = None
    drop_mesas: float | None = None
    nota: str | None = None


class BudgetEntryPublic(BudgetEntryBase):
    id: int
    creado_en: datetime


class PaginatedBudgetEntries(SQLModel):
    total: int
    items: list[BudgetEntryPublic]
