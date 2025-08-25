"""
AMTP Python SDK

A simple Python SDK for building AI agents that communicate using the
Agent Message Transfer Protocol (AMTP) v1.0.

This SDK provides 4 core classes:
- AMTP: Handles gateway connection, registration, and message processing
- Message: Builds and validates AMTP messages
- Schema: Manages schema registration and validation
- Error: Simple error handling

Example usage:
    from amtp import AMTP, Message

    # Create AMTP connection
    amtp = AMTP("my-agent@company.com", "https://gateway.company.com")

    # Handle messages
    @amtp.on_message
    async def handle_message(message):
        print(f"Received: {message.payload}")
        return {"response": "processed"}

    # Send a message
    message = Message(
        sender="my-agent@company.com",
        recipients=["other@company.com"],
        subject="Hello",
        payload={"greeting": "Hello, World!"}
    )
    await amtp.send(message)

    # Start the connection
    await amtp.run()
"""

__version__ = "1.0.0"
__author__ = "AMTP Protocol Team"
__email__ = "xiyou.wangcong@gmail.com"
__license__ = "Apache-2.0"

# Core imports - just 4 simple classes
from .agent import AMTP
from .message import Message
from .schema import Schema
from .error import Error

__all__ = [
    # Core classes - that's it!
    "AMTP",
    "Message", 
    "Schema",
    "Error",
]