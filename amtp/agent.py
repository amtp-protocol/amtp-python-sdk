"""
AMTP Protocol Implementation

A simple, all-in-one AMTP implementation that handles gateway connection, registration,
message sending/receiving, and message processing.
"""

import asyncio
import aiohttp
import json
import logging
import ssl
from typing import Optional, Dict, Any, List, Callable, Awaitable
from datetime import datetime
from urllib.parse import urljoin

from .message import Message
from .error import Error


logger = logging.getLogger(__name__)


class AMTP:
    """
    AMTP Protocol Implementation - handles everything needed for AMTP communication.
    
    Features:
    - Gateway connection and registration
    - Message sending and receiving
    - Message processing with handlers
    - Pull/push delivery modes
    - Automatic reconnection and error handling
    """
    
    def __init__(self, address: str, gateway_url: str, 
                 delivery_mode: str = "pull",
                 api_key: Optional[str] = None,
                 tls_enabled: bool = True,
                 **kwargs):
        """
        Initialize AMTP connection.
        
        Args:
            address: AMTP address (e.g., "my-agent@company.com")
            gateway_url: AMTP gateway URL
            delivery_mode: "pull" or "push"
            api_key: API key for authentication
            tls_enabled: Enable TLS/SSL
            **kwargs: Additional configuration options
        """
        self.address = address
        self.gateway_url = gateway_url
        self.delivery_mode = delivery_mode
        self.api_key = api_key
        self.tls_enabled = tls_enabled
        
        # Configuration
        self.config = {
            'connect_timeout': kwargs.get('connect_timeout', 30),
            'read_timeout': kwargs.get('read_timeout', 60),
            'max_retries': kwargs.get('max_retries', 3),
            'retry_delay': kwargs.get('retry_delay', 1.0),
            'poll_interval': kwargs.get('poll_interval', 5.0),
            'max_message_size': kwargs.get('max_message_size', 10 * 1024 * 1024),  # 10MB
            'log_level': kwargs.get('log_level', 'INFO'),
        }
        
        # Internal state
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._registered = False
        self._message_handler: Optional[Callable[[Message], Awaitable[Optional[Dict[str, Any]]]]] = None
        self._error_handler: Optional[Callable[[Exception], Awaitable[None]]] = None
        
        # Setup logging
        log_level = getattr(logging, self.config['log_level'].upper())
        logging.basicConfig(level=log_level)
        self.logger = logging.getLogger(f"amtp.{self.address}")
        
        self.logger.info(f"AMTP {self.address} initialized for gateway {self.gateway_url}")
    
    async def connect(self):
        """Connect to the AMTP gateway."""
        if self._session:
            return
        
        # Create SSL context
        ssl_context = None
        if self.tls_enabled:
            ssl_context = ssl.create_default_context()
        
        # Create session
        timeout = aiohttp.ClientTimeout(
            connect=self.config['connect_timeout'],
            sock_read=self.config['read_timeout']
        )
        
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )
        
        # Test connection
        try:
            await self._request("GET", "/health")
            self.logger.info("Connected to AMTP gateway")
        except Exception as e:
            await self.close()
            raise Error(f"Failed to connect to gateway: {e}")
    
    async def close(self):
        """Close connection to gateway."""
        if self._session:
            await self._session.close()
            self._session = None
        self.logger.info("Disconnected from gateway")
    
    async def register(self):
        """Register with the AMTP gateway."""
        if self._registered:
            return
        
        data = {
            "address": self.address,
            "delivery_mode": self.delivery_mode
        }
        
        try:
            response = await self._request("POST", "/v1/admin/agents", data)            
            # Extract API key and full address from response - it's nested in the agent object
            agent_data = response.get("agent", {})
            self.api_key = (agent_data.get("api_key") or
                           response.get("api_key") or
                           response.get("token") or
                           response.get("access_token") or
                           self.api_key)
            
            # Update address to the full address returned by the gateway
            if agent_data.get("address"):
                self.address = agent_data["address"]
            self._registered = True
            self.logger.info(f"Registered with {self.delivery_mode} delivery mode")
            if self.api_key:
                self.logger.debug(f"Received API key: {self.api_key[:8]}...")
            else:
                self.logger.warning("No API key received from gateway")
        except Exception as e:
            raise Error(f"Failed to register: {e}")
    
    async def unregister(self):
        """Unregister from AMTP gateway."""
        if not self._registered:
            return
        
        try:
            # Extract agent name from full address (e.g., "manager@localhost" -> "manager")
            agent_name = self.address.split('@')[0] if '@' in self.address else self.address
            await self._request("DELETE", f"/v1/admin/agents/{agent_name}")
            self._registered = False
            self.logger.info("Unregistered from gateway")
        except Exception as e:
            self.logger.warning(f"Failed to unregister: {e}")
    
    async def send(self, message: Message) -> str:
        """
        Send a message.
        
        Args:
            message: Message to send
            
        Returns:
            str: Message ID
        """
        if not self._session:
            await self.connect()
        
        # Validate message
        if not message.sender:
            message.sender = self.address
        
        message.validate()
        
        # Check size
        size = len(json.dumps(message.to_dict()).encode('utf-8'))
        if size > self.config['max_message_size']:
            raise Error(f"Message too large: {size} bytes (max: {self.config['max_message_size']})")
        
        try:
            response = await self._request("POST", "/v1/messages", message.to_dict())
            message_id = response.get("message_id", message.message_id)
            self.logger.info(f"Message {message_id} sent to {len(message.recipients)} recipients")
            return message_id
        except Exception as e:
            raise Error(f"Failed to send message: {e}")
    
    async def receive(self, limit: int = 10) -> List[Message]:
        """
        Receive messages from inbox (pull mode only).
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List[Message]: Received messages
        """
        if self.delivery_mode != "pull":
            raise Error("receive() only works in pull delivery mode")
        
        # For development setups, API key might not be required
        # We'll try the request and let the gateway decide if auth is needed
        
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await self._request(
                "GET", 
                f"/v1/inbox/{self.address}",
                params={"limit": limit},
                headers=headers if headers else None
            )
            
            messages = []
            if response and "messages" in response and response["messages"]:
                for msg_data in response["messages"]:
                    messages.append(Message.from_dict(msg_data))
            
            return messages
        except Exception as e:
            raise Error(f"Failed to receive messages: {e}")
    
    async def acknowledge(self, message_id: str):
        """
        Acknowledge a received message (pull mode only).
        
        Args:
            message_id: Message ID to acknowledge
        """
        if self.delivery_mode != "pull":
            raise Error("acknowledge() only works in pull delivery mode")
        
        # For development setups, API key might not be required
        # We'll try the request and let the gateway decide if auth is needed
        
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            await self._request(
                "DELETE",
                f"/v1/inbox/{self.address}/{message_id}",
                headers=headers if headers else None
            )
            self.logger.debug(f"Message {message_id} acknowledged")
        except Exception as e:
            raise Error(f"Failed to acknowledge message: {e}")
    
    def on_message(self, handler: Callable[[Message], Awaitable[Optional[Dict[str, Any]]]]):
        """
        Register message handler.
        
        Args:
            handler: Async function that processes messages
        """
        self._message_handler = handler
        self.logger.info("Message handler registered")
    
    def on_error(self, handler: Callable[[Exception], Awaitable[None]]):
        """
        Register error handler.
        
        Args:
            handler: Async function that handles errors
        """
        self._error_handler = handler
        self.logger.info("Error handler registered")
    
    async def start(self):
        """Start AMTP connection (connect, register, begin processing)."""
        if self._running:
            return
        
        self.logger.info(f"Starting AMTP connection for {self.address}")
        
        try:
            await self.connect()
            await self.register()
            self._running = True
            
            if self.delivery_mode == "pull":
                # Start message polling loop
                asyncio.create_task(self._message_loop())
            
            self.logger.info("AMTP connection started successfully")
        except Exception as e:
            # Ensure cleanup happens even if start fails
            try:
                await self.close()
            except Exception as cleanup_error:
                self.logger.warning(f"Error during cleanup: {cleanup_error}")
            raise Error(f"Failed to start AMTP connection: {e}")
    
    async def stop(self):
        """Stop AMTP connection (unregister, disconnect)."""
        if not self._running:
            return
        
        self.logger.info("Stopping AMTP connection")
        self._running = False
        
        # Only try to unregister if we were actually registered
        if self._registered:
            try:
                await self.unregister()
            except Exception as e:
                self.logger.warning(f"Error during unregister: {e}")
        
        await self.close()
        self.logger.info("AMTP connection stopped")
    
    async def run(self):
        """Run AMTP connection forever (until interrupted)."""
        await self.start()
        
        try:
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            await self.stop()
    
    async def _message_loop(self):
        """Message processing loop for pull mode."""
        # Warn if no API key is available, but continue for development setups
        if not self.api_key:
            self.logger.warning("No API key available - continuing without authentication")
            
        while self._running:
            try:
                messages = await self.receive()
                
                for message in messages:
                    try:
                        # Process message
                        response = None
                        if self._message_handler:
                            response = await self._message_handler(message)
                        
                        # Send response if provided
                        if response and message.sender:
                            reply = Message(
                                sender=self.address,
                                recipients=[message.sender],
                                subject=f"Re: {message.subject or 'Message'}",
                                payload=response,
                                in_reply_to=message.message_id
                            )
                            await self.send(reply)
                        
                        # Acknowledge message
                        await self.acknowledge(message.message_id)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing message {message.message_id}: {e}")
                        if self._error_handler:
                            try:
                                await self._error_handler(e)
                            except Exception as handler_error:
                                self.logger.error(f"Error in error handler: {handler_error}")
                
                # Wait before next poll
                await asyncio.sleep(self.config['poll_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
                if self._error_handler:
                    try:
                        await self._error_handler(e)
                    except Exception as handler_error:
                        self.logger.error(f"Error in error handler: {handler_error}")
                
                # Wait before retrying
                await asyncio.sleep(self.config['retry_delay'])
    
    async def _request(self, method: str, endpoint: str, 
                      data: Optional[Dict[str, Any]] = None,
                      params: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make HTTP request to gateway."""
        if not self._session:
            await self.connect()
        
        url = urljoin(self.gateway_url, endpoint)
        request_headers = {}
        
        if self.api_key:
            request_headers["Authorization"] = f"Bearer {self.api_key}"
        
        if headers:
            request_headers.update(headers)
        
        for attempt in range(self.config['max_retries']):
            try:
                async with self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=request_headers
                ) as response:
                    
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                    else:
                        response_data = {"message": await response.text()}
                    
                    if response.status in (200, 201, 202):
                        # Handle empty responses gracefully
                        return response_data if response_data is not None else {}
                    elif response.status == 400:
                        raise Error(f"Bad request: {response_data.get('error', 'Unknown error')}")
                    elif response.status == 401:
                        raise Error("Authentication failed")
                    elif response.status == 404:
                        raise Error("Not found")
                    elif response.status == 429:
                        raise Error("Rate limited")
                    else:
                        raise Error(f"HTTP {response.status}: {response_data.get('error', 'Unknown error')}")
            
            except aiohttp.ClientError as e:
                if attempt == self.config['max_retries'] - 1:
                    raise Error(f"Request failed: {e}")
                await asyncio.sleep(self.config['retry_delay'] * (2 ** attempt))
            except asyncio.TimeoutError:
                if attempt == self.config['max_retries'] - 1:
                    raise Error("Request timed out")
                await asyncio.sleep(self.config['retry_delay'] * (2 ** attempt))
    
    def __repr__(self) -> str:
        return f"AMTP(address='{self.address}', gateway='{self.gateway_url}')"