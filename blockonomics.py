"""
Blockonomics Bitcoin Payment Integration Module

This module handles Bitcoin payments via the Blockonomics API.
Blockonomics is a non-custodial Bitcoin payment processor.
"""

import logging
import time
import requests
import hashlib
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)

# Blockonomics API endpoints
BLOCKONOMICS_BASE_URL = "https://www.blockonomics.co/api"
NEW_ADDRESS_ENDPOINT = f"{BLOCKONOMICS_BASE_URL}/new_address"
PRICE_ENDPOINT = f"{BLOCKONOMICS_BASE_URL}/price"
ADDRESS_HISTORY_ENDPOINT = f"{BLOCKONOMICS_BASE_URL}/searchhistory"


class PaymentStatus(Enum):
    """Status of a Bitcoin payment."""
    PENDING = 0  # Waiting for payment
    UNCONFIRMED = 1  # Payment detected but unconfirmed
    CONFIRMED = 2  # Payment confirmed
    EXPIRED = -1  # Payment expired
    ERROR = -2  # Error occurred


@dataclass
class BitcoinPayment:
    """Represents a Bitcoin payment request."""
    address: str
    amount_btc: float
    amount_fiat: float
    currency: str
    status: PaymentStatus
    txid: Optional[str] = None
    confirmations: int = 0
    created_at: float = 0
    expires_at: float = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if the payment has expired."""
        return time.time() > self.expires_at
    
    @property
    def is_paid(self) -> bool:
        """Check if the payment is confirmed."""
        return self.status == PaymentStatus.CONFIRMED


class BlockonomicsAPI:
    """
    Blockonomics API client for Bitcoin payments.
    
    This class provides methods to:
    - Generate new Bitcoin addresses for payments
    - Convert fiat currency to BTC
    - Check payment status
    """
    
    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize the Blockonomics API client.
        
        Args:
            api_key: Your Blockonomics API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_btc_price(self, currency: str = "USD") -> Optional[float]:
        """
        Get current Bitcoin price in the specified currency.
        
        Args:
            currency: ISO currency code (USD, EUR, etc.)
            
        Returns:
            Current BTC price or None if request fails
        """
        try:
            response = requests.get(
                PRICE_ENDPOINT,
                params={"currency": currency},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return float(data.get("price", 0))
        except Exception as e:
            log.error(f"Failed to get BTC price: {e}")
            return None
    
    def create_payment_address(self) -> Optional[str]:
        """
        Generate a new Bitcoin address for receiving payment.
        
        Returns:
            New Bitcoin address or None if request fails
        """
        try:
            response = requests.post(
                NEW_ADDRESS_ENDPOINT,
                headers=self._headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            address = data.get("address")
            if address:
                log.info(f"Generated new payment address: {address[:10]}...")
                return address
            log.error(f"No address in response: {data}")
            return None
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP error creating payment address: {e}")
            # Handle specific error codes
            if e.response.status_code == 401:
                log.error("Invalid API key")
            elif e.response.status_code == 500:
                log.error("Blockonomics server error - check your wallet setup")
            return None
        except Exception as e:
            log.error(f"Failed to create payment address: {e}")
            return None
    
    def convert_to_btc(self, amount: float, currency: str = "USD") -> Optional[float]:
        """
        Convert fiat amount to BTC.
        
        Args:
            amount: Amount in fiat currency
            currency: ISO currency code
            
        Returns:
            Equivalent BTC amount or None if conversion fails
        """
        btc_price = self.get_btc_price(currency)
        if btc_price and btc_price > 0:
            return round(amount / btc_price, 8)
        return None
    
    def check_address_transactions(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Check transactions for a specific Bitcoin address.
        
        Args:
            address: Bitcoin address to check
            
        Returns:
            Transaction information or None if request fails
        """
        try:
            response = requests.get(
                ADDRESS_HISTORY_ENDPOINT,
                headers=self._headers,
                params={"addr": address},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error(f"Failed to check address transactions: {e}")
            return None


class BlockonomicsPaymentProcessor:
    """
    High-level payment processor using Blockonomics.
    
    Handles the complete payment flow:
    1. Create payment request with BTC amount
    2. Generate unique payment address
    3. Monitor for incoming payments
    4. Handle payment confirmation
    """
    
    def __init__(self, api_key: str, currency: str = "USD", 
                 payment_timeout: int = 3600, min_confirmations: int = 1):
        """
        Initialize the payment processor.
        
        Args:
            api_key: Blockonomics API key
            currency: Default fiat currency
            payment_timeout: Time in seconds before payment expires (default 1 hour)
            min_confirmations: Minimum confirmations required (default 1)
        """
        self.api = BlockonomicsAPI(api_key)
        self.currency = currency
        self.payment_timeout = payment_timeout
        self.min_confirmations = min_confirmations
        self._pending_payments: Dict[str, BitcoinPayment] = {}
    
    def create_payment(self, amount_fiat: float, 
                      currency: Optional[str] = None) -> Optional[BitcoinPayment]:
        """
        Create a new payment request.
        
        Args:
            amount_fiat: Amount to pay in fiat currency
            currency: Currency code (uses default if not specified)
            
        Returns:
            BitcoinPayment object or None if creation fails
        """
        currency = currency or self.currency
        
        # Convert to BTC
        amount_btc = self.api.convert_to_btc(amount_fiat, currency)
        if not amount_btc:
            log.error("Failed to convert fiat to BTC")
            return None
        
        # Generate payment address
        address = self.api.create_payment_address()
        if not address:
            log.error("Failed to create payment address")
            return None
        
        # Create payment object
        current_time = time.time()
        payment = BitcoinPayment(
            address=address,
            amount_btc=amount_btc,
            amount_fiat=amount_fiat,
            currency=currency,
            status=PaymentStatus.PENDING,
            created_at=current_time,
            expires_at=current_time + self.payment_timeout
        )
        
        # Store pending payment
        self._pending_payments[address] = payment
        
        log.info(f"Created payment: {amount_fiat} {currency} = {amount_btc} BTC to {address[:10]}...")
        return payment
    
    def check_payment_status(self, address: str) -> PaymentStatus:
        """
        Check the status of a pending payment.
        
        Args:
            address: Bitcoin address to check
            
        Returns:
            Current payment status
        """
        payment = self._pending_payments.get(address)
        if not payment:
            return PaymentStatus.ERROR
        
        # Check if expired
        if payment.is_expired:
            payment.status = PaymentStatus.EXPIRED
            return PaymentStatus.EXPIRED
        
        # Check for transactions
        tx_info = self.api.check_address_transactions(address)
        if not tx_info:
            return payment.status
        
        history = tx_info.get("history", [])
        if history:
            # Find transaction matching expected amount
            for tx in history:
                tx_value = tx.get("value", 0) / 100000000  # Convert satoshi to BTC
                if tx_value >= payment.amount_btc * 0.99:  # Allow 1% variance
                    confirmations = tx.get("confirmations", 0)
                    payment.txid = tx.get("txid")
                    payment.confirmations = confirmations
                    
                    if confirmations >= self.min_confirmations:
                        payment.status = PaymentStatus.CONFIRMED
                    else:
                        payment.status = PaymentStatus.UNCONFIRMED
                    break
        
        return payment.status
    
    def get_payment(self, address: str) -> Optional[BitcoinPayment]:
        """
        Get a pending payment by address.
        
        Args:
            address: Bitcoin address
            
        Returns:
            BitcoinPayment object or None
        """
        return self._pending_payments.get(address)
    
    def cleanup_expired(self) -> int:
        """
        Remove expired payments from tracking.
        
        Returns:
            Number of payments removed
        """
        expired = [addr for addr, p in self._pending_payments.items() if p.is_expired]
        for addr in expired:
            del self._pending_payments[addr]
        return len(expired)
    
    def generate_payment_id(self, user_id: int, amount: float) -> str:
        """
        Generate a unique payment ID for tracking.
        
        Args:
            user_id: Telegram user ID
            amount: Payment amount
            
        Returns:
            Unique payment identifier
        """
        data = f"{user_id}:{amount}:{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


def format_btc_amount(amount: float) -> str:
    """Format BTC amount for display."""
    if amount >= 0.001:
        return f"{amount:.8f} BTC"
    else:
        return f"{amount * 100000000:.0f} sats"


def generate_payment_qr_data(address: str, amount_btc: float) -> str:
    """
    Generate Bitcoin payment URI for QR code.
    
    Args:
        address: Bitcoin address
        amount_btc: Amount in BTC
        
    Returns:
        BIP21 formatted payment URI
    """
    return f"bitcoin:{address}?amount={amount_btc}"
