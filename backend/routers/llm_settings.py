from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, LLMSetting
from schemas import LLMSettingCreate, LLMSettingUpdate, LLMSetting as LLMSettingSchema
from auth import get_current_user

router = APIRouter()


@router.post("/", response_model=LLMSettingSchema)
def create_llm_setting(
    setting: LLMSettingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_setting = db.query(LLMSetting).filter(
        LLMSetting.user_id == current_user.id,
        LLMSetting.provider == setting.provider
    ).first()
    
    if db_setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setting for this provider already exists"
        )
    
    db_setting = LLMSetting(**setting.dict(), user_id=current_user.id)
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


@router.get("/", response_model=List[LLMSettingSchema])
def read_llm_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    settings = db.query(LLMSetting).filter(LLMSetting.user_id == current_user.id).all()
    return settings


@router.get("/{provider}", response_model=LLMSettingSchema)
def read_llm_setting(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    setting = db.query(LLMSetting).filter(
        LLMSetting.user_id == current_user.id,
        LLMSetting.provider == provider
    ).first()
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


@router.put("/{provider}", response_model=LLMSettingSchema)
def update_llm_setting(
    provider: str,
    setting_update: LLMSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    setting = db.query(LLMSetting).filter(
        LLMSetting.user_id == current_user.id,
        LLMSetting.provider == provider
    ).first()
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    update_data = setting_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)
    
    db.commit()
    db.refresh(setting)
    return setting


@router.delete("/{provider}")
def delete_llm_setting(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    setting = db.query(LLMSetting).filter(
        LLMSetting.user_id == current_user.id,
        LLMSetting.provider == provider
    ).first()
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    db.delete(setting)
    db.commit()
    return {"message": "Setting deleted successfully"}