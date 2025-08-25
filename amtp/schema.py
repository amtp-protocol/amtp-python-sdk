"""
AMTP Schema

Schema registration and validation for AMTP messages.
"""

import json
import re
from typing import Dict, Any, Optional, List, ClassVar
from dataclasses import dataclass, field

from .error import Error


@dataclass
class Schema:
    """
    AMTP Schema - handles schema registration and message validation.
    
    Provides schema management for AMTP messages:
    - Schema registration and storage
    - Message payload validation
    - Schema versioning
    - Shared schema registry
    """
    
    id: str  # e.g., "agntcy:commerce.order.v1"
    name: str
    version: str
    schema_def: Dict[str, Any]  # JSON Schema definition
    description: Optional[str] = None
    
    # Class-level schema registry (shared across all instances)
    _registry: ClassVar[Dict[str, 'Schema']] = {}
    
    def __post_init__(self):
        """Validate schema after creation."""
        self.validate_schema_id()
        self.validate_schema_definition()
    
    def validate_schema_id(self):
        """Validate schema ID format."""
        if not self.id:
            raise Error("Schema ID cannot be empty")
        
        # Validate format: namespace:category.subcategory.version
        pattern = r'^[a-zA-Z0-9_-]+:[a-zA-Z0-9_.-]+\.v\d+$'
        if not re.match(pattern, self.id):
            raise Error(f"Invalid schema ID format: {self.id}. Expected format: 'namespace:category.subcategory.vN'")
    
    def validate_schema_definition(self):
        """Validate JSON Schema definition."""
        if not isinstance(self.schema_def, dict):
            raise Error("Schema definition must be a dictionary")
        
        # Basic JSON Schema validation
        if "type" not in self.schema_def:
            raise Error("Schema definition must have a 'type' field")
        
        # Ensure it's a valid JSON Schema structure
        required_fields = ["type"]
        for field in required_fields:
            if field not in self.schema_def:
                raise Error(f"Schema definition missing required field: {field}")
    
    def validate_message(self, payload: Dict[str, Any]) -> bool:
        """
        Validate a message payload against this schema.
        
        Args:
            payload: Message payload to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            Error: If validation fails
        """
        try:
            # Simple validation - in a real implementation, you'd use jsonschema library
            return self._validate_against_schema(payload, self.schema_def)
        except Exception as e:
            raise Error(f"Schema validation failed: {e}")
    
    def _validate_against_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Basic schema validation (simplified)."""
        schema_type = schema.get("type")
        
        if schema_type == "object":
            if not isinstance(data, dict):
                raise Error(f"Expected object, got {type(data).__name__}")
            
            # Check required properties
            required = schema.get("required", [])
            for prop in required:
                if prop not in data:
                    raise Error(f"Missing required property: {prop}")
            
            # Validate properties
            properties = schema.get("properties", {})
            for prop, value in data.items():
                if prop in properties:
                    self._validate_against_schema(value, properties[prop])
        
        elif schema_type == "array":
            if not isinstance(data, list):
                raise Error(f"Expected array, got {type(data).__name__}")
            
            items_schema = schema.get("items")
            if items_schema:
                for item in data:
                    self._validate_against_schema(item, items_schema)
        
        elif schema_type == "string":
            if not isinstance(data, str):
                raise Error(f"Expected string, got {type(data).__name__}")
        
        elif schema_type == "number":
            if not isinstance(data, (int, float)):
                raise Error(f"Expected number, got {type(data).__name__}")
        
        elif schema_type == "integer":
            if not isinstance(data, int):
                raise Error(f"Expected integer, got {type(data).__name__}")
        
        elif schema_type == "boolean":
            if not isinstance(data, bool):
                raise Error(f"Expected boolean, got {type(data).__name__}")
        
        return True
    
    def register(self):
        """Register this schema in the global registry."""
        Schema._registry[self.id] = self
    
    @classmethod
    def get(cls, schema_id: str) -> Optional['Schema']:
        """Get a schema from the registry."""
        return cls._registry.get(schema_id)
    
    @classmethod
    def list_schemas(cls) -> List[str]:
        """List all registered schema IDs."""
        return list(cls._registry.keys())
    
    @classmethod
    def validate_payload(cls, schema_id: str, payload: Dict[str, Any]) -> bool:
        """
        Validate a payload against a registered schema.
        
        Args:
            schema_id: Schema ID to validate against
            payload: Payload to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            Error: If schema not found or validation fails
        """
        schema = cls.get(schema_id)
        if not schema:
            raise Error(f"Schema not found: {schema_id}")
        
        return schema.validate_message(payload)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schema':
        """Create schema from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            schema_def=data["schema"],
            description=data.get("description")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "schema": self.schema_def
        }
        
        if self.description:
            data["description"] = self.description
        
        return data
    
    def to_json(self) -> str:
        """Convert schema to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Schema':
        """Create schema from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise Error(f"Invalid JSON: {e}")
    
    def __str__(self) -> str:
        return f"Schema({self.id})"
    
    def __repr__(self) -> str:
        return f"Schema(id='{self.id}', name='{self.name}', version='{self.version}')"
