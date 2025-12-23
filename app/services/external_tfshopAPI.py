"""
TF Shop WooCommerce API Client
Fetches membership orders from WooCommerce with pagination
"""
import httpx
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
import base64

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to consistent format with country code (+47 for Norwegian)
    Assumes Norwegian number if no country code present
    """
    if not phone:
        return ''
    
    # Remove spaces, hyphens, and parentheses
    normalized = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Remove leading plus
    normalized = normalized.replace('+', '')
    
    # Handle Norwegian numbers starting with 0047
    if normalized.startswith('0047'):
        normalized = '47' + normalized[4:]
    
    # If number starts with 00 (international format), keep as is
    elif normalized.startswith('00'):
        normalized = normalized[2:]  # Remove 00, keep country code
        
    # If number is 8 digits and looks Norwegian, add 47
    elif len(normalized) == 8 and normalized[0] in '456789':
        normalized = '47' + normalized
    
    # If number is 8 digits (any Norwegian number without country code), add 47
    elif len(normalized) == 8:
        normalized = '47' + normalized
    
    # Add + prefix if not empty
    if normalized:
        normalized = '+' + normalized
    
    return normalized


class TFShopAPIClient:
    """Client for fetching data from TF Shop WooCommerce API"""
    
    def __init__(self, consumer_key: str = None, consumer_secret: str = None):
        self.consumer_key = consumer_key or os.getenv('consumer_key')  # Endre fra 'TF_CONSUMER_KEY'
        self.consumer_secret = consumer_secret or os.getenv('consumer_secret')  # Endre fra 'TF_CONSUMER_SECRET'
        self.base_url = 'https://ntnui.no/toppturogfrikjoring/wp-json/wc/v3/orders'
        
        if not self.consumer_key or not self.consumer_secret:
            logger.warning("TF Shop API credentials not configured")
    
    async def fetch_all_orders(self, product_id: int = 4223) -> List[Dict]:
        """
        Fetch all orders for a specific product with pagination
        
        Args:
            product_id: WooCommerce product ID (default: 4223)
            
        Returns:
            List of order dictionaries
        """
        if not self.consumer_key or not self.consumer_secret:
            logger.error("Cannot fetch orders: API credentials missing")
            return []
        
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json'
        }
        
        all_orders = []
        page = 1
        per_page = 100  # Max allowed by WooCommerce
        
        logger.info(f"🔄 Fetching fresh data from WooCommerce (product_id={product_id})...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                try:
                    url = f"{self.base_url}?product={product_id}&per_page={per_page}&page={page}"
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    
                    orders = response.json()
                    all_orders.extend(orders)
                    
                    logger.info(f"  📄 Page {page}: {len(orders)} orders (total: {len(all_orders)})")
                    
                    # If we got fewer orders than per_page, we've reached the end
                    if len(orders) < per_page:
                        break
                    
                    page += 1
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error fetching orders (page {page}): {e}")
                    break
                except httpx.RequestError as e:
                    logger.error(f"Request error fetching orders (page {page}): {e}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error fetching orders (page {page}): {e}")
                    break
        
        logger.info(f"✅ TF Shop fetch complete: {len(all_orders)} total orders")
        return all_orders
    
    def normalize_orders_to_members(self, orders: List[Dict]) -> List[Dict]:
        """
        Convert raw WooCommerce orders to normalized member format
        Keeps only the most recent order per phone number
        Only includes orders with membership product
        
        Returns:
            List of normalized member dictionaries
        """
        # Dictionary to track latest order per phone number
        phone_to_order = {}
        membership_product_name = "Medlemskap i NTNUI Topptur og Frikjøring"
        
        for order in orders:
            billing = order.get('billing', {})
            phone = billing.get('phone', '')
            
            if not phone:
                continue
            
            # Check if this order contains the membership product
            line_items = order.get('line_items', [])
            has_membership = any(
                item.get('name', '') == membership_product_name 
                for item in line_items
            )
            
            if not has_membership:
                continue  # Skip orders without membership product
            
            normalized_phone = normalize_phone_number(phone)
            date_paid = order.get('date_paid', '')
            
            if not date_paid:
                continue
            
            # Parse date to compare
            try:
                paid_date = datetime.fromisoformat(date_paid.replace('Z', '+00:00'))
            except Exception:
                continue
            
            # Keep only the most recent order per phone number
            if normalized_phone in phone_to_order:
                existing_date = datetime.fromisoformat(
                    phone_to_order[normalized_phone].get('date_paid', '').replace('Z', '+00:00')
                )
                if paid_date > existing_date:
                    phone_to_order[normalized_phone] = order
            else:
                phone_to_order[normalized_phone] = order
        
        # Now convert to member format
        members = []
        
        for normalized_phone, order in phone_to_order.items():
            billing = order.get('billing', {})
            date_paid = order.get('date_paid', '')
            
            # Calculate expiry date (membership valid until end of purchase year)
            tf_valid_until = None
            if date_paid:
                try:
                    paid_date = datetime.fromisoformat(date_paid.replace('Z', '+00:00'))
                    # Membership valid until end of purchase year
                    tf_valid_until = datetime(paid_date.year, 12, 31).date()
                except Exception as e:
                    logger.warning(f"Could not parse date_paid '{date_paid}': {e}")
            
            member = {
                'phone': normalized_phone,
                'first_name': billing.get('first_name', ''),
                'last_name': billing.get('last_name', ''),
                'email': billing.get('email', ''),
                'date_paid': date_paid,
                'product_name': membership_product_name,
                'tf_valid_until': tf_valid_until
            }
            
            members.append(member)
        
        logger.info(f"✅ Normalized {len(members)} unique TF Shop members (from {len(orders)} orders, filtered for membership product)")
        return members
    
    async def get_members(self, product_id: int = 4223) -> List[Dict]:
        """
        Fetch and normalize all member data from TF Shop
        
        Returns:
            List of normalized member dictionaries
        """
        orders = await self.fetch_all_orders(product_id)
        return self.normalize_orders_to_members(orders)
