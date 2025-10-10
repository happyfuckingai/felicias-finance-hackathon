# Project Documentation Rules (Non-Obvious Only)

- "src/" contains VSCode extension code, not source for web apps (counterintuitive)
- Provider examples in src/api/providers/ are the canonical reference (docs are outdated)
- UI runs in VSCode webview with restrictions (no localStorage, limited APIs)
- Package.json scripts must be run from specific directories, not root
- Locales in root are for extension, webview-ui/src/i18n for UI (two separate systems)
- Circuit breaker documentation in crypto/core/error_handling.py contains implementation details
- Token resolver multi-provider strategy documented in crypto/core/token_resolver.py comments
- Emergency mode reset procedures in fail_safe.py documentation section
- ADK agent coordination patterns documented in adk_agents/adk/adk_integration.py
- Swedish comments in crypto modules are intentional for team consistency
- React frontend uses shadcn/ui "new-york" style exclusively
- Phosphor icons required, not Lucide or Heroicons