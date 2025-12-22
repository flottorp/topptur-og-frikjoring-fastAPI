import logging
from sqlalchemy.orm import Session
from app.models.member import Member
from app.services.external_apis import ExternalAPIClient
from datetime import datetime, date
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class MemberSyncService:
    """Service for syncing members from external sources"""
    
    def __init__(self, db: Session, external_api_client: ExternalAPIClient = None):
        self.db = db
        self.external_api = external_api_client
    
    def sync_members_from_external(self, tf_data: List[Dict] = None, ntnui_data: List[Dict] = None) -> dict:
        """
        Sync members from external API or provided data
        
        Args:
            tf_data: List of TF member data (optional, for testing)
            ntnui_data: List of NTNUI member data (optional, for testing)
        
        Returns:
            dict: Sync result with status and count
        """
        try:
            logger.info("Starting member sync from external API")
            
            # Merge data from both sources
            members_dict = {}
            
            # Process TF data
            if tf_data:
                for entry in tf_data:
                    billing = entry.get("billing", {})
                    phone = billing.get("phone")
                    if phone:
                        date_paid = entry.get("date_paid")
                        tf_valid_until = None
                        
                        if date_paid:
                            # Parse date and calculate expiry (1 year from payment)
                            try:
                                paid_date = datetime.fromisoformat(date_paid.replace('Z', '+00:00'))
                                # Set expiry to end of year after payment
                                tf_valid_until = date(paid_date.year + 1, 12, 31)
                            except:
                                logger.warning(f"Could not parse date_paid: {date_paid}")
                        
                        members_dict[phone] = {
                            "telephone_number": phone,
                            "name": f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip(),
                            "email": billing.get("email"),
                            "tf_valid_until": tf_valid_until,
                            "ntnui_valid_until": None
                        }
            
            # Process NTNUI data
            if ntnui_data:
                for entry in ntnui_data:
                    phone = entry.get("phone_number")
                    if phone:
                        ntnui_valid_until = None
                        expiry = entry.get("ntnui_contract_expiry_date")
                        
                        if expiry:
                            try:
                                ntnui_valid_until = datetime.strptime(expiry, "%Y-%m-%d").date()
                            except:
                                logger.warning(f"Could not parse ntnui_contract_expiry_date: {expiry}")
                        
                        if phone in members_dict:
                            # Update existing entry
                            members_dict[phone]["ntnui_valid_until"] = ntnui_valid_until
                        else:
                            # Create new entry
                            members_dict[phone] = {
                                "telephone_number": phone,
                                "name": f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip(),
                                "email": entry.get("email"),
                                "tf_valid_until": None,
                                "ntnui_valid_until": ntnui_valid_until
                            }
            
            # Calculate validity and sync to database
            today = date.today()
            synced_count = 0
            
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
                    logger.info(f"Updated member: {phone}")
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
                    logger.info(f"Created new member: {phone}")
                
                synced_count += 1
            
            self.db.commit()
            
            return {
                "status": "success",
                "synced_count": synced_count,
                "message": f"Member sync completed. {synced_count} members synced."
            }
        except Exception as e:
            logger.error(f"Error syncing members: {e}")
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
