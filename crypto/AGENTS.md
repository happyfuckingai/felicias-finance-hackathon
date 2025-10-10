# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build/Lint/Test Commands
- Dependencies: pip install -r config/requirements.txt (Google Cloud packages require `gcloud auth application-default login`; run from project root)
- Tests: pytest tests/ -v --asyncio-mode=auto (requires pytest-asyncio; tests use sys.path.insert for relative imports from crypto/)
- Single test: pytest tests/test_crypto_system.py::TestMarketAnalyzer::test_get_token_price_success -v (execute from project root; async tests need event loop)
- Lint: flake8 . && black . --check && mypy . --strict (no .pre-commit-config.yaml; enforce via dev deps)
- Format: black . && isort . (isort not in requirements.txt but implied for import sorting)
- Run trading: cd trading && python trading_system.py --mode auto (requires CRYPTO_PRIVATE_KEY env; simulation if unset)

## Code Style Guidelines
- Imports: Relative for internal (e.g., from ..crypto.core.*); absolute for stdlib/third-party. Group: stdlib, third-party (web3/google-cloud-*), local. No wildcard imports.
- Formatting: Black (line-length=88 implied); snake_case vars/functions, PascalCase classes. Docstrings in triple-quotes with Swedish/English mix.
- Types: Full annotations with typing/typing_extensions; use Decimal for web3 values (e.g., balances/prices) to avoid float precision loss.
- Naming: Tokens lowercase (e.g., 'bitcoin'); errors via core/errors/* (e.g., CryptoError with codes like "INTEGRATION_INIT_ERROR").
- Error Handling: Wrap async I/O (web3/BigQuery) in @handle_errors decorator from core/errors/error_handling.py; use CircuitBreaker/RetryManager for rate-limited APIs (e.g., Google Cloud Web3 calls fail silently without).
- BigQuery: Queries via services/bigquery_service.py only; datasets/tables per config/bigquery_config.py schemas (manual creation required; no auto-migrate).

## Project-Specific Gotchas
- Async everywhere: All core/services/ use asyncio; run with asyncio.run() or pytest --asyncio-mode=auto.
- Web3: google-cloud-web3==1.0.0 for multi-chain (ethereum/polygon/etc.); cache via cache/web3_cache.py to avoid quota exhaustion.
- Tests: Insert sys.path for crypto/ imports; mocks needed for web3/google-cloud (e.g., patch aiohttp.ClientSession).