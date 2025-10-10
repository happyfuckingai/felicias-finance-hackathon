# Project Architecture Rules (Non-Obvious Only)

- Providers MUST be stateless - hidden caching layer assumes this
- Webview and extension communicate through specific IPC channel patterns only
- Database migrations cannot be rolled back - forward-only by design
- React hooks required because external state libraries break webview isolation
- Monorepo packages have circular dependency on types package (intentional)
- Circuit breaker pattern: crypto/core/error_handling.py implements automatic failover
- Multi-provider strategy: crypto/core/token_resolver.py contains fallback chain logic
- Emergency mode: fail_safe.py triggers at 10% drawdown with manual reset requirement
- ADK agent coordination: adk_agents/adk/adk_integration.py uses lazy initialization pattern
- SSE architecture: crypto_mcp_server uses Server-Sent Events for real-time data
- Language isolation: Swedish comments in crypto modules for team consistency
- UI restrictions: React frontend runs in VSCode webview with limited APIs
- Build constraints: NODE_ENV=production required for certain features to work