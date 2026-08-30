"""
NTNUI API Client
Fetches NTNUI membership data from the NTNUI API with pagination support
"""
import httpx
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)


class NTNUIAPIClient:
    """Client for fetching data from NTNUI API"""
    
    def __init__(self, api_key: str = None, group_slug: str = 'topptur-og-frikjoring'):
        self.api_key = api_key or os.getenv('tfNtnuiApiKey')
        self.base_url = 'https://api.ntnui.no'
        self.group_slug = group_slug
        
        if not self.api_key:
            logger.warning("NTNUI API key not configured")
    
    async def fetch_all_memberships(self) -> List[Dict]:
        """
        Fetch all memberships for the group with pagination
        
        Returns:
            List of membership dictionaries
        """
        if not self.api_key:
            logger.error("Cannot fetch memberships: API key missing")
            return []
        
        headers = {
            'accept': 'application/json',
            'API-KEY': self.api_key
        }
        
        all_memberships = []
        page = 1
        per_page = 500  # Safe page size for ~1600 members
        
        logger.info(f"🔄 Fetching fresh data from NTNUI API (group: {self.group_slug})...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            while True:
                try:
                    url = f"{self.base_url}/groups/{self.group_slug}/memberships/"
                    params = {
                        'page': page,
                        'page_size': per_page
                    }
                    
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Handle both paginated and non-paginated responses
                    if isinstance(data, dict) and 'results' in data:
                        memberships = data.get('results', [])
                        all_memberships.extend(memberships)
                        
                        logger.info(f"  📄 Page {page}: {len(memberships)} memberships (total: {len(all_memberships)})")
                        
                        # Check if there are more pages
                        if not data.get('next'):
                            break
                        
                        page += 1
                    else:
                        # Non-paginated response
                        if isinstance(data, list):
                            all_memberships.extend(data)
                            logger.info(f"  📄 Fetched {len(data)} memberships (non-paginated)")
                        break
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"❌ HTTP error fetching memberships (page {page}): {e}")
                    break
                except httpx.RequestError as e:
                    logger.error(f"❌ Request error fetching memberships (page {page}): {e}")
                    break
                except Exception as e:
                    logger.error(f"❌ Unexpected error fetching memberships (page {page}): {e}")
                    break
        
        logger.info(f"✅ NTNUI fetch complete: {len(all_memberships)} total memberships")
        return all_memberships
    
    def normalize_memberships_to_members(self, memberships: List[Dict]) -> List[Dict]:
        """
        Convert raw NTNUI memberships to normalized member format
        
        Returns:
            List of normalized member dictionaries
        """
        members = []
        today = date.today()
        contract_valid_count = 0
        
        for membership in memberships:
            phone = membership.get('phone_number', '')
            
            if not phone:
                continue
            
            # NTNUI API already uses phone numbers with land code
            # No normalization needed as per user requirement
            
            # The endpoint lists everyone who has ever joined the group, so
            # membership validity comes from has_valid_group_membership - NOT
            # from ntnui_contract_expiry_date, which is the separate
            # NTNUI-wide contract and can be expired while the group
            # membership is perfectly valid.
            ntnui_valid = bool(membership.get('has_valid_group_membership'))
            
            # Group membership follows the calendar year, which is what
            # medlem.ntnui.no shows ("gyldig til 31. des").
            ntnui_valid_until = date(today.year, 12, 31) if ntnui_valid else None
            
            # Only for the log line below, so the gap stays visible
            contract_expiry = membership.get('ntnui_contract_expiry_date')
            if contract_expiry:
                try:
                    if datetime.strptime(contract_expiry, '%Y-%m-%d').date() >= today:
                        contract_valid_count += 1
                except Exception as e:
                    logger.warning(f"Could not parse expiry date '{contract_expiry}': {e}")
            
            member = {
                'phone': phone,  # Already has land code
                'first_name': membership.get('first_name', ''),
                'last_name': membership.get('last_name', ''),
                'email': membership.get('email', ''),
                'ntnui_valid': ntnui_valid,
                'ntnui_valid_until': ntnui_valid_until
            }
            
            members.append(member)
        
        valid_count = sum(1 for m in members if m['ntnui_valid'])
        logger.info(
            f"✅ Normalized {len(members)} NTNUI members: "
            f"{valid_count} with a valid group membership "
            f"({contract_valid_count} with a valid NTNUI contract date)"
        )
        return members
    
    async def get_members(self) -> List[Dict]:
        """
        Fetch and normalize all member data from NTNUI
        
        Returns:
            List of normalized member dictionaries
        """
        memberships = await self.fetch_all_memberships()
        return self.normalize_memberships_to_members(memberships)

