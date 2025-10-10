# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Critical Non-Obvious Patterns

**Circuit Breaker Pattern**: Always use `handle_errors()` decorator from `crypto/core/error_handling.py` for API calls - it includes automatic retry logic and circuit breakers that prevent cascade failures.

**Token Resolution**: Use `resolve_token()` from `crypto/core/token_resolver.py` instead of direct API calls - it implements multi-provider fallbacks (CoinGecko, CoinMarketCap, DexScreener) with intelligent caching.

**Emergency Mode**: The `fail_safe.py` system automatically triggers emergency mode when portfolio drawdown exceeds 10% - this halts all trading operations until manually reset.

**ADK Integration**: Agent coordination requires lazy initialization pattern from `adk_agents/adk/adk_integration.py` - never instantiate ADK directly, always use `get_instance()`.

**Language Mixing**: Swedish error messages and comments are intentional in crypto modules - maintain this pattern for consistency with existing codebase.

## Code Style Requirements

**React/TypeScript Frontend**:
- Use shadcn/ui "new-york" style with CSS variables
- Phosphor icons only (not Lucide or Heroicons)
- Strict TypeScript with explicit `any` disabled except where configured
- Path aliases: `@/components`, `@/lib`, `@/hooks`

**Python Backend**:
- Black formatting with 88 char line length (crypto modules)
- Async/await pattern mandatory for all I/O operations
- Swedish error messages in crypto modules only
- Pylint disabled for unused variables in route-decorated functions

## Testing Conventions

**Async Testing**: Use `pytest.mark.asyncio` for async tests, not unittest's async support
**Financial Tests**: All VaR calculations must use confidence level 0.95 by default
**Performance Tests**: 30-second timeout for concurrent API calls (10 simultaneous)
**Mocking**: Use AsyncMock for async functions, maintain Swedish error messages in mocks