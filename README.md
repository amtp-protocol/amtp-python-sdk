# AMTP Python SDK

A simple Python SDK for building AI agents using the Agent Message Transfer Protocol (AMTP) v1.0.

## Overview

The AMTP Python SDK provides a clean, simple framework for creating AI agents that communicate reliably across organizational boundaries using structured messaging and multi-agent coordination.

## Features

### Core Capabilities
- **Universal Addressing**: `agent@domain` format with DNS-based discovery
- **Message Validation**: Comprehensive AMTP message structure validation
- **Protocol Compliance**: Full AMTP v1.0 specification implementation
- **Federated Architecture**: Decentralized communication across domains
- **Schema Integration**: User-defined schema validation for structured data
- **Reliability**: At-least-once delivery with idempotency guarantees

### SDK Features
- **Simple API**: Just 4 core classes - Agent, Message, Schema, Error
- **Async/Await Support**: Built on asyncio for high-performance concurrent operations
- **Flexible Configuration**: Simple constructor-based configuration
- **Comprehensive Error Handling**: Single Error class for all error scenarios
- **Type Safety**: Full type hints and dataclass-based messages
- **Extensible Design**: Easy to extend with custom schemas and handlers

## Quick Start

### Installation

```bash
pip install amtp
```

For development with all optional dependencies:
```bash
pip install amtp[dev,yaml,examples]
```

### Basic Usage

#### Simple Agent

```python
import asyncio
from amtp import AMTP, Message

# Create AMTP connection
amtp = AMTP("my-agent@company.com", "https://amtp.company.com")

# Handle messages
@amtp.on_message
async def handle_message(message):
    print(f"Received: {message.subject}")
    return {"status": "processed", "response": "Hello back!"}

# Send a message
message = Message(
    sender="my-agent@company.com",
    recipients=["user@partner.com"],
    subject="Hello from AI Agent",
    payload={"greeting": "Hello, World!"}
)

async def main():
    await amtp.send(message)
    await amtp.run()  # Run forever

asyncio.run(main())
```

#### Direct Message Sending

```python
import asyncio
from amtp import AMTP, Message

async def send_message():
    amtp = AMTP("sender@company.com", "https://amtp.company.com")
    await amtp.start()
    
    message = Message(
        sender="sender@company.com",
        recipients=["recipient@partner.com"],
        subject="Hello from AMTP",
        payload={"greeting": "Hello, World!"}
    )
    
    message_id = await amtp.send(message)
    print(f"Message sent: {message_id}")
    
    await amtp.stop()

asyncio.run(send_message())
```

### Schema Validation

```python
from amtp import AMTP, Message, Schema

# Create your own schema
order_schema = Schema(
    id="myapp:commerce.order.v1",
    name="Order Schema",
    version="v1",
    schema_def={
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "customer": {"type": "object"},
            "items": {"type": "array"},
            "total": {"type": "number"}
        },
        "required": ["order_id", "customer", "items", "total"]
    }
)
order_schema.register()

# Use your schema in messages
message = Message(
    sender="sender@company.com",
    recipients=["recipient@partner.com"],
    subject="Order Processing",
    schema="myapp:commerce.order.v1",
    payload={
        "order_id": "ORD-12345",
        "customer": {"name": "John Doe", "email": "john@example.com"},
        "items": [{"sku": "WIDGET-001", "quantity": 2, "price": 29.99}],
        "total": 59.98
    }
)

# Create custom schema
custom_schema = Schema(
    id="myapp:notification.alert.v1",
    name="Alert Notification",
    version="v1",
    schema_def={
        "type": "object",
        "properties": {
            "alert_type": {"type": "string"},
            "severity": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": ["alert_type", "severity", "message"]
    }
)
custom_schema.register()
```


## Configuration

### Simple Configuration

```python
from amtp import AMTP

# Basic configuration
amtp = AMTP(
    address="my-agent@company.com",
    gateway_url="https://amtp.company.com",
    delivery_mode="pull",  # or "push"
    tls_enabled=True,
    api_key="your-api-key"
)
```

### Advanced Configuration

```python
amtp = AMTP(
    address="my-agent@company.com",
    gateway_url="https://amtp.company.com",
    delivery_mode="pull",
    tls_enabled=True,
    connect_timeout=30,
    read_timeout=60,
    max_retries=3,
    retry_delay=1.0,
    poll_interval=5.0,
    log_level="INFO"
)
```

## Advanced Features

### Message Handlers

```python
from amtp import AMTP, Message

amtp = AMTP("my-agent@company.com", "https://amtp.company.com")

@amtp.on_message
async def handle_message(message: Message):
    if message.schema == "agntcy:commerce.order.v1":
        # Handle order
        return {"status": "order_processed", "order_id": message.payload["order_id"]}
    
    elif message.coordination_type == "parallel":
        # Handle workflow
        return {"status": "workflow_step_completed"}
    
    else:
        # Default handling
        return {"status": "received", "message": "Message processed"}

@amtp.on_error
async def handle_error(error):
    print(f"Error occurred: {error}")
```

### Error Handling

```python
from amtp import AMTP, Message, Error

async def robust_messaging():
    amtp = AMTP("my-agent@company.com", "https://amtp.company.com")
    
    try:
        await amtp.start()
        
        message = Message(
            sender="my-agent@company.com",
            recipients=["recipient@partner.com"],
            subject="Test Message",
            payload={"data": "test"}
        )
        
        message_id = await amtp.send(message)
        print(f"Message sent: {message_id}")
        
    except Error as e:
        print(f"AMTP Error: {e}")
        if e.details:
            print(f"Details: {e.details}")
    
    finally:
        await amtp.stop()
```

### Custom Schemas

```python
from amtp import Schema

# Create custom schema
notification_schema = Schema(
    id="myapp:notification.system.v1",
    name="System Notification",
    version="v1",
    description="System-wide notification schema",
    schema_def={
        "type": "object",
        "properties": {
            "event_type": {"type": "string"},
            "timestamp": {"type": "string"},
            "data": {"type": "object"}
        },
        "required": ["event_type", "timestamp"]
    }
)

# Register schema
notification_schema.register()

# Validate data
try:
    Schema.validate_payload("myapp:notification.system.v1", {
        "event_type": "user_login",
        "timestamp": "2025-01-01T12:00:00Z",
        "data": {"user_id": "123"}
    })
    print("Data is valid!")
except Error as e:
    print(f"Validation failed: {e}")
```

## Examples

The SDK includes comprehensive examples in the `examples/` directory:

- **`simple_agent.py`**: Basic AMTP connection with message handling
- **`schema_example.py`**: Schema registration and validation

Run examples:
```bash
# Start simple AMTP connection
python examples/simple_agent.py

# Run schema examples
python examples/schema_example.py
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/amtp-protocol/amtp-python-sdk.git
cd amtp-python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]
```

### Building and Publishing

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

## API Reference

### Core Classes

- **`AMTP`**: All-in-one AMTP implementation with gateway connection, registration, and message processing
- **`Message`**: AMTP message representation with validation and serialization
- **`Schema`**: Schema registration and validation for structured messages
- **`Error`**: Simple error handling for all AMTP operations

### Message Types

- **Text Messages**: Simple text-based communication
- **Schema Messages**: Structured data with validation
- **Workflow Messages**: Multi-agent coordination
- **Reply Messages**: Response to received messages

### Delivery Modes

- **Pull Mode**: Agent polls gateway for messages
- **Push Mode**: Gateway pushes messages to agent endpoint

## Protocol Compliance

This SDK implements the complete AMTP v1.0 specification:

- ✅ Universal addressing (`agent@domain`)
- ✅ DNS-based capability discovery
- ✅ Message structure validation
- ✅ At-least-once delivery semantics
- ✅ Idempotency guarantees
- ✅ Multi-agent coordination patterns
- ✅ Schema validation framework
- ✅ TLS 1.3 security
- ✅ Error handling and retry logic


## Security

Security features and best practices:

- **TLS 1.3**: Mandatory encryption for production
- **API Key Authentication**: Secure AMTP authentication
- **Message Validation**: Comprehensive input validation
- **Schema Validation**: Structured data validation
- **Error Handling**: Secure error messages
- **Audit Logging**: Security event tracking

## Reporting Issues

Please report bugs and feature requests through [GitHub Issues](https://github.com/amtp-protocol/amtp-python-sdk/issues).

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
