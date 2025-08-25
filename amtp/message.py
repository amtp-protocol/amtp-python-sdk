"""
AMTP Message

Simple message class for building and handling AMTP messages.
"""

import json
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

from .error import Error


def generate_message_id() -> str:
    """Generate a unique message ID."""
    return str(uuid.uuid4())


def generate_idempotency_key() -> str:
    """Generate a unique idempotency key."""
    return str(uuid.uuid4())


@dataclass
class Message:
    """
    AMTP Message - represents an AMTP protocol message.
    
    Simple message structure that handles all AMTP message types:
    - Basic text messages
    - Schema-validated messages  
    - Messages with attachments
    - Workflow coordination messages
    """
    
    # Required fields
    sender: str
    recipients: List[str]
    
    # Optional fields
    subject: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    schema: Optional[str] = None
    
    # Auto-generated fields
    message_id: str = field(default_factory=generate_message_id)
    idempotency_key: str = field(default_factory=generate_idempotency_key)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"
    
    # Reply fields
    in_reply_to: Optional[str] = None
    
    # Additional fields
    headers: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        """Validate message after creation."""
        self.validate()
    
    def validate(self):
        """Validate message structure."""
        if not self.sender:
            raise Error("Message must have a sender")
        
        if not self.recipients:
            raise Error("Message must have at least one recipient")
        
        # Validate email addresses
        for recipient in self.recipients:
            if not self._is_valid_address(recipient):
                raise Error(f"Invalid recipient address: {recipient}")
        
        if not self._is_valid_address(self.sender):
            raise Error(f"Invalid sender address: {self.sender}")
        
        # Validate schema if provided
        if self.schema and not self._is_valid_schema(self.schema):
            raise Error(f"Invalid schema format: {self.schema}")
    
    def _is_valid_address(self, address: str) -> bool:
        """Check if address is valid AMTP format (agent@domain)."""
        if not address or '@' not in address:
            return False
        
        parts = address.split('@')
        if len(parts) != 2:
            return False
        
        agent, domain = parts
        return bool(agent and domain)
    
    def _is_valid_schema(self, schema: str) -> bool:
        """Check if schema ID is valid format."""
        # Basic validation for schema format (e.g., "agntcy:commerce.order.v1")
        return ':' in schema and '.' in schema
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        data = {
            "version": self.version,
            "message_id": self.message_id,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "recipients": self.recipients,
        }
        
        # Add optional fields if present
        if self.subject:
            data["subject"] = self.subject
        if self.payload:
            data["payload"] = self.payload
        if self.schema:
            data["schema"] = self.schema
        if self.in_reply_to:
            data["in_reply_to"] = self.in_reply_to
        if self.headers:
            data["headers"] = self.headers
        if self.attachments:
            data["attachments"] = self.attachments
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        # Parse timestamp
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            # Handle nanosecond precision by truncating to microseconds
            # Python's fromisoformat only supports up to microseconds (6 digits)
            timestamp_str = timestamp_str.replace('Z', '+00:00')
            
            # If there are more than 6 digits after the decimal point, truncate
            if '.' in timestamp_str and '+' in timestamp_str:
                date_part, tz_part = timestamp_str.rsplit('+', 1)
                if '.' in date_part:
                    base_part, frac_part = date_part.split('.')
                    # Truncate fractional seconds to 6 digits (microseconds)
                    frac_part = frac_part[:6]
                    timestamp_str = f"{base_part}.{frac_part}+{tz_part}"
            
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.now(timezone.utc)
        
        return cls(
            version=data.get("version", "1.0"),
            message_id=data.get("message_id", generate_message_id()),
            idempotency_key=data.get("idempotency_key", generate_idempotency_key()),
            timestamp=timestamp,
            sender=data["sender"],
            recipients=data["recipients"],
            subject=data.get("subject"),
            payload=data.get("payload"),
            schema=data.get("schema"),
            in_reply_to=data.get("in_reply_to"),
            headers=data.get("headers"),
            attachments=data.get("attachments"),
        )
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise Error(f"Invalid JSON: {e}")
    
    def reply(self, payload: Dict[str, Any], subject: Optional[str] = None) -> 'Message':
        """Create a reply message."""
        return Message(
            sender="",  # Will be set by agent
            recipients=[self.sender],
            subject=subject or f"Re: {self.subject or 'Message'}",
            payload=payload,
            in_reply_to=self.message_id
        )
    
    def size(self) -> int:
        """Get message size in bytes."""
        return len(self.to_json().encode('utf-8'))
    
    def __str__(self) -> str:
        return f"Message(id={self.message_id[:8]}..., from={self.sender}, to={self.recipients})"
    
    def __repr__(self) -> str:
        return f"Message(message_id='{self.message_id}', sender='{self.sender}', recipients={self.recipients})"
