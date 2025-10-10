# Project Coding Rules (Non-Obvious Only)

- Always use safeWriteJson() from src/utils/ instead of JSON.stringify for file writes (prevents corruption)
- API retry mechanism in src/api/providers/utils/ is mandatory (not optional as it appears)
- Database queries MUST use the query builder in packages/evals/src/db/queries/ (raw SQL will fail)
- Provider interface in packages/types/src/ has undocumented required methods
- Test files must be in same directory as source for vitest to work (not in separate test folder)
- Circuit breaker pattern: Use handle_errors() decorator from crypto/core/error_handling.py for all API calls
- Token resolution: Use resolve_token() from crypto/core/token_resolver.py instead of direct API calls
- Emergency mode: fail_safe.py system triggers automatically at 10% portfolio drawdown
- ADK integration: Always use get_instance() from adk_agents/adk/adk_integration.py, never instantiate directly
- Language mixing: Swedish error messages required in crypto modules, maintain pattern consistency
- Async patterns: All I/O operations must use async/await in Python backend
- TypeScript: Strict mode with explicit any disabled, use @/* path aliases
- React: shadcn/ui "new-york" style only, Phosphor icons only, RSC enabled