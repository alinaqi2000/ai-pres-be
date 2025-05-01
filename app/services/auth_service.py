from fastapi import APIRouter, Depends
from fastapi import status
from sqlalchemy.orm import Session
from schemas.auth_schema import LoginRequest, Token, UserCreate
from database.init import get_db
from models.user_model import User
from utils.dependencies import verify_password, hash_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

# Register user
@router.post("/signup", response_model=Token)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=payload.email).first()
    if existing:
        raise HTTPException(status_code=403, details = "User already exists!")
    
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True
    )
    db.add(user)
    dommit()
    db.refresh(user)

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# login user
@router.post("/signin", response_model=Token)
def signin(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
       raise HTTPException(status_code=401, details="Invalid credentials")
    
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


# Get all users
@router.get("/get_all", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(User).all()

# Get a single user by ID
@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
       raise HTTPException(status_code=404, details="User not found!")
    return user

# Delete user by ID
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
       raise HTTPException(status_code=404, details="User not found!")
    
    db.delete(user)
    db.commit()
    return      