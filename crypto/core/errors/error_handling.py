"""
Produktions-ready felhantering för HappyOS Crypto.
Robust error handling och recovery mechanisms.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import traceback
import sys
from functools import wraps

logger = logging.getLogger(__name__)

class CryptoError(Exception):
    """Basfelklass för crypto-operationer."""

    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class WalletError(CryptoError):
    """Fel relaterade till wallet-operationer."""
    pass

class TransactionError(CryptoError):
    """Fel relaterade till transaktioner."""
    pass

class TokenError(CryptoError):
    """Fel relaterade till token-operationer."""
    pass

class APIError(CryptoError):
    """Fel relaterade till externa API:er."""
    pass

class NetworkError(CryptoError):
    """Fel relaterade till nätverksproblem."""
    pass

class ValidationError(CryptoError):
    """Fel relaterade till validering."""
    pass

class TradingError(CryptoError):
    """Fel relaterade till trading-operationer."""
    pass

class SecurityError(CryptoError):
    """Fel relaterade till säkerhetsoperationer."""
    pass

class CacheError(CryptoError):
    """Fel relaterade till cache-operationer."""
    pass

class CircuitBreaker:
    """Circuit breaker pattern för att hantera API-fel."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        """Registrera lyckad operation."""
        self.failure_count = 0
        self.state = 'CLOSED'

    def record_failure(self):
        """Registrera misslyckad operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

    def can_execute(self) -> bool:
        """Kontrollera om operation kan utföras."""
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        elif self.state == 'HALF_OPEN':
            return True
        return False

class RetryManager:
    """Intelligent retry management med exponential backoff."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Utför funktion med retry-logik.

        Args:
            func: Funktion att utföra
            *args: Funktionens argument
            **kwargs: Funktionens keyword-argument

        Returns:
            Funktionens resultat

        Raises:
            Ursprungliga exception efter max retries
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed. Last error: {e}")
                    raise last_exception

        raise last_exception

class ErrorRecovery:
    """Felåterhämtning och fallback-strategier."""

    def __init__(self):
        self.circuit_breakers = {
            'coingecko': CircuitBreaker(),
            'dexscreener': CircuitBreaker(),
            'newsapi': CircuitBreaker(),
            'blockchain': CircuitBreaker()
        }

    async def execute_with_fallback(self, primary_func: Callable, fallback_func: Callable,
                                  service_name: str, *args, **kwargs) -> Any:
        """
        Kör primär funktion med fallback om den misslyckas.

        Args:
            primary_func: Primär funktion att försöka
            fallback_func: Fallback-funktion
            service_name: Namn på tjänst för circuit breaker
            *args, **kwargs: Argument till funktionerna

        Returns:
            Resultat från primär eller fallback funktion
        """
        circuit_breaker = self.circuit_breakers.get(service_name, CircuitBreaker())

        if not circuit_breaker.can_execute():
            logger.info(f"Circuit breaker open for {service_name}, using fallback")
            return await fallback_func(*args, **kwargs)

        try:
            result = await primary_func(*args, **kwargs)
            circuit_breaker.record_success()
            return result
        except Exception as e:
            circuit_breaker.record_failure()
            logger.warning(f"Primary function failed for {service_name}: {e}, using fallback")
            return await fallback_func(*args, **kwargs)

class ErrorLogger:
    """Avancerad fel-logging och monitoring."""

    def __init__(self):
        self.error_counts = {}
        self.error_history = []

    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Logga fel med kontext och statistik."""
        error_type = type(error).__name__
        error_message = str(error)

        # Uppdatera räknare
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1

        # Spara felhistorik
        error_entry = {
            'timestamp': datetime.now(),
            'error_type': error_type,
            'message': error_message,
            'context': context or {},
            'traceback': traceback.format_exc()
        }

        self.error_history.append(error_entry)

        # Behåll bara senaste 1000 felen
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

        # Logga med lämplig nivå
        if isinstance(error, (NetworkError, APIError)):
            logger.warning(f"Service error: {error_type}: {error_message}")
        elif isinstance(error, ValidationError):
            logger.info(f"Validation error: {error_message}")
        else:
            logger.error(f"Unexpected error: {error_type}: {error_message}", exc_info=True)

    def get_error_stats(self) -> Dict[str, Any]:
        """Hämta felstatistik."""
        return {
            'total_errors': len(self.error_history),
            'error_counts': self.error_counts.copy(),
            'recent_errors': [
                {
                    'timestamp': entry['timestamp'],
                    'error_type': entry['error_type'],
                    'message': entry['message']
                }
                for entry in self.error_history[-10:]  # Senaste 10
            ]
        }

def handle_errors(service_name: str = None, enable_retry: bool = True):
    """
    Decorator för automatisk felhantering.

    Args:
        service_name: Namn på tjänst för circuit breaker
        enable_retry: Om retry ska aktiveras
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            error_recovery = ErrorRecovery()
            error_logger = ErrorLogger()
            retry_manager = RetryManager() if enable_retry else None

            try:
                if retry_manager and service_name:
                    return await error_recovery.execute_with_fallback(
                        lambda: retry_manager.execute_with_retry(func, *args, **kwargs),
                        lambda: func(*args, **kwargs),  # Fallback är samma funktion utan retry
                        service_name,
                        *args, **kwargs
                    )
                else:
                    return await func(*args, **kwargs)

            except CryptoError as e:
                error_logger.log_error(e, {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs),
                    'service': service_name
                })
                raise e

            except Exception as e:
                # Konvertera till CryptoError
                crypto_error = CryptoError(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    "UNEXPECTED_ERROR",
                    {
                        'original_error': type(e).__name__,
                        'function': func.__name__,
                        'traceback': traceback.format_exc()
                    }
                )
                error_logger.log_error(crypto_error)
                raise crypto_error

        return wrapper
    return decorator

class HealthChecker:
    """Hälsokontroll för olika tjänster."""

    def __init__(self):
        self.services = {}
        self.last_checks = {}

    def register_service(self, name: str, check_func: Callable):
        """Registrera en tjänst för hälsokontroll."""
        self.services[name] = check_func

    async def check_all_services(self) -> Dict[str, Any]:
        """Kontrollera hälsa för alla registrerade tjänster."""
        results = {}

        for service_name, check_func in self.services.items():
            try:
                start_time = datetime.now()
                health_status = await check_func()
                check_time = (datetime.now() - start_time).total_seconds()

                results[service_name] = {
                    'status': 'healthy' if health_status else 'unhealthy',
                    'response_time': check_time,
                    'timestamp': datetime.now()
                }

            except Exception as e:
                results[service_name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now()
                }

        self.last_checks = results
        return results

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Hämta status för en specifik tjänst."""
        return self.last_checks.get(service_name)

# Globala instanser
error_recovery = ErrorRecovery()
error_logger = ErrorLogger()
health_checker = HealthChecker()

# Bekväma funktioner för användning
def log_error(error: Exception, context: Dict[str, Any] = None):
    """Global fel-logging funktion."""
    error_logger.log_error(error, context)

def get_error_stats() -> Dict[str, Any]:
    """Hämta global felstatistik."""
    return error_logger.get_error_stats()

async def check_system_health() -> Dict[str, Any]:
    """Kontrollera övergripande systemhälsa."""
    return await health_checker.check_all_services()