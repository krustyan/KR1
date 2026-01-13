from datetime import date

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import (
    BudgetEntry,
    BudgetEntryCreate,
    BudgetEntryPublic,
    BudgetEntryUpdate,
    PaginatedBudgetEntries,
)

router = APIRouter(prefix="/entries", tags=["entries"])
log = structlog.get_logger()


@router.post("/", response_model=BudgetEntryPublic, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: BudgetEntryCreate, session: Session = Depends(get_session)
) -> BudgetEntryPublic:
    entry = BudgetEntry.from_orm(payload)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    log.info("entry_created", entry_id=entry.id, fecha=str(entry.fecha))
    return entry


@router.get("/", response_model=PaginatedBudgetEntries)
def list_entries(
    *,
    session: Session = Depends(get_session),
    start_date: date | None = None,
    end_date: date | None = None,
    min_coin_in: float | None = None,
    max_coin_in: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedBudgetEntries:
    query = select(BudgetEntry)

    if start_date:
        query = query.where(BudgetEntry.fecha >= start_date)
    if end_date:
        query = query.where(BudgetEntry.fecha <= end_date)
    if min_coin_in is not None:
        query = query.where(BudgetEntry.coin_in >= min_coin_in)
    if max_coin_in is not None:
        query = query.where(BudgetEntry.coin_in <= max_coin_in)

    count_result = session.exec(query.with_only_columns(func.count()).order_by(None)).one()
    total = count_result[0] if isinstance(count_result, tuple) else count_result
    entries = session.exec(query.offset(offset).limit(limit)).all()

    return PaginatedBudgetEntries(total=total, items=entries)


@router.get("/{entry_id}", response_model=BudgetEntryPublic)
def get_entry(entry_id: int, session: Session = Depends(get_session)) -> BudgetEntryPublic:
    entry = session.get(BudgetEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@router.put("/{entry_id}", response_model=BudgetEntryPublic)
def update_entry(
    entry_id: int, payload: BudgetEntryUpdate, session: Session = Depends(get_session)
) -> BudgetEntryPublic:
    entry = session.get(BudgetEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    payload_data = payload.dict(exclude_unset=True)
    for key, value in payload_data.items():
        setattr(entry, key, value)

    session.add(entry)
    session.commit()
    session.refresh(entry)
    log.info("entry_updated", entry_id=entry.id)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, session: Session = Depends(get_session)) -> None:
    entry = session.get(BudgetEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    session.delete(entry)
    session.commit()
    log.info("entry_deleted", entry_id=entry_id)
