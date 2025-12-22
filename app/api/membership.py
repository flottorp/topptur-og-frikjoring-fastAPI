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


@router.get("/{member_id}")
def get_member(member_id: int, db: Session = Depends(get_db)):
    """Get a specific member by ID"""
    service = MemberSyncService(db)
    member = service.get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.post("/")
def create_member(name: str, email: str, phone: str = None, db: Session = Depends(get_db)):
    """Create a new member"""
    service = MemberSyncService(db)
    try:
        member = service.create_member(name=name, email=email, phone=phone)
        return {"status": "success", "member": member}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
def sync_members(db: Session = Depends(get_db)):
    """Sync members from external API"""
    service = MemberSyncService(db)
    result = service.sync_members_from_external()
    return result
