from fastapi import APIRouter, Depends, HTTPException, Body, Security
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.member import Member
from app.services.sync_members import MemberSyncService
from app.services.external_tfshopAPI import TFShopAPIClient
from app.services.external_ntnuiAPI import NTNUIAPIClient
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


@router.post("/sync/tfshop")
async def sync_tfshop_members(
    db: Session = Depends(get_db),
    api_key: str = Security(require_superuser)
):
    """
    Fetch and sync members from TF Shop WooCommerce API (requires superuser API key)
    """
    try:
        tf_client = TFShopAPIClient()
        tf_members = await tf_client.get_members()
        
        service = MemberSyncService(db)
        result = await service.sync_members_from_external(tf_data=tf_members, ntnui_data=[])
        
        return {
            **result,
            "source": "tfshop",
            "fetched_count": len(tf_members)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing TF Shop members: {str(e)}")


@router.post("/sync/ntnui")
async def sync_ntnui_members(
    db: Session = Depends(get_db),
    api_key: str = Security(require_superuser)
):
    """
    Fetch and sync members from NTNUI API (requires superuser API key)
    """
    try:
        ntnui_client = NTNUIAPIClient()
        ntnui_members = await ntnui_client.get_members()
        
        service = MemberSyncService(db)
        result = await service.sync_members_from_external(tf_data=[], ntnui_data=ntnui_members)
        
        return {
            **result,
            "source": "ntnui",
            "fetched_count": len(ntnui_members)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing NTNUI members: {str(e)}")


@router.post("/sync/all")
async def sync_all_members(
    db: Session = Depends(get_db),
    api_key: str = Security(require_superuser)
):
    """
    Fetch and sync members from both TF Shop and NTNUI APIs (requires superuser API key)
    Fetches data from both sources in parallel for optimal performance
    """
    try:
        service = MemberSyncService(db)
        result = await service.sync_members_from_external()
        
        return {
            **result,
            "source": "all"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing all members: {str(e)}")


@router.post("/sync")
async def sync_members(
    tf_data: List[Dict] = Body(None),
    ntnui_data: List[Dict] = Body(None),
    db: Session = Depends(get_db),
    api_key: str = Security(require_superuser)
):
    """
    Sync members from provided JSON data (requires superuser API key)
    For testing purposes - use /sync/tfshop, /sync/ntnui, or /sync/all for live data
    
    Body should contain:
    - tf_data: List of TF member data (optional)
    - ntnui_data: List of NTNUI member data (optional)
    """
    service = MemberSyncService(db)
    result = await service.sync_members_from_external(tf_data=tf_data, ntnui_data=ntnui_data)
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
