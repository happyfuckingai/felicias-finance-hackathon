# Felicia's Finance: AI-Driven Hybrid Banking Platform

## Inspiration
This project was born from a simple but powerful question: What if we could build a secure and intelligent bridge between the slow, stable world of traditional finance and the fast-paced, complex world of DeFi? We were inspired by Google's Bank of Anthos, not as a standalone demo, but as a foundational component in a larger, more intelligent system. Our goal was to create a true Hybrid Finance (HyFi) platform that makes advanced finance accessible to everyone, orchestrated by a single, powerful AI agent.

## What it does
Felicia's Finance is an AI-driven private banking platform fronted by "Felicia," an intelligent AI agent that acts as your personal financial partner. Through a simple, conversational interface, a user can:

• **Connect to Traditional Banking**: Using our Bank of Anthos MCP server wrapper, Felicia can access account balances and execute fiat transfers with enterprise-grade security.

• **Invest in DeFi Intelligently**: Felicia leverages our advanced Crypto MCP server with built-in AI orchestration to perform real-time market analysis, generate trading signals, and manage crypto portfolios autonomously.

• **Get Holistic Financial Advice**: Because Felicia operates in both worlds, she can provide comprehensive risk analysis and investment advice that covers a user's entire financial landscape - from traditional banking to DeFi investments.

• **Experience Real-time AI Orchestration**: Through our A2A (Agent-to-Agent) communication protocol, Felicia coordinates complex multi-step financial workflows behind the scenes, providing live progress updates via event streaming.

• **See Dynamic Visualizations**: Using MCP-UI integration, Felicia can dynamically render interactive charts, portfolio breakdowns, and risk analysis visualizations directly in the conversational interface.

Essentially, Felicia's Finance allows you to give a high-level command like, "Invest 1,000 EUR from my bank account into a balanced crypto portfolio," and the entire complex workflow - spanning authentication, fund transfers, market analysis, risk assessment, and portfolio optimization - is orchestrated autonomously in the background with real-time status updates.

## How we built it
Felicia's Finance is built on a revolutionary agent-based architecture designed for robustness and scalability on Google Kubernetes Engine (GKE). The system implements our 7-act saga of Felicia's Finance, creating a clean separation between AI orchestration and core systems.

### The 7-Act Architecture:

**Act 1: Two Kingdoms, Two Toolboxes**
We created two MCP (Model Context Protocol) servers as specialized toolboxes:
- **Bank MCP Server**: Wraps Bank of Anthos APIs providing traditional banking tools (balance checks, transfers, contacts)
- **Crypto MCP Server**: Advanced AI-powered toolbox with market analysis, trading signals, and autonomous portfolio management

**Act 2: The Invisible Craftsman (Orchestrator Agent)**
Our master Orchestrator Agent, built on Google's ADK framework, acts as the technical "showrunner." This agent:
- Analyzes user intentions using Gemini AI
- Creates detailed execution plans spanning both traditional and DeFi domains
- Delegates tasks to appropriate toolboxes via secure API calls
- Handles error recovery and workflow optimization
- Remains completely invisible to end users, focusing solely on perfect execution

**Act 3: The Ambassador's Voice (Communication Agent Felicia)**
Felicia, our user-facing AI agent, provides the social intelligence layer:
- Translates natural language requests into technical intentions
- Maintains conversation context using mem0.ai for personalized interactions
- Presents complex financial data as clear, understandable narratives
- Has zero direct control over systems - she's purely a communication bridge

**Act 4: The Magical Connection (A2A Protocol)**
Using Google's A2A (Agent-to-Agent) protocol, we created a secure, one-way event streaming system:
- Orchestrator broadcasts real-time status updates ("Analyzing market data...", "Executing transfer...")
- Felicia passively listens and presents updates as live conversation
- Enables complex workflows without direct agent-to-agent coupling

**Act 5-7: The Living Experience**
- **LiveKit**: Provides real-time conversational interface with voice capabilities
- **MCP-UI**: Enables dynamic rendering of financial charts and visualizations within chat
- **mem0.ai**: Gives Felicia persistent memory for personalized financial guidance

### Leveraging Google's Agent Ecosystem:
• **ADK (Agent Development Kit)**: All agents built using Google's enterprise-grade agent framework for reliability and security
• **A2A Protocol**: Secure inter-agent communication enabling complex multi-domain workflows
• **GKE Autopilot**: Serverless Kubernetes for automatic scaling and management
• **Vertex AI (Gemini)**: Powers intelligent decision-making and natural language processing
• **Google Cloud Run**: All MCP servers (Banking, Crypto, Agent Core) deployed as remote services
• **Google Web3**: Integrated blockchain infrastructure for DeFi operations

### Production Deployment Architecture:
All system components are deployed as independent MCP servers on Google Cloud Run:
- **Agent Core MCP Server**: Orchestrates multi-agent workflows via Google's ADK
- **Bank of Anthos MCP Server**: Provides traditional banking operations via secure API integration
- **Crypto MCP Server**: Handles DeFi operations, portfolio management, and Web3 interactions
- **Google Web3 Integration**: Native blockchain connectivity for cross-chain operations

This microservices architecture ensures scalability, fault tolerance, and independent scaling of each component while maintaining secure inter-service communication through Google's managed infrastructure.

### Technical Innovation:
The architecture demonstrates the convergence of Anthropic's MCP (tools & context for agents) with Google's A2A (agent interoperability), deployed on Google Cloud Run as production-ready microservices. This creates a future-proof ecosystem where AI agents from different vendors can collaborate seamlessly on complex business workflows, with native Web3 integration for comprehensive financial operations.

## Challenges we ran into
The greatest challenge wasn't technical; it was personal. My biggest obstacle has always been bringing things to a close. My mind is constantly analyzing, improving, and planning the next step, which makes it incredibly difficult to ever say, "This is good enough for now."

The hardest part of this entire project was not building the federated architecture or implementing the AI. It was the internal battle to reach a point of completion, to resist the urge to endlessly refine, and to finally decide that what I have built is something I can be proud of and submit.

This hackathon submission, therefore, represents not just the solution to a technical problem, but a victory over my own greatest challenge: the art of completion.

## Accomplishments that we're proud of
My greatest accomplishment with this project is not just the final code, but the revolutionary process used to create it, and the humble hardware it was built on.

My previous career started from a drunken bet with a friend. At the age of 23, with zero experience in the industry, I quit my safe job and turned that bet into a successful Swedish construction company with 9.5 million SEK in revenue. But a year ago, at the age of 28, I saw a future that needed to be built, one not of concrete and steel, but of intelligent, autonomous systems. My first thought was bookkeeping—it is extremely costly and incredibly boring, yet every business needs it. I realized that AI could revolutionize not just construction, but the fundamental operations that businesses struggle with every day. So, I made the difficult decision to leave that life behind to pursue a new mission: making advanced technology accessible to everyone.

At that point, I didn't even know what Python was. If someone had asked me, I would have thought of a snake. Today, I live and breathe code. This journey has taught me that life and programming work in exactly the same way. But here is the crucial part: I have never written a single line of code for this project myself.

Not because I couldn't, but because it would have been too slow.

Instead, I acted as an architect and a conductor. I built this entire system on a scrappy, old laptop—a machine so underpowered it couldn't even run a standard operating system, forcing me to install Lubuntu just to keep it from crashing. It has no GPU. On this humble hardware, I orchestrated a team of AI coding agents, leveraging Roo Code in VS Code and their Roo CodeCloud for free access to powerful models like X-AI's Grok.

My role was to provide the vision, design the architecture, and then guide these freely accessible AI agents to connect all the pieces correctly. I didn't write the code; I orchestrated the AI that wrote the code, for free, on a computer most would have thrown away.

For my entire life, due to my ADHD, I have never once brought a major project to completion. This project changes everything. Felicia's Finance, named in honor of my sister, is the first time I have ever reached a point where I can consciously decide to "complete" a stage of work, submit it, and feel an immense sense of pride in what I have created.

This is my "Hello, World!" – a world where human vision and AI execution work in perfect harmony, available to anyone with a dream, regardless of their resources.

## What we learned
The most profound lesson has been that the hardest part of any great journey is not the journey itself, but having the courage to take the very first step.

On a technical level, this project embodies the philosophy captured by Alfred North Whitehead: "Civilization advances by extending the number of important operations which we can perform without thinking about them." We learned that the true power of an AI agent comes from the strength of the ecosystem it operates in—a system designed to automate complexity, freeing up human time and energy for what truly matters.

## What's next for Felicia's Finance
Felicia's Finance is not the culmination of my work. It is my "Hello, World!"

It is the first public demonstration of a powerful, proprietary AI ecosystem I have engineered. It is the proof-of-concept that validates the foundation. This is where the real journey begins.

My ultimate vision is to build a suite of interconnected, AI-powered applications that will fundamentally change how we interact with technology. The next application is already designed: "Assistenten Svea," named after my other sister, an autonomous accounting system for the construction industry. This isn't the end of a hackathon project; it is the public beginning of a lifelong mission. A mission to build tools that empower people, to advance technology for my home nation, Sweden, and ultimately, for all of humanity.