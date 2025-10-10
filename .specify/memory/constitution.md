<!-- Sync Impact Report: Felicia's Finance Constitution Update

**Version Change**: 1.0.0 → 1.0.0 (No version change required - system already aligned)
**Analysis Date**: 2025-09-22
**Status**: System already properly aligned with 7-act saga structure

**Modified Principles**: None - all principles already properly structured
**Added Sections**: None - constitution already comprehensive
**Removed Sections**: None - no redundant content found

**Templates Requiring Updates**:
- ✅ plan-template.md: Already includes constitution checks and 7-act compliance gates
- ✅ tasks-template.md: Already follows TDD and proper constitutional ordering
- ✅ spec-template.md: Already focused on user requirements (not implementation)
- ✅ agent-file-template.md: Already generic and constitution-aligned

**Follow-up TODOs**:
- [ ] Regular constitution compliance audits (quarterly)
- [ ] Update constitution version when new architectural patterns are discovered
- [ ] Ensure all future templates include 7-act compliance gates

**Summary**: The Felicia's Finance system is already excellently aligned with the 7-act saga governance structure. The constitution comprehensively captures all critical non-obvious patterns discovered in the codebase, including circuit breakers, multi-provider fallbacks, emergency mode triggers, ADK lazy initialization, and Swedish language consistency requirements. All templates properly enforce constitutional compliance.

**Recommendation**: No immediate changes needed. System is production-ready with proper 7-act governance.
-->

# Felicia's Finance Constitution
<!-- The 7-Act Saga of Autonomous Financial Intelligence -->

## The 7-Act Governance Structure

### **Act 1: The Bridge Between Worlds (Vision & Architecture)**
**I. Unified Financial Intelligence**
Every system component must contribute to bridging traditional banking and DeFi. All agents, services, and interfaces must maintain this dual-world compatibility, ensuring seamless translation between conventional financial operations and decentralized protocols.

### **Act 2: The Ambassador Protocol (Communication & Interface)**
**II. Felicia-First Interface**
Felicia is the single point of human interaction. All user communications must route through her, ensuring consistent experience across banking operations, crypto trading, and multi-agent orchestration. No direct system access bypasses the ambassador layer.

### **Act 3: The AI Agent Army (Orchestration & Coordination)**
**III. Multi-Agent Orchestration (NON-NEGOTIABLE)**
Complex financial operations require coordinated multi-agent teams using Google's ADK. Single-agent solutions are prohibited for operations involving market analysis, risk assessment, or cross-domain transactions. All agents must implement lazy initialization patterns.

### **Act 4: The Secure Network (Communication & Security)**
**IV. A2A Protocol Compliance**
All inter-agent communication must use the A2A (Agent-to-Agent) protocol with end-to-end encryption. Circuit breaker patterns must be implemented for all external API calls. Emergency mode triggers automatically at 10% portfolio drawdown with manual reset requirements.

### **Act 5: The Living Experience (User Interface & Real-time Updates)**
**V. Real-time Responsiveness**
All user interactions must maintain sub-second response times. MCP-UI integration required for real-time data visualization. LiveKit Server mandatory for voice/text communication with zero-latency requirements.

### **Act 6: The Eternal Memory (Persistence & Context)**
**VI. Memory Integration**
Mem0.ai integration required for all user preference and context storage. Agent memory must persist across sessions and contribute to learning. Swedish language support mandatory for crypto module consistency.

### **Act 7: The Grand Finale (System Integration & Safety)**
**VII. Emergency Circuit Breakers**
Fail-safe systems must automatically trigger at critical thresholds. Multi-provider fallback chains required for all external services (CoinGecko, DexScreener, CoinMarketCap). Emergency mode halts all trading operations until manual reset.

## Critical System Constraints

### **Circuit Breaker Requirements**
- **Token Resolution**: Multi-provider fallback with intelligent caching (crypto/core/token_resolver.py)
- **Error Handling**: Automatic retry with exponential backoff (crypto/core/error_handling.py)
- **Risk Management**: 20% emergency stop-loss triggers system-wide halt (crypto/core/fail_safe.py)
- **API Resilience**: Circuit breakers for all external services with 5-failure threshold

### **Security Standards**
- **Provider Diversity**: Minimum 3 providers per service type with automatic failover
- **Session Management**: Encrypted A2A sessions with 1-hour expiry
- **Compliance Integration**: Real-time compliance checks before all transactions
- **Emergency Protocols**: Manual reset required after emergency mode activation

### **Performance Standards**
- **Cache Efficiency**: 3600-second cache duration for token data
- **Concurrent Limits**: Maximum 3 simultaneous API requests per service
- **Response Times**: Sub-500ms for all user interactions
- **Memory Persistence**: Context retention across all sessions

## Development Workflow

### **Test-First Requirements**
- **Financial Testing**: All VaR calculations use 0.95 confidence level
- **Async Testing**: Pytest.mark.asyncio mandatory for all I/O operations
- **Performance Testing**: 30-second timeout for concurrent API calls
- **Mocking Standards**: AsyncMock for async functions with Swedish error messages

### **Integration Testing Focus**
- **New Service Contracts**: All new agent integrations require contract tests
- **Inter-Service Communication**: A2A protocol message passing validation
- **Cross-Domain Operations**: Banking ↔ Crypto transaction flow testing
- **Emergency Scenarios**: Fail-safe and circuit breaker testing

## Architecture Governance

### **System Components**
- **Crypto System**: Advanced trading with circuit breakers and multi-provider fallbacks
- **ADK Agents**: Google ADK multi-agent orchestration with lazy initialization
- **Banking A2A**: Secure inter-agent banking operations with compliance checks
- **MCP Servers**: Model Context Protocol tools for crypto and banking functions
- **React Frontend**: Next.js with shadcn/ui "new-york" style components

### **Technology Stack Requirements**
- **Frontend**: React/TypeScript with strict mode, shadcn/ui, Phosphor icons
- **Backend**: Python with async/await, Black formatting (88-char limit)
- **Communication**: A2A protocol, MCP servers, LiveKit integration
- **AI/ML**: Google ADK for agent orchestration, mem0.ai for memory

## Amendment Process

### **Constitutional Changes**
This constitution supersedes all other practices and architectural decisions. Amendments require:
1. Documentation of the proposed change and its impact on the 7-act structure
2. Approval from system architects and lead developers
3. Migration plan for existing implementations
4. Testing against all circuit breaker and emergency scenarios

### **Runtime Guidance**
All development must verify compliance with this constitution. Use [AGENTS.md] for runtime development guidance. Complexity must be justified against the 7-act governance structure.

**Version**: 1.0.0 | **Ratified**: 2025-09-22 | **Last Amended**: 2025-09-22