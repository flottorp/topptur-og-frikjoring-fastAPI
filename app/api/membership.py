from fastapi import APIRouter, Depends, HTTPException, Body, Security
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.member import Member
from app.services.sync_members import MemberSyncService
from app.core.security import require_superuser, require_user_or_superuser
from typing import List, Dict

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("/")
def get_all_members(
    db: Session = Depends(get_db),
    api_key: str = Security(require_user_or_superuser)
):
    """Get all members (requires API key)"""
    service = MemberSyncService(db)
    members = service.get_all_members()
    return {"members": members, "count": len(members)}


@router.get("/{telephone_number}")
def get_member(
    telephone_number: str,
    db: Session = Depends(get_db),
    api_key: str = Security(require_user_or_superuser)
):
    """Get a specific member by telephone number (requires API key)"""
    service = MemberSyncService(db)
    member = service.get_member_by_id(telephone_number)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.post("/")
def create_member(
    name: str,
    email: str,
    telephone_number: str = None,
    tf_valid: bool = False,
    tf_valid_until: str = None,
    ntnui_valid: bool = False,
    ntnui_valid_until: str = None,
    db: Session = Depends(get_db),
    api_key: str = Security(require_superuser)
):
    """Create a new member (requires superuser API key)"""
    service = MemberSyncService(db)
    try:
        member = service.create_member(name=name, email=email, telephone_number=telephone_number, tf_valid=tf_valid, tf_valid_until=tf_valid_until, ntnui_valid=ntnui_valid, ntnui_valid_until=ntnui_valid_until)
        return {"status": "success", "member": member}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
def sync_members(
    tf_data: List[Dict] = Body(None),
    ntnui_data: List[Dict] = Body(None),
    db: Session = Depends(get_db),
    api_key: str = Security(require_superuser)
):
    """
    Sync members from external API or provided JSON data (requires superuser API key)
    
    Body should contain:
    - tf_data: List of TF member data (optional)
    - ntnui_data: List of NTNUI member data (optional)
    """
    service = MemberSyncService(db)
    result = service.sync_members_from_external(tf_data=tf_data, ntnui_data=ntnui_data)
    return result


@router.delete("/reset")
def reset_members(
    db: Session = Depends(get_db),
    api_key: str = Security(require_superuser)
):
    """
    Reset the members database by deleting all members (requires superuser API key)
    WARNING: This will delete all member data!
    """
    try:
        deleted_count = db.query(Member).delete()
        db.commit()
        return {
            "status": "success",
            "message": f"Database reset completed. {deleted_count} members deleted."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting database: {str(e)}")
