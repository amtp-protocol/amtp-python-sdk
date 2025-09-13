#!/usr/bin/env python3
"""
AMTP Supported Schemas Example

Demonstrates how to register agents with specific supported schema patterns
and how to check schema support at runtime.
"""

import asyncio
import logging
from datetime import datetime

from amtp import AMTP, Message, Schema, Error


async def supported_schemas_example():
    """Demonstrate supported schemas functionality."""
    print("=== Supported Schemas Example ===")
    
    # Create some test schemas
    print("Creating test schemas...")
    
    # Commerce schemas
    order_schema = Schema(
        id="agntcy:commerce.order.v1",
        name="Commerce Order",
        version="v1",
        description="E-commerce order schema",
        schema_def={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "total": {"type": "number"}
            },
            "required": ["order_id", "total"]
        }
    )
    order_schema.register()
    
    inventory_schema = Schema(
        id="agntcy:commerce.inventory.v1",
        name="Commerce Inventory",
        version="v1",
        description="Inventory management schema",
        schema_def={
            "type": "object",
            "properties": {
                "sku": {"type": "string"},
                "quantity": {"type": "integer"}
            },
            "required": ["sku", "quantity"]
        }
    )
    inventory_schema.register()
    
    # Finance schemas
    payment_schema = Schema(
        id="agntcy:finance.payment.v1",
        name="Finance Payment",
        version="v1",
        description="Payment processing schema",
        schema_def={
            "type": "object",
            "properties": {
                "payment_id": {"type": "string"},
                "amount": {"type": "number"}
            },
            "required": ["payment_id", "amount"]
        }
    )
    payment_schema.register()
    
    billing_schema = Schema(
        id="agntcy:finance.billing.v1",
        name="Finance Billing",
        version="v1",
        description="Billing schema",
        schema_def={
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string"},
                "amount": {"type": "number"}
            },
            "required": ["invoice_id", "amount"]
        }
    )
    billing_schema.register()
    
    # User management schema
    user_schema = Schema(
        id="agntcy:user.profile.v1",
        name="User Profile",
        version="v1",
        description="User profile schema",
        schema_def={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "name": {"type": "string"}
            },
            "required": ["user_id", "name"]
        }
    )
    user_schema.register()
    
    print("✅ Test schemas registered")
    
    # Create agents with different supported schema patterns
    print("\nCreating agents with different schema support...")
    
    # Commerce agent - supports all commerce schemas
    commerce_agent = AMTP(
        address="commerce-agent",
        gateway_url="http://localhost:8080",
        tls_enabled=False,
        supported_schemas=["agntcy:commerce.*"]
    )
    
    # Finance agent - supports only payment schemas
    finance_agent = AMTP(
        address="finance-agent",
        gateway_url="http://localhost:8080",
        tls_enabled=False,
        supported_schemas=["agntcy:finance.payment.*"]
    )
    
    # Multi-domain agent - supports commerce and finance payment schemas
    multi_agent = AMTP(
        address="multi-agent",
        gateway_url="http://localhost:8080",
        tls_enabled=False,
        supported_schemas=["agntcy:commerce.*", "agntcy:finance.payment.*"]
    )
    
    # General agent - no schema restrictions (supports all)
    general_agent = AMTP(
        address="general-agent",
        gateway_url="http://localhost:8080",
        tls_enabled=False
        # No supported_schemas specified - supports everything
    )
    
    # Test schema support checking
    print("\nTesting schema support checking...")
    
    test_schemas = [
        "agntcy:commerce.order.v1",
        "agntcy:commerce.inventory.v1",
        "agntcy:finance.payment.v1",
        "agntcy:finance.billing.v1",
        "agntcy:user.profile.v1"
    ]
    
    agents = [
        ("Commerce Agent", commerce_agent),
        ("Finance Agent", finance_agent),
        ("Multi Agent", multi_agent),
        ("General Agent", general_agent)
    ]
    
    for agent_name, agent in agents:
        print(f"\n{agent_name} schema support:")
        print(f"  Supported patterns: {agent.get_supported_schemas()}")
        
        for schema_id in test_schemas:
            supports = agent.supports_schema(schema_id)
            status = "✅" if supports else "❌"
            print(f"  {status} {schema_id}")
    
    # Demonstrate message filtering based on schema support
    print("\n=== Message Filtering Example ===")
    
    # Set up message handlers that check schema support
    @commerce_agent.on_message
    async def commerce_handler(message: Message):
        if message.schema and not commerce_agent.supports_schema(message.schema):
            print(f"🚫 Commerce agent rejecting unsupported schema: {message.schema}")
            return {"status": "unsupported_schema", "message": "This agent doesn't support this schema"}
        
        print(f"✅ Commerce agent processing message with schema: {message.schema}")
        return {"status": "processed", "agent": "commerce"}
    
    @finance_agent.on_message
    async def finance_handler(message: Message):
        if message.schema and not finance_agent.supports_schema(message.schema):
            print(f"🚫 Finance agent rejecting unsupported schema: {message.schema}")
            return {"status": "unsupported_schema", "message": "This agent doesn't support this schema"}
        
        print(f"✅ Finance agent processing message with schema: {message.schema}")
        return {"status": "processed", "agent": "finance"}
    
    try:
        # Start agents (connect and register with the gateway)
        print("\nStarting agents...")
        await commerce_agent.start()
        await finance_agent.start()
        
        print(f"Commerce agent registered as: {commerce_agent.address}")
        print(f"Finance agent registered as: {finance_agent.address}")
        
        # Simulate message processing
        print("\nSimulating message processing...")
        
        # Create a sender agent to send test messages
        sender_agent = AMTP(
            address="test-sender",
            gateway_url="http://localhost:8080",
            tls_enabled=False
        )
        await sender_agent.start()
        print(f"Sender agent registered as: {sender_agent.address}")
        
        # Test messages with different schemas
        test_messages = [
            Message(
                sender=sender_agent.address,
                recipients=[commerce_agent.address],
                subject="Order Processing",
                schema="agntcy:commerce.order.v1",
                payload={"order_id": "ORD-001", "total": 99.99}
            ),
            Message(
                sender=sender_agent.address,
                recipients=[finance_agent.address],
                subject="Payment Processing",
                schema="agntcy:finance.payment.v1",
                payload={"payment_id": "PAY-001", "amount": 99.99}
            ),
            Message(
                sender=sender_agent.address,
                recipients=[finance_agent.address],
                subject="Billing Update",
                schema="agntcy:finance.billing.v1",
                payload={"invoice_id": "INV-001", "amount": 99.99}
            )
        ]
        
        # Send messages and let the agents process them
        for message in test_messages:
            print(f"\nSending message with schema: {message.schema}")
            print(f"  From: {message.sender}")
            print(f"  To: {message.recipients[0]}")
            print(f"  Subject: {message.subject}")
            
            try:
                message_id = await sender_agent.send(message)
                print(f"  ✅ Message sent successfully: {message_id}")
            except Exception as e:
                print(f"  ❌ Failed to send message: {e}")
        
        # Wait a bit for message processing
        print("\nWaiting for message processing...")
        await asyncio.sleep(3)
        
        print("\n✅ Schema support demonstration completed")
        
    except Exception as e:
        print(f"❌ Error in example: {e}")
    finally:
        # Clean up
        print("\nStopping agents...")
        await commerce_agent.stop()
        await finance_agent.stop()
        try:
            await sender_agent.stop()
        except NameError:
            pass  # sender_agent might not be created if error occurred earlier


async def main():
    """Run the supported schemas example."""
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise for examples
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("AMTP Supported Schemas Example")
    print("=============================")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    try:
        await supported_schemas_example()
        print("\n=== Example Completed Successfully ===")
        
    except Exception as e:
        print(f"\nExample failed: {e}")
        logging.error(f"Supported schemas example error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
