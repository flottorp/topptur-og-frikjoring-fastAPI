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
    
    async def sync_from_tfshop(self) -> dict:
        """
        Sync ONLY TF Shop data - preserves all existing NTNUI fields
        """
        try:
            logger.info("🔄 Starting TF Shop sync...")
            tf_data = await self.tf_client.get_members()
            
            created_count = 0
            updated_count = 0
            today = date.today()
            
            for entry in tf_data:
                phone = entry.get('phone')
                if not phone:
                    continue
                
                tf_valid_until = entry.get('tf_valid_until')
                tf_valid = tf_valid_until >= today if tf_valid_until else False
                
                existing = self.get_member_by_id(phone)
                
                if existing:
                    # UPDATE ONLY TF FIELDS - NTNUI fields untouched!
                    existing.tf_valid = tf_valid
                    existing.tf_valid_until = tf_valid_until
                    # Only update name/email if currently empty
                    if not existing.name:
                        name = f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip()
                        existing.name = name
                    if not existing.email:
                        existing.email = entry.get('email', '')
                    existing.last_synced = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new - NTNUI fields default to False/None
                    name = f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip()
                    new_member = Member(
                        telephone_number=phone,
                        name=name,
                        email=entry.get('email', ''),
                        tf_valid=tf_valid,
                        tf_valid_until=tf_valid_until,
                        ntnui_valid=False,
                        ntnui_valid_until=None
                    )
                    self.db.add(new_member)
                    created_count += 1
            
            self.db.commit()
            logger.info(f"✅ TF Shop sync: {created_count} created, {updated_count} updated")
            
            return {
                "status": "success",
                "source": "tfshop",
                "synced_count": len(tf_data),
                "created_count": created_count,
                "updated_count": updated_count
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ TF Shop sync failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def sync_from_ntnui(self) -> dict:
        """
        Sync ONLY NTNUI data - preserves all existing TF fields
        """
        try:
            logger.info("🔄 Starting NTNUI sync...")
            ntnui_data = await self.ntnui_client.get_members()
            
            created_count = 0
            updated_count = 0
            
            for entry in ntnui_data:
                phone = entry.get('phone')
                if not phone:
                    continue
                
                # Validity comes from the group membership flag, not from a date
                ntnui_valid_until = entry.get('ntnui_valid_until')
                ntnui_valid = bool(entry.get('ntnui_valid'))
                
                existing = self.get_member_by_id(phone)
                
                if existing:
                    # UPDATE ONLY NTNUI FIELDS - TF fields untouched!
                    existing.ntnui_valid = ntnui_valid
                    existing.ntnui_valid_until = ntnui_valid_until
                    # NTNUI has priority for name/email
                    name = f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip()
                    if name:
                        existing.name = name
                    if entry.get('email'):
                        existing.email = entry.get('email')
                    existing.last_synced = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new - TF fields default to False/None
                    name = f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip()
                    new_member = Member(
                        telephone_number=phone,
                        name=name,
                        email=entry.get('email', ''),
                        tf_valid=False,
                        tf_valid_until=None,
                        ntnui_valid=ntnui_valid,
                        ntnui_valid_until=ntnui_valid_until
                    )
                    self.db.add(new_member)
                    created_count += 1
            
            self.db.commit()
            logger.info(f"✅ NTNUI sync: {created_count} created, {updated_count} updated")
            
            return {
                "status": "success",
                "source": "ntnui",
                "synced_count": len(ntnui_data),
                "created_count": created_count,
                "updated_count": updated_count
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ NTNUI sync failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def sync_all(self) -> dict:
        """
        Sync from both sources - merges data properly
        """
        try:
            logger.info("🔄 Starting full sync from both sources...")
            
            # Fetch both in parallel
            tf_data, ntnui_data = await asyncio.gather(
                self.tf_client.get_members(),
                self.ntnui_client.get_members(),
                return_exceptions=True
            )
            
            if isinstance(tf_data, Exception):
                logger.error(f"❌ TF API failed: {tf_data}")
                tf_data = []
            if isinstance(ntnui_data, Exception):
                logger.error(f"❌ NTNUI API failed: {ntnui_data}")
                ntnui_data = []
            
            # Merge by phone - TF first, NTNUI overwrites name/email
            members_dict = {}
            
            for entry in tf_data:
                phone = entry.get('phone')
                if phone:
                    members_dict[phone] = {
                        'first_name': entry.get('first_name', ''),
                        'last_name': entry.get('last_name', ''),
                        'email': entry.get('email', ''),
                        'tf_valid_until': entry.get('tf_valid_until'),
                        'ntnui_valid': False,
                        'ntnui_valid_until': None
                    }
            
            for entry in ntnui_data:
                phone = entry.get('phone')
                if not phone:
                    continue
                if phone in members_dict:
                    members_dict[phone]['ntnui_valid'] = bool(entry.get('ntnui_valid'))
                    members_dict[phone]['ntnui_valid_until'] = entry.get('ntnui_valid_until')
                    # NTNUI priority for name/email
                    if entry.get('first_name'):
                        members_dict[phone]['first_name'] = entry.get('first_name')
                    if entry.get('last_name'):
                        members_dict[phone]['last_name'] = entry.get('last_name')
                    if entry.get('email'):
                        members_dict[phone]['email'] = entry.get('email')
                else:
                    members_dict[phone] = {
                        'first_name': entry.get('first_name', ''),
                        'last_name': entry.get('last_name', ''),
                        'email': entry.get('email', ''),
                        'tf_valid_until': None,
                        'ntnui_valid': bool(entry.get('ntnui_valid')),
                        'ntnui_valid_until': entry.get('ntnui_valid_until')
                    }
            
            # Update database
            created_count = 0
            updated_count = 0
            today = date.today()
            
            for phone, data in members_dict.items():
                tf_valid_until = data['tf_valid_until']
                ntnui_valid_until = data['ntnui_valid_until']
                tf_valid = tf_valid_until >= today if tf_valid_until else False
                ntnui_valid = data['ntnui_valid']
                name = f"{data['first_name']} {data['last_name']}".strip()
                
                existing = self.get_member_by_id(phone)
                
                if existing:
                    existing.name = name or existing.name
                    existing.email = data['email'] or existing.email
                    existing.tf_valid = tf_valid
                    existing.tf_valid_until = tf_valid_until
                    existing.ntnui_valid = ntnui_valid
                    existing.ntnui_valid_until = ntnui_valid_until
                    existing.last_synced = datetime.utcnow()
                    updated_count += 1
                else:
                    new_member = Member(
                        telephone_number=phone,
                        name=name,
                        email=data['email'],
                        tf_valid=tf_valid,
                        tf_valid_until=tf_valid_until,
                        ntnui_valid=ntnui_valid,
                        ntnui_valid_until=ntnui_valid_until
                    )
                    self.db.add(new_member)
                    created_count += 1
            
            self.db.commit()
            logger.info(f"✅ Full sync: {created_count} created, {updated_count} updated")
            
            return {
                "status": "success",
                "source": "all",
                "synced_count": len(members_dict),
                "created_count": created_count,
                "updated_count": updated_count,
                "tf_count": len(tf_data),
                "ntnui_count": len(ntnui_data)
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Full sync failed: {e}")
            return {"status": "error", "message": str(e)}
    
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
