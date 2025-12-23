import logging
import asyncio
from sqlalchemy.orm import Session
from app.models.member import Member
from app.services.external_tfshopAPI import TFShopAPIClient
from app.services.external_ntnuiAPI import NTNUIAPIClient
from datetime import datetime, date
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class MemberSyncService:
    """Service for syncing members from external sources"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tf_client = TFShopAPIClient()
        self.ntnui_client = NTNUIAPIClient()
    
    async def sync_members_from_external(self, tf_data: List[Dict] = None, ntnui_data: List[Dict] = None) -> dict:
        """
        Sync members from external APIs or provided data
        
        Args:
            tf_data: List of TF member data (optional, for testing - skips API call)
            ntnui_data: List of NTNUI member data (optional, for testing - skips API call)
        
        Returns:
            dict: Sync result with status and count
        """
        try:
            logger.info("Starting member sync from external APIs")
            
            # Fetch data from both APIs in parallel (if not provided for testing)
            if tf_data is None or ntnui_data is None:
                logger.info("Fetching data from external APIs in parallel...")
                
                # Run both API calls concurrently
                tf_task = self.tf_client.get_members() if tf_data is None else None
                ntnui_task = self.ntnui_client.get_members() if ntnui_data is None else None
                
                tasks = []
                if tf_task:
                    tasks.append(tf_task)
                if ntnui_task:
                    tasks.append(ntnui_task)
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    result_index = 0
                    if tf_data is None:
                        if isinstance(results[result_index], Exception):
                            logger.error(f"TF Shop API error: {results[result_index]}")
                            tf_data = []
                        else:
                            tf_data = results[result_index]
                        result_index += 1
                    
                    if ntnui_data is None:
                        if isinstance(results[result_index], Exception):
                            logger.error(f"NTNUI API error: {results[result_index]}")
                            ntnui_data = []
                        else:
                            ntnui_data = results[result_index]
            
            # Ensure we have data lists
            tf_data = tf_data or []
            ntnui_data = ntnui_data or []
            
            logger.info(f"Processing {len(tf_data)} TF members and {len(ntnui_data)} NTNUI members")
            
            # Merge data from both sources by phone number
            members_dict = {}
            
            # Process TF data
            for entry in tf_data:
                phone = entry.get("phone")
                if phone:
                    members_dict[phone] = {
                        "telephone_number": phone,
                        "name": f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip(),
                        "email": entry.get("email", ""),
                        "tf_valid_until": entry.get("tf_valid_until"),
                        "ntnui_valid_until": None
                    }
            
            # Process NTNUI data - merge with existing or create new
            for entry in ntnui_data:
                phone = entry.get("phone")
                if phone:
                    if phone in members_dict:
                        # Update existing entry with NTNUI data
                        members_dict[phone]["ntnui_valid_until"] = entry.get("ntnui_valid_until")
                        # Update name/email if not present from TF
                        if not members_dict[phone]["name"]:
                            members_dict[phone]["name"] = f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip()
                        if not members_dict[phone]["email"]:
                            members_dict[phone]["email"] = entry.get("email", "")
                    else:
                        # Create new entry from NTNUI data
                        members_dict[phone] = {
                            "telephone_number": phone,
                            "name": f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip(),
                            "email": entry.get("email", ""),
                            "tf_valid_until": None,
                            "ntnui_valid_until": entry.get("ntnui_valid_until")
                        }
            
            # Calculate validity and sync to database
            today = date.today()
            synced_count = 0
            updated_count = 0
            created_count = 0
            
            for phone, member_data in members_dict.items():
                tf_valid_until = member_data.get("tf_valid_until")
                ntnui_valid_until = member_data.get("ntnui_valid_until")
                
                # Calculate validity based on expiry dates
                tf_valid = tf_valid_until >= today if tf_valid_until else False
                ntnui_valid = ntnui_valid_until >= today if ntnui_valid_until else False
                
                # Check if member exists
                existing_member = self.get_member_by_id(phone)
                
                if existing_member:
                    # Update existing member
                    existing_member.name = member_data["name"]
                    existing_member.email = member_data["email"]
                    existing_member.tf_valid = tf_valid
                    existing_member.tf_valid_until = tf_valid_until
                    existing_member.ntnui_valid = ntnui_valid
                    existing_member.ntnui_valid_until = ntnui_valid_until
                    existing_member.last_synced = datetime.utcnow()
                    updated_count += 1
                    logger.debug(f"Updated member: {phone}")
                else:
                    # Create new member
                    self.create_member(
                        name=member_data["name"],
                        email=member_data["email"],
                        telephone_number=phone,
                        tf_valid=tf_valid,
                        tf_valid_until=tf_valid_until,
                        ntnui_valid=ntnui_valid,
                        ntnui_valid_until=ntnui_valid_until
                    )
                    created_count += 1
                    logger.debug(f"Created new member: {phone}")
                
                synced_count += 1
            
            self.db.commit()
            
            logger.info(f"Sync complete: {synced_count} total, {created_count} created, {updated_count} updated")
            
            return {
                "status": "success",
                "synced_count": synced_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "message": f"Member sync completed. {synced_count} members synced ({created_count} created, {updated_count} updated)."
            }
        except Exception as e:
            logger.error(f"Error syncing members: {e}", exc_info=True)
            self.db.rollback()
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_all_members(self):
        """Get all members from database"""
        return self.db.query(Member).all()
    
    def get_member_by_id(self, telephone_number: str):
        """Get a specific member by telephone number (primary key)"""
        return self.db.query(Member).filter(Member.telephone_number == telephone_number).first()
    
    def create_member(self, name: str, email: str, telephone_number: str = None, tf_valid: bool = False, tf_valid_until: date = None, ntnui_valid: bool = False, ntnui_valid_until: date = None) -> Member:
        """Create a new member"""
        member = Member(
            name=name,
            email=email,
            telephone_number=telephone_number,
            tf_valid=tf_valid,
            tf_valid_until=tf_valid_until,
            ntnui_valid=ntnui_valid,
            ntnui_valid_until=ntnui_valid_until
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
