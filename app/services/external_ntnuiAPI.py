"""
NTNUI API Client
Fetches NTNUI membership data from the NTNUI API with pagination support
"""
import httpx
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NTNUIAPIClient:
    """Client for fetching data from NTNUI API"""
    
    def __init__(self, api_key: str = None, group_slug: str = 'esport'):
        self.api_key = api_key or os.getenv('devNTNUIApiKey')
        self.base_url = 'https://dev.api.ntnui.no'
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
        per_page = 100  # Adjust based on NTNUI API limits
        
        logger.info(f"Fetching memberships from NTNUI API (group: {self.group_slug})...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                        
                        logger.info(f"Fetched page {page}: {len(memberships)} memberships (total: {len(all_memberships)})")
                        
                        # Check if there are more pages
                        if not data.get('next'):
                            break
                        
                        page += 1
                    else:
                        # Non-paginated response
                        if isinstance(data, list):
                            all_memberships.extend(data)
                            logger.info(f"Fetched {len(data)} memberships (non-paginated)")
                        break
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error fetching memberships (page {page}): {e}")
                    break
                except httpx.RequestError as e:
                    logger.error(f"Request error fetching memberships (page {page}): {e}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error fetching memberships (page {page}): {e}")
                    break
        
        logger.info(f"NTNUI fetch complete: {len(all_memberships)} total memberships")
        return all_memberships
    
    def normalize_memberships_to_members(self, memberships: List[Dict]) -> List[Dict]:
        """
        Convert raw NTNUI memberships to normalized member format
        
        Returns:
            List of normalized member dictionaries
        """
        members = []
        
        for membership in memberships:
            phone = membership.get('phone_number', '')
            
            if not phone:
                continue
            
            # NTNUI API already uses phone numbers with land code
            # No normalization needed as per user requirement
            
            # Parse expiry date
            ntnui_valid_until = None
            expiry_date = membership.get('ntnui_contract_expiry_date') or membership.get('end_date')
            
            if expiry_date:
                try:
                    ntnui_valid_until = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                except Exception as e:
                    logger.warning(f"Could not parse expiry date '{expiry_date}': {e}")
            
            member = {
                'phone': phone,  # Already has land code
                'first_name': membership.get('first_name', ''),
                'last_name': membership.get('last_name', ''),
                'email': membership.get('email', ''),
                'ntnui_valid_until': ntnui_valid_until
            }
            
            members.append(member)
        
        logger.info(f"Normalized {len(members)} NTNUI members")
        return members
    
    async def get_members(self) -> List[Dict]:
        """
        Fetch and normalize all member data from NTNUI
        
        Returns:
            List of normalized member dictionaries
        """
        memberships = await self.fetch_all_memberships()
        return self.normalize_memberships_to_members(memberships)

