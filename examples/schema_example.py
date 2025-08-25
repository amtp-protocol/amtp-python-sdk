#!/usr/bin/env python3
"""
AMTP Schema Example

Demonstrates schema registration, validation, and usage in AMTP messages.
Shows how to create custom schemas, validate data, and use schemas in
agent communication.
"""

import asyncio
import logging
from datetime import datetime

from amtp import AMTP, Message, Schema, Error


async def basic_schema_validation_example():
    """Demonstrate basic schema validation with user-defined schemas."""
    print("=== Basic Schema Validation Example ===")
    
    # Create a simple text message schema
    print("Creating text message schema...")
    text_schema = Schema(
        id="myapp:message.text.v1",
        name="Text Message",
        version="v1",
        description="Simple text message schema",
        schema_def={
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"]
        }
    )
    text_schema.register()
    
    # Test text message schema
    print("Testing text message schema...")
    try:
        text_data = {"text": "Hello, World!"}
        Schema.validate_payload(text_schema.id, text_data)
        print("✅ Text message data is valid")
    except Error as e:
        print(f"❌ Text validation failed: {e}")
    
    # Create an order schema for this example
    print("\nCreating order schema...")
    order_schema = Schema(
        id="myapp:commerce.order.v1",
        name="E-commerce Order",
        version="v1",
        description="E-commerce order processing schema",
        schema_def={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    },
                    "required": ["name", "email"]
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sku": {"type": "string"},
                            "name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "price": {"type": "number"}
                        },
                        "required": ["sku", "quantity", "price"]
                    }
                },
                "total": {"type": "number"},
                "currency": {"type": "string"}
            },
            "required": ["order_id", "customer", "items", "total"]
        }
    )
    order_schema.register()
    
    # Test order schema
    print("Testing order schema...")
    try:
        order_data = {
            "order_id": "ORD-2025-001",
            "customer": {
                "name": "John Doe",
                "email": "john.doe@example.com"
            },
            "items": [
                {
                    "sku": "WIDGET-001",
                    "name": "Premium Widget",
                    "quantity": 2,
                    "price": 29.99
                }
            ],
            "total": 59.98,
            "currency": "USD"
        }
        
        Schema.validate_payload(order_schema.id, order_data)
        print("✅ Order data is valid")
    except Error as e:
        print(f"❌ Order validation failed: {e}")
    
    # Test validation failure
    print("\nTesting validation failure...")
    try:
        invalid_order = {
            "order_id": "ORD-123",
            # Missing required customer field
            "items": [],
            "total": 0
        }
        Schema.validate_payload(order_schema.id, invalid_order)
        print("❌ This should have failed!")
    except Error as e:
        print(f"✅ Expected validation error: {e}")


async def custom_schema_creation_example():
    """Demonstrate creating and registering custom schemas."""
    print("\n=== Custom Schema Creation Example ===")
    
    # Create a user profile schema
    user_schema = Schema(
        id="myapp:user.profile.v1",
        name="User Profile",
        version="v1",
        description="User profile information schema",
        schema_def={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "username": {"type": "string"},
                "email": {"type": "string"},
                "profile": {
                    "type": "object",
                    "properties": {
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "age": {"type": "integer"},
                        "preferences": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["first_name", "last_name"]
                },
                "created_at": {"type": "string"}
            },
            "required": ["user_id", "username", "email", "profile"]
        }
    )
    
    # Register the schema
    user_schema.register()
    print(f"✅ Registered schema: {user_schema.id}")
    
    # Test valid user data
    print("\nTesting valid user data...")
    valid_user = {
        "user_id": "user_12345",
        "username": "johndoe",
        "email": "john.doe@example.com",
        "profile": {
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
            "preferences": ["tech", "sports", "music"]
        },
        "created_at": datetime.now().isoformat()
    }
    
    try:
        Schema.validate_payload(user_schema.id, valid_user)
        print("✅ User data is valid")
    except Error as e:
        print(f"❌ User validation failed: {e}")
    
    # Test invalid user data
    print("\nTesting invalid user data...")
    invalid_user = {
        "user_id": "user_67890",
        "username": "janedoe",
        "email": "jane.doe@example.com",
        "profile": {
            "first_name": "Jane",
            # Missing required last_name
            "age": "twenty-five"  # Wrong type - should be integer
        }
    }
    
    try:
        Schema.validate_payload(user_schema.id, invalid_user)
        print("❌ This should have failed!")
    except Error as e:
        print(f"✅ Expected validation error: {e}")


async def notification_schema_example():
    """Create and use a notification schema."""
    print("\n=== Notification Schema Example ===")
    
    # Create notification schema
    notification_schema = Schema(
        id="myapp:notification.system.v1",
        name="System Notification",
        version="v1",
        description="System-wide notification schema",
        schema_def={
            "type": "object",
            "properties": {
                "notification_id": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["info", "warning", "error", "success"]
                },
                "title": {"type": "string"},
                "message": {"type": "string"},
                "timestamp": {"type": "string"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"]
                },
                "metadata": {"type": "object"},
                "expires_at": {"type": "string"}
            },
            "required": ["notification_id", "type", "title", "message", "timestamp", "priority"]
        }
    )
    
    # Register schema
    notification_schema.register()
    print(f"✅ Registered notification schema: {notification_schema.id}")
    
    # Create different types of notifications
    notifications = [
        {
            "notification_id": "notif_001",
            "type": "info",
            "title": "System Update",
            "message": "System will be updated tonight at 2 AM",
            "timestamp": datetime.now().isoformat(),
            "priority": "medium",
            "metadata": {"component": "system", "version": "1.2.3"}
        },
        {
            "notification_id": "notif_002", 
            "type": "error",
            "title": "Database Connection Failed",
            "message": "Unable to connect to primary database",
            "timestamp": datetime.now().isoformat(),
            "priority": "urgent",
            "metadata": {"component": "database", "error_code": "DB_CONN_001"}
        },
        {
            "notification_id": "notif_003",
            "type": "success",
            "title": "Backup Completed",
            "message": "Daily backup completed successfully",
            "timestamp": datetime.now().isoformat(),
            "priority": "low",
            "metadata": {"component": "backup", "size_mb": 1024}
        }
    ]
    
    # Validate all notifications
    print("\nValidating notifications...")
    for i, notification in enumerate(notifications, 1):
        try:
            Schema.validate_payload(notification_schema.id, notification)
            print(f"✅ Notification {i} ({notification['type']}) is valid")
        except Error as e:
            print(f"❌ Notification {i} validation failed: {e}")


async def schema_messaging_example():
    """Demonstrate using schemas in actual agent messaging."""
    print("\n=== Schema Messaging Example ===")
    
    # Create a task assignment schema
    task_schema = Schema(
        id="myapp:task.assignment.v1",
        name="Task Assignment",
        version="v1",
        description="Task assignment between agents",
        schema_def={
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "task_type": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "assigned_to": {"type": "string"},
                "assigned_by": {"type": "string"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"]
                },
                "due_date": {"type": "string"},
                "estimated_hours": {"type": "number"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["task_id", "task_type", "title", "assigned_to", "assigned_by", "priority"]
        }
    )
    
    # Register schema
    task_schema.register()
    print(f"✅ Registered task schema: {task_schema.id}")
    
    # Create agents
    manager_amtp = AMTP(
        address="manager",
        gateway_url="http://localhost:8080",
        tls_enabled=False
    )
    
    worker_amtp = AMTP(
        address="worker",
        gateway_url="http://localhost:8080",
        tls_enabled=False
    )
    
    # Set up worker to handle task assignments
    @worker_amtp.on_message
    async def handle_task_assignment(message: Message):
        if message.schema == task_schema.id:
            task = message.payload
            print(f"🔧 Worker received task: {task['title']}")
            print(f"   Priority: {task['priority']}")
            print(f"   Estimated hours: {task.get('estimated_hours', 'Not specified')}")
            
            # Simulate task processing
            await asyncio.sleep(1)
            
            return {
                "status": "accepted",
                "task_id": task["task_id"],
                "estimated_completion": "2025-01-15T10:00:00Z",
                "worker": worker_amtp.address
            }
        else:
            return {"status": "unknown_message_type"}
    
    try:
        # Start both agents
        print("\nStarting agents...")
        await manager_amtp.start()
        await worker_amtp.start()
        
        # Create task assignment data
        task_data = {
            "task_id": "TASK-001",
            "task_type": "development",
            "title": "Implement user authentication",
            "description": "Add OAuth2 authentication to the user service",
            "assigned_to": worker_amtp.address,
            "assigned_by": manager_amtp.address,
            "priority": "high",
            "due_date": "2025-01-15T23:59:59Z",
            "estimated_hours": 8.5,
            "tags": ["backend", "security", "oauth2"]
        }
        
        # Validate task data
        print("\nValidating task data...")
        try:
            Schema.validate_payload(task_schema.id, task_data)
            print("✅ Task data is valid")
        except Error as e:
            print(f"❌ Task validation failed: {e}")
            return
        
        # Send schema-validated task assignment
        print("\nSending task assignment...")
        task_message = Message(
            sender=manager_amtp.address,
            recipients=[worker_amtp.address],
            subject="New Task Assignment",
            schema=task_schema.id,
            payload=task_data
        )
        
        message_id = await manager_amtp.send(task_message)
        print(f"✅ Task assignment sent: {message_id}")
        
        # Wait a bit for processing
        await asyncio.sleep(2)
        
    except Error as e:
        print(f"❌ Error in messaging example: {e}")
    finally:
        print("\nStopping agents...")
        await manager_amtp.stop()
        await worker_amtp.stop()


async def schema_registry_example():
    """Demonstrate schema registry operations."""
    print("\n=== Schema Registry Example ===")
    
    # List all registered schemas
    print("Currently registered schemas:")
    schemas = Schema.list_schemas()
    for schema_id in schemas:
        schema = Schema.get(schema_id)
        print(f"  - {schema_id}: {schema.name} ({schema.version})")
    
    # Create multiple related schemas
    print("\nRegistering related schemas...")
    
    # Base event schema
    event_schema = Schema(
        id="myapp:event.base.v1",
        name="Base Event",
        version="v1",
        description="Base schema for all events",
        schema_def={
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "event_type": {"type": "string"},
                "timestamp": {"type": "string"},
                "source": {"type": "string"},
                "data": {"type": "object"}
            },
            "required": ["event_id", "event_type", "timestamp", "source"]
        }
    )
    event_schema.register()
    
    # User event schema (extends base)
    user_event_schema = Schema(
        id="myapp:event.user.v1",
        name="User Event",
        version="v1",
        description="User-related events",
        schema_def={
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "event_type": {"type": "string"},
                "timestamp": {"type": "string"},
                "source": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "action": {"type": "string"},
                        "details": {"type": "object"}
                    },
                    "required": ["user_id", "action"]
                }
            },
            "required": ["event_id", "event_type", "timestamp", "source", "data"]
        }
    )
    user_event_schema.register()
    
    print(f"✅ Registered: {event_schema.id}")
    print(f"✅ Registered: {user_event_schema.id}")
    
    # Test user event
    user_event_data = {
        "event_id": "evt_001",
        "event_type": "user_login",
        "timestamp": datetime.now().isoformat(),
        "source": "auth_service",
        "data": {
            "user_id": "user_12345",
            "action": "login",
            "details": {
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "success": True
            }
        }
    }
    
    try:
        Schema.validate_payload(user_event_schema.id, user_event_data)
        print("✅ User event data is valid")
    except Error as e:
        print(f"❌ User event validation failed: {e}")
    
    # Show final registry state
    print(f"\nFinal registry contains {len(Schema.list_schemas())} schemas:")
    for schema_id in sorted(Schema.list_schemas()):
        schema = Schema.get(schema_id)
        print(f"  - {schema_id}: {schema.name}")


async def main():
    """Run all schema examples."""
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise for examples
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("AMTP Schema Examples")
    print("===================")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    try:
        await basic_schema_validation_example()
        await custom_schema_creation_example()
        await notification_schema_example()
        await schema_messaging_example()
        await schema_registry_example()
        
        print("\n=== All Schema Examples Completed ===")
        
    except Exception as e:
        print(f"\nExample failed: {e}")
        logging.error(f"Schema example error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
