#!/usr/bin/env python3
"""
Simple AMTP Example

Demonstrates how to create a basic AMTP connection using the simplified AMTP SDK.
This example responds to simple text messages with acknowledgments.
"""

import asyncio
import logging
from datetime import datetime

from amtp import AMTP, Message, Error


async def main():
    """Main function to run the simple AMTP connection."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create AMTP connection
    amtp = AMTP(
        address="simple-agent",
        gateway_url="http://localhost:8080",
        delivery_mode="pull",
        tls_enabled=False,
        log_level="INFO"
    )
    
    # Message counter
    message_count = 0
    
    # Register message handler
    @amtp.on_message
    async def handle_message(message: Message):
        nonlocal message_count
        message_count += 1
        
        print(f"Received message #{message_count} from {message.sender}")
        print(f"Subject: {message.subject}")
        
        if message.payload:
            print(f"Payload: {message.payload}")
        
        # Handle different message types
        response = {
            "status": "received",
            "message_count": message_count,
            "amtp_address": amtp.address,
            "original_subject": message.subject,
            "response": f"Thank you for your message! This is response #{message_count}."
        }
        
        # If the message contains a question, try to answer it
        if message.payload and isinstance(message.payload, dict):
            question = message.payload.get("question") or message.payload.get("text")
            if question:
                response["answer"] = answer_question(question, amtp.address, message_count)
        
        return response
    
    # Register error handler
    @amtp.on_error
    async def handle_error(error: Exception):
        print(f"Error occurred: {error}")
        logging.error(f"AMTP error: {error}", exc_info=True)
    
    def answer_question(question: str, amtp_address: str, msg_count: int) -> str:
        """Provide simple answers to common questions."""
        question_lower = question.lower()
        
        if "hello" in question_lower or "hi" in question_lower:
            return f"Hello! I'm {amtp_address}, nice to meet you!"
        elif "how are you" in question_lower:
            return f"I'm doing well, thank you! I've processed {msg_count} messages so far."
        elif "what is your name" in question_lower or "who are you" in question_lower:
            return f"I'm {amtp_address}, a simple AMTP connection."
        elif "time" in question_lower:
            return f"The current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            return "I'm a simple AMTP connection, so I can only answer basic questions. Try asking 'hello', 'how are you', 'what is your name', or 'what time is it'."
    
    try:
        print("Starting Simple AMTP Connection...")
        print(f"AMTP address: {amtp.address}")
        print(f"Gateway URL: {amtp.gateway_url}")
        print("I can respond to basic questions and acknowledge messages.")
        print("Press Ctrl+C to stop")
        
        # Run the AMTP connection
        await amtp.run()
        
    except KeyboardInterrupt:
        print("\nShutting down AMTP connection...")
    except Error as e:
        print(f"AMTP Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())