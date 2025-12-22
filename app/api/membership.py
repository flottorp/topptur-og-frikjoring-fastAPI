from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.member import Member
from app.services.sync_members import MemberSyncService

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("/")
def get_all_members(db: Session = Depends(get_db)):
    """Get all members"""
    service = MemberSyncService(db)
    members = service.get_all_members()
    return {"members": members, "count": len(members)}


@router.get("/{telephone_number}")
def get_member(telephone_number: str, db: Session = Depends(get_db)):
    """Get a specific member by telephone number"""
    service = MemberSyncService(db)
    member = service.get_member_by_id(telephone_number)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.post("/")
def create_member(name: str, email: str, telephone_number: str = None, tf_fee: bool = False, ntnui_tf_member: bool = False, db: Session = Depends(get_db)):
    """Create a new member"""
    service = MemberSyncService(db)
    try:
        member = service.create_member(name=name, email=email, telephone_number=telephone_number, tf_fee=tf_fee, ntnui_tf_member=ntnui_tf_member)
        return {"status": "success", "member": member}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
def sync_members(db: Session = Depends(get_db)):
    """Sync members from external API"""
    service = MemberSyncService(db)
    result = service.sync_members_from_external()
    return result
