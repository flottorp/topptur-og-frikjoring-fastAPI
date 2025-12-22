import httpx
import logging

logger = logging.getLogger(__name__)


class ExternalAPIClient:
    """Client for external API calls"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def fetch_member_data(self, member_id: str) -> dict:
        """
        Fetch member data from external API
        
        Args:
            member_id: ID of the member to fetch
            
        Returns:
            dict: Member data from external API
        """
        try:
            if not self.base_url:
                logger.warning("No external API URL configured")
                return {}
            
            response = await self.client.get(
                f"{self.base_url}/members/{member_id}",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error fetching member data: {e}")
            return {}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
