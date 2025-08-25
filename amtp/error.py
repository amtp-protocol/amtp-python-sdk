"""
AMTP Error Handling

Simple error class for AMTP operations.
"""


class Error(Exception):
    """
    AMTP Error - base exception for all AMTP-related errors.
    
    Simple, single error class that covers all AMTP error scenarios:
    - Connection errors
    - Authentication errors  
    - Validation errors
    - Message delivery errors
    - Gateway errors
    """
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize AMTP error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message
    
    def __repr__(self) -> str:
        return f"Error('{self.message}', {self.details})"
