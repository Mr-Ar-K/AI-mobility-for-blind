from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import database, models, schemas

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.get("/{user_id}", response_model=List[schemas.HistoryItem])
def get_user_history(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return history items in reverse chronological order
    history_items = db.query(models.DetectionHistory)\
                      .filter(models.DetectionHistory.user_id == user_id)\
                      .order_by(models.DetectionHistory.timestamp.desc())\
                      .all()
    
    return history_items
