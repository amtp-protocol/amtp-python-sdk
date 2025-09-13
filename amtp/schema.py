"""
AMTP Schema

Schema registration and validation for AMTP messages.
"""

import json
import re
from typing import Dict, Any, Optional, List, ClassVar
from dataclasses import dataclass, field

import jsonschema
from jsonschema import Draft7Validator, ValidationError as JsonSchemaValidationError

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
        
        # Validate that this is a proper JSON Schema using Draft7Validator
        try:
            Draft7Validator.check_schema(self.schema_def)
        except JsonSchemaValidationError as e:
            raise Error(f"Invalid JSON Schema definition: {e.message}")
        except Exception as e:
            raise Error(f"Schema definition validation failed: {e}")
        
        # Basic requirement - must have a type field
        if "type" not in self.schema_def:
            raise Error("Schema definition must have a 'type' field")
    
    def validate_message(self, payload: Dict[str, Any]) -> bool:
        """
        Validate a message payload against this schema using JSON Schema validation.
        
        Args:
            payload: Message payload to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            Error: If validation fails
        """
        try:
            # Create validator instance for this schema
            validator = Draft7Validator(self.schema_def)
            
            # Validate the payload
            validator.validate(payload)
            
            return True
            
        except JsonSchemaValidationError as e:
            # Format the validation error message nicely
            error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            raise Error(f"Schema validation failed at {error_path}: {e.message}")
        except Exception as e:
            raise Error(f"Schema validation failed: {e}")
    
    def validate_message_detailed(self, payload: Dict[str, Any]) -> List[str]:
        """
        Validate a message payload and return detailed error information.
        
        Args:
            payload: Message payload to validate
            
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        try:
            validator = Draft7Validator(self.schema_def)
            errors = []
            
            for error in validator.iter_errors(payload):
                error_path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                errors.append(f"At {error_path}: {error.message}")
            
            return errors
            
        except Exception as e:
            return [f"Validation error: {e}"]
    
    def is_valid(self, payload: Dict[str, Any]) -> bool:
        """
        Check if a payload is valid without raising exceptions.
        
        Args:
            payload: Message payload to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            self.validate_message(payload)
            return True
        except Error:
            return False
    
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
    def validate_payload_detailed(cls, schema_id: str, payload: Dict[str, Any]) -> List[str]:
        """
        Validate a payload against a registered schema and return detailed errors.
        
        Args:
            schema_id: Schema ID to validate against
            payload: Payload to validate
            
        Returns:
            List[str]: List of validation error messages (empty if valid)
            
        Raises:
            Error: If schema not found
        """
        schema = cls.get(schema_id)
        if not schema:
            raise Error(f"Schema not found: {schema_id}")
        
        return schema.validate_message_detailed(payload)
    
    @classmethod
    def is_payload_valid(cls, schema_id: str, payload: Dict[str, Any]) -> bool:
        """
        Check if a payload is valid against a registered schema without raising exceptions.
        
        Args:
            schema_id: Schema ID to validate against
            payload: Payload to validate
            
        Returns:
            bool: True if valid, False otherwise (including if schema not found)
        """
        try:
            schema = cls.get(schema_id)
            if not schema:
                return False
            return schema.is_valid(payload)
        except Exception:
            return False
    
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
