from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import database, models, schemas

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/signup", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Storing password as plain text for prototype
    new_user = models.User(
        username=user.username,
        email=user.email,
        password=user.password 
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.User)
def login_user(form_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid username"
        )
    
    # Plain text password check for prototype
    if user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    return user

@router.get("/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class UserUpdate(schemas.UserBase):
    pass

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Enforce unique email and username constraints
    if payload.username and payload.username != user.username:
        exists_u = db.query(models.User).filter(models.User.username == payload.username).first()
        if exists_u:
            raise HTTPException(status_code=400, detail="Username already registered")
        user.username = payload.username

    if payload.email and payload.email != user.email:
        exists_e = db.query(models.User).filter(models.User.email == payload.email).first()
        if exists_e:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = payload.email

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
