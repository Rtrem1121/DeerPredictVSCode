#!/usr/bin/env python3
"""
Async HTTP Client Service

Provides async HTTP client functionality with connection pooling,
retry logic, and proper resource management.

Author: System Refactoring - Phase 2
Version: 2.0.0
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import json

try:
    import aiohttp
    import aiofiles
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from backend.services.base_service import BaseService, Result, AppError, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class HttpResponse:
    """HTTP response data structure"""
    status_code: int
    data: Union[Dict[str, Any], str, bytes]
    headers: Dict[str, str]
    url: str
    elapsed_ms: float


class AsyncHttpService(BaseService):
    """
    Async HTTP client service with connection pooling and retry logic
    
    Features:
    - Connection pooling for performance
    - Automatic retry with exponential backoff
    - Request/response logging
    - Timeout management
    - Resource cleanup
    """
    
    def __init__(self, 
                 timeout_seconds: float = 30.0,
                 max_connections: int = 100,
                 max_retries: int = 3):
        super().__init__()
        self.timeout_seconds = timeout_seconds
        self.max_connections = max_connections
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        
        if not AIOHTTP_AVAILABLE:
            self.logger.warning("aiohttp not available - HTTP functionality limited")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP client session with connection pooling"""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp not installed - cannot create HTTP session")
        
        if self._session is None or self._session.closed:
            # Create connector with connection pooling
            self._connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            # Create timeout configuration
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            
            # Create session with connector and timeout
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'DeerPredictionApp/2.0 AsyncHttpService'
                }
            )
            
            self.logger.debug("Created new HTTP session with connection pooling")
        
        return self._session
    
    async def get(self, url: str, 
                  params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None) -> Result[HttpResponse]:
        """
        Perform async GET request with retry logic
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Result containing HttpResponse or error
        """
        return await self._request('GET', url, params=params, headers=headers)
    
    async def post(self, url: str,
                   data: Optional[Dict[str, Any]] = None,
                   json_data: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None) -> Result[HttpResponse]:
        """
        Perform async POST request with retry logic
        
        Args:
            url: Request URL
            data: Form data
            json_data: JSON payload
            headers: Additional headers
            
        Returns:
            Result containing HttpResponse or error
        """
        return await self._request('POST', url, data=data, json_data=json_data, headers=headers)
    
    async def _request(self, method: str, url: str,
                      params: Optional[Dict[str, Any]] = None,
                      data: Optional[Dict[str, Any]] = None,
                      json_data: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None) -> Result[HttpResponse]:
        """
        Internal request method with retry logic and error handling
        """
        try:
            self.log_operation_start("http_request", method=method, url=url)
            
            if not AIOHTTP_AVAILABLE:
                return Result.failure(AppError(
                    ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
                    "HTTP client not available - aiohttp not installed",
                    {"method": method, "url": url}
                ))
            
            last_exception = None
            
            # Retry loop with exponential backoff
            for attempt in range(self.max_retries + 1):
                try:
                    session = await self._get_session()
                    
                    # Prepare request kwargs
                    kwargs = {}
                    if params:
                        kwargs['params'] = params
                    if data:
                        kwargs['data'] = data
                    if json_data:
                        kwargs['json'] = json_data
                    if headers:
                        kwargs['headers'] = headers
                    
                    # Measure request time
                    start_time = asyncio.get_event_loop().time()
                    
                    # Perform request
                    async with session.request(method, url, **kwargs) as response:
                        end_time = asyncio.get_event_loop().time()
                        elapsed_ms = (end_time - start_time) * 1000
                        
                        # Read response data
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'application/json' in content_type:
                            response_data = await response.json()
                        elif 'text/' in content_type:
                            response_data = await response.text()
                        else:
                            response_data = await response.read()
                        
                        # Create response object
                        http_response = HttpResponse(
                            status_code=response.status,
                            data=response_data,
                            headers=dict(response.headers),
                            url=str(response.url),
                            elapsed_ms=elapsed_ms
                        )
                        
                        # Check if response indicates success
                        if 200 <= response.status < 300:
                            self.log_operation_success("http_request", 
                                                     status_code=response.status,
                                                     elapsed_ms=elapsed_ms,
                                                     attempt=attempt + 1)
                            return Result.success(http_response)
                        else:
                            # Handle HTTP error status
                            error = AppError(
                                ErrorCode.EXTERNAL_API_ERROR,
                                f"HTTP {response.status}: {response.reason}",
                                {
                                    "method": method,
                                    "url": url,
                                    "status_code": response.status,
                                    "response_data": response_data if isinstance(response_data, (str, dict)) else str(response_data)[:500]
                                }
                            )
                            
                            # Don't retry on client errors (4xx)
                            if 400 <= response.status < 500:
                                self.logger.warning(f"Client error {response.status} for {method} {url}")
                                return Result.failure(error)
                            
                            # Retry on server errors (5xx)
                            if attempt < self.max_retries:
                                delay = 2 ** attempt  # Exponential backoff
                                self.logger.warning(f"Server error {response.status} for {method} {url}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                                await asyncio.sleep(delay)
                                continue
                            else:
                                return Result.failure(error)
                        
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_exception = e
                    
                    if attempt < self.max_retries:
                        delay = 2 ** attempt  # Exponential backoff
                        self.logger.warning(f"Request failed for {method} {url}: {str(e)}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break
            
            # All retries exhausted
            error = self.handle_unexpected_error("http_request", last_exception, 
                                                method=method, url=url, max_retries=self.max_retries)
            return Result.failure(error)
            
        except Exception as e:
            error = self.handle_unexpected_error("http_request", e, method=method, url=url)
            return Result.failure(error)
    
    async def download_file(self, url: str, file_path: str,
                           chunk_size: int = 8192) -> Result[str]:
        """
        Download file asynchronously with progress tracking
        
        Args:
            url: File URL
            file_path: Local file path to save
            chunk_size: Download chunk size in bytes
            
        Returns:
            Result containing file path or error
        """
        try:
            self.log_operation_start("download_file", url=url, file_path=file_path)
            
            if not AIOHTTP_AVAILABLE:
                return Result.failure(AppError(
                    ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
                    "File download not available - aiohttp not installed",
                    {"url": url, "file_path": file_path}
                ))
            
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status != 200:
                    return Result.failure(AppError(
                        ErrorCode.EXTERNAL_API_ERROR,
                        f"Download failed with status {response.status}",
                        {"url": url, "status_code": response.status}
                    ))
                
                # Use aiofiles for async file writing
                try:
                    import aiofiles
                    async with aiofiles.open(file_path, 'wb') as file:
                        downloaded_bytes = 0
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            downloaded_bytes += len(chunk)
                    
                    self.log_operation_success("download_file", 
                                             file_path=file_path,
                                             downloaded_bytes=downloaded_bytes)
                    return Result.success(file_path)
                    
                except ImportError:
                    # Fallback to synchronous file writing
                    with open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            file.write(chunk)
                    
                    return Result.success(file_path)
            
        except Exception as e:
            error = self.handle_unexpected_error("download_file", e, url=url, file_path=file_path)
            return Result.failure(error)
    
    async def health_check(self) -> Result[Dict[str, Any]]:
        """Check HTTP client health and connection status"""
        try:
            health_data = {
                "service": "AsyncHttpService",
                "status": "healthy",
                "session_active": self._session is not None and not self._session.closed,
                "max_connections": self.max_connections,
                "timeout_seconds": self.timeout_seconds,
                "aiohttp_available": AIOHTTP_AVAILABLE
            }
            
            if self._connector:
                health_data.update({
                    "connections_acquired": getattr(self._connector, '_acquired', 0),
                    "connections_available": getattr(self._connector, '_available_connections', 0)
                })
            
            return Result.success(health_data)
            
        except Exception as e:
            error = self.handle_unexpected_error("health_check", e)
            return Result.failure(error)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown HTTP client and connections"""
        try:
            if self._session and not self._session.closed:
                await self._session.close()
                self.logger.debug("HTTP session closed")
            
            if self._connector:
                await self._connector.close()
                self.logger.debug("HTTP connector closed")
            
            # Wait for connections to close
            await asyncio.sleep(0.1)
            
        except Exception as e:
            self.logger.error(f"Error during HTTP service shutdown: {e}")


# Factory function for dependency injection
def create_async_http_service() -> AsyncHttpService:
    """Create a new AsyncHttpService instance"""
    return AsyncHttpService()
