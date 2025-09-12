"""
Request Service

API request handling, retry logic, and error management for AI providers.
Consolidates request patterns and provides consistent error handling.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional


class RequestStatus(Enum):
    """Status of an AI request."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class RequestResult:
    """Result of an AI request."""

    status: RequestStatus
    content: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    total_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RetryConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for request retry logic."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    timeout: float = 90.0

    # Specific error handling
    retry_on_network_error: bool = True
    retry_on_rate_limit: bool = True
    retry_on_server_error: bool = True
    retry_on_timeout: bool = True


class RequestService:
    """Centralized AI request handling with retry logic and error management."""

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """Initialize request service with retry configuration."""
        self.retry_config = retry_config or RetryConfig()
        self.logger = logging.getLogger(__name__)
        self._active_requests: Dict[str, RequestResult] = {}

    def make_ai_request(
        self,
        provider_func: Callable[[], str],
        request_id: Optional[str] = None,
        timeout: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> RequestResult:
        """Make AI request with retry logic and error handling.

        Args:
            provider_func: Function that makes the actual AI API call
            request_id: Optional unique identifier for tracking
            timeout: Override timeout for this request
            retry_config: Override retry config for this request

        Returns:
            RequestResult with the outcome
        """
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"

        config = retry_config or self.retry_config
        actual_timeout = timeout or config.timeout

        # Initialize request tracking
        result = RequestResult(status=RequestStatus.PENDING)
        self._active_requests[request_id] = result

        start_time = time.time()
        attempt = 0

        while attempt < config.max_attempts:
            attempt += 1
            result.attempts = attempt
            result.status = RequestStatus.IN_PROGRESS

            try:
                self.logger.debug(
                    "AI request attempt %d/%d for %s", attempt, config.max_attempts, request_id
                )

                # Make the actual request with timeout
                content = self._execute_with_timeout(provider_func, actual_timeout)

                # Success
                result.status = RequestStatus.SUCCESS
                result.content = content
                result.total_time = time.time() - start_time

                self.logger.info("AI request %s succeeded on attempt %d", request_id, attempt)
                break

            except Exception as e:
                error_msg = str(e)
                result.error = error_msg
                result.total_time = time.time() - start_time

                self.logger.warning(
                    "AI request %s attempt %d failed: %s", request_id, attempt, error_msg
                )

                # Determine if we should retry
                if attempt >= config.max_attempts:
                    result.status = RequestStatus.FAILED
                    self.logger.error("AI request %s failed after %d attempts", request_id, attempt)
                    break

                if not self._should_retry_error(e, config):
                    result.status = RequestStatus.FAILED
                    self.logger.error(
                        "AI request %s failed with non-retryable error: %s", request_id, error_msg
                    )
                    break

                # Calculate retry delay
                result.status = RequestStatus.RETRYING
                delay = self._calculate_retry_delay(attempt, config)

                self.logger.info(
                    "Retrying AI request %s in %.1fs (attempt %d)", request_id, delay, attempt + 1
                )
                time.sleep(delay)

        # Clean up request tracking
        if request_id in self._active_requests:
            del self._active_requests[request_id]

        return result

    def _execute_with_timeout(self, func: Callable[[], str], timeout: float) -> Optional[str]:
        """Execute function with timeout."""
        import signal
        import threading

        if hasattr(signal, "alarm"):  # Unix systems

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Request timed out after {timeout} seconds")

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))

            try:
                result = func()
                signal.alarm(0)  # Cancel alarm
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)

        else:  # Windows or systems without signal.alarm
            # Use threading for timeout
            result_container: Dict[str, Any] = {"result": None, "error": None}

            def run_func():
                try:
                    result_container["result"] = func()
                except Exception as e:
                    result_container["error"] = e

            thread = threading.Thread(target=run_func)
            thread.daemon = True
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                # Thread is still running - timeout occurred
                raise TimeoutError(f"Request timed out after {timeout} seconds")

            if result_container["error"]:
                error = result_container["error"]
                if isinstance(error, Exception):
                    raise error
                else:
                    raise RuntimeError(f"Request failed: {error}")

            result = result_container["result"]
            if result is None:
                raise RuntimeError("Function returned None unexpectedly")
            return result

    def _should_retry_error(self, error: Exception, config: RetryConfig) -> bool:
        """Determine if an error should trigger a retry."""
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network errors
        if config.retry_on_network_error:
            network_indicators = [
                "connection",
                "network",
                "timeout",
                "unreachable",
                "dns",
                "socket",
                "ssl",
                "certificate",
            ]
            if any(indicator in error_msg for indicator in network_indicators):
                return True

        # Rate limiting
        if config.retry_on_rate_limit:
            rate_limit_indicators = [
                "rate limit",
                "rate_limit",
                "too many requests",
                "429",
                "quota",
                "throttle",
            ]
            if any(indicator in error_msg for indicator in rate_limit_indicators):
                return True

        # Server errors (5xx)
        if config.retry_on_server_error:
            server_error_indicators = [
                "500",
                "502",
                "503",
                "504",
                "server error",
                "internal error",
                "service unavailable",
                "bad gateway",
            ]
            if any(indicator in error_msg for indicator in server_error_indicators):
                return True

        # Timeout errors
        if config.retry_on_timeout:
            if "timeout" in error_type or "timeout" in error_msg:
                return True

        # Provider-specific retryable errors
        retryable_patterns = [
            "temporarily unavailable",
            "try again",
            "service busy",
            "model loading",
            "warming up",
        ]
        if any(pattern in error_msg for pattern in retryable_patterns):
            return True

        return False

    def _calculate_retry_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay before retry using exponential backoff with jitter."""
        # Exponential backoff
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        delay = min(delay, config.max_delay)

        # Add jitter to prevent thundering herd
        if config.jitter:
            import random

            jitter_factor = 0.1  # 10% jitter
            jitter = delay * jitter_factor * random.random()
            delay += jitter

        return delay

    async def make_ai_request_async(
        self,
        provider_func: Callable[[], str],
        request_id: Optional[str] = None,
        timeout: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> RequestResult:
        """Make async AI request with retry logic."""
        loop = asyncio.get_event_loop()

        def sync_request():
            return self.make_ai_request(provider_func, request_id, timeout, retry_config)

        return await loop.run_in_executor(None, sync_request)

    def get_active_requests(self) -> Dict[str, RequestResult]:
        """Get status of currently active requests."""
        return self._active_requests.copy()

    def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request if possible."""
        if request_id in self._active_requests:
            self._active_requests[request_id].status = RequestStatus.CANCELLED
            return True
        return False

    def get_request_statistics(self) -> Dict[str, Any]:
        """Get statistics about request patterns and performance."""
        # This could be enhanced to track historical statistics
        return {
            "active_requests": len(self._active_requests),
            "retry_config": {
                "max_attempts": self.retry_config.max_attempts,
                "base_delay": self.retry_config.base_delay,
                "max_delay": self.retry_config.max_delay,
                "timeout": self.retry_config.timeout,
            },
        }
