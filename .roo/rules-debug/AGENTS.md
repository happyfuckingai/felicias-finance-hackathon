# Project Debug Rules (Non-Obvious Only)

- Webview dev tools accessed via Command Palette > "Developer: Open Webview Developer Tools" (not F12)
- IPC messages fail silently if not wrapped in try/catch in packages/ipc/src/
- Production builds require NODE_ENV=production or certain features break without error
- Database migrations must run from packages/evals/ directory, not root
- Extension logs only visible in "Extension Host" output channel, not Debug Console
- Circuit breaker states logged to crypto/core/error_handling.py custom logger
- Emergency mode activation logs to fail_safe.py with specific format
- Token resolver cache hits/misses tracked in crypto/core/token_resolver.py stats
- ADK agent coordination issues require checking adk_agents/adk/adk_integration.py logs
- SSE server debugging requires crypto_mcp_server/.env CRYPTO_DEBUG=true
- React frontend debugging uses Next.js dev tools, not standard browser dev tools
- Multi-provider API failures cascade through token_resolver.py fallback chain