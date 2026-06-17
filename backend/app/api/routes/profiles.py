"""API routes for experiment profile management."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.tables import ExperimentProfile, User

router = APIRouter()


@router.get("", response_model=List[dict])
def list_profiles(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_presets: bool = True,
) -> List[dict]:
    """List all experiment profiles (user's custom + presets)."""
    query = select(ExperimentProfile).where(
        (ExperimentProfile.created_by_id == current_user.id) |
        (ExperimentProfile.is_preset == True if include_presets else False)
    ).order_by(ExperimentProfile.is_preset.desc(), ExperimentProfile.created_at.desc())
    
    profiles = db.exec(query).all()
    
    return [
        {
            "id": str(profile.id),
            "name": profile.name,
            "description": profile.description,
            "workflow_config": profile.workflow_config,
            "is_preset": profile.is_preset,
            "preset_type": profile.preset_type,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }
        for profile in profiles
    ]


@router.post("", response_model=dict)
def create_profile(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    name: str,
    workflow_config: dict,
    description: str = None,
) -> dict:
    """Save a new experiment profile."""
    profile = ExperimentProfile(
        name=name,
        description=description,
        workflow_config=workflow_config,
        is_preset=False,
        created_by_id=current_user.id,
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return {
        "id": str(profile.id),
        "name": profile.name,
        "description": profile.description,
        "workflow_config": profile.workflow_config,
        "is_preset": profile.is_preset,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


@router.get("/{profile_id}", response_model=dict)
def get_profile(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile_id: UUID,
) -> dict:
    """Get a specific profile by ID."""
    profile = db.get(ExperimentProfile, profile_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check access: user's own profile or preset
    if profile.created_by_id != current_user.id and not profile.is_preset:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(profile.id),
        "name": profile.name,
        "description": profile.description,
        "workflow_config": profile.workflow_config,
        "is_preset": profile.is_preset,
        "preset_type": profile.preset_type,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


@router.put("/{profile_id}", response_model=dict)
def update_profile(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile_id: UUID,
    name: str = None,
    description: str = None,
    workflow_config: dict = None,
) -> dict:
    """Update an existing profile."""
    profile = db.get(ExperimentProfile, profile_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Only owner can update (presets are read-only)
    if profile.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot modify this profile")
    
    if profile.is_preset:
        raise HTTPException(status_code=403, detail="Cannot modify preset profiles")
    
    if name is not None:
        profile.name = name
    if description is not None:
        profile.description = description
    if workflow_config is not None:
        profile.workflow_config = workflow_config
    
    from datetime import datetime
    profile.updated_at = datetime.utcnow()
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return {
        "id": str(profile.id),
        "name": profile.name,
        "description": profile.description,
        "workflow_config": profile.workflow_config,
        "is_preset": profile.is_preset,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


@router.delete("/{profile_id}")
def delete_profile(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile_id: UUID,
) -> dict:
    """Delete a profile."""
    profile = db.get(ExperimentProfile, profile_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Only owner can delete (presets cannot be deleted)
    if profile.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete this profile")
    
    if profile.is_preset:
        raise HTTPException(status_code=403, detail="Cannot delete preset profiles")
    
    db.delete(profile)
    db.commit()
    
    return {"ok": True, "message": "Profile deleted"}

# Made with Bob
