# Contributing to Felicia's Finance

Thank you for your interest in contributing to the Felicia's Finance multi-agent orchestration platform! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Security Considerations](#security-considerations)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background, experience level, or identity. We expect all participants to adhere to our code of conduct.

### Expected Behavior

- **Be respectful**: Treat all community members with respect and kindness
- **Be collaborative**: Work together constructively and share knowledge
- **Be inclusive**: Welcome newcomers and help them get started
- **Be professional**: Maintain professional communication in all interactions
- **Be constructive**: Provide helpful feedback and suggestions

### Unacceptable Behavior

- Harassment, discrimination, or offensive language
- Personal attacks or trolling
- Sharing private information without consent
- Spam or off-topic discussions
- Any behavior that would be inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Git**: Version control system
- **Docker**: Container runtime (v20.10+)
- **Kubernetes**: Local cluster (minikube, kind, or Docker Desktop)
- **Python**: Version 3.9 or higher
- **Node.js**: Version 16 or higher (for frontend components)
- **Go**: Version 1.19 or higher (for some utilities)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/felicias-finance-hackathon.git
   cd felicias-finance-hackathon
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/happyfuckingai/felicias-finance-hackathon.git
   ```

### First-Time Setup

1. Install development dependencies:
   ```bash
   make install-dev
   ```
2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```
3. Run initial tests:
   ```bash
   make test
   ```

## Development Environment

### Local Development Setup

#### Using Docker Compose
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

#### Using Kubernetes (Recommended)
```bash
# Deploy to local cluster
make deploy-local

# Port forward services
kubectl port-forward svc/orchestrator 8080:8080 -n felicias-finance-dev
kubectl port-forward svc/banking-agent 8081:8080 -n felicias-finance-dev
kubectl port-forward svc/crypto-agent 8082:8080 -n felicias-finance-dev

# Clean up
make clean-local
```

### Environment Variables

Create a `.env.local` file for development:
```bash
# Development configuration
DEBUG=true
LOG_LEVEL=debug
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/felicias_finance_dev
REDIS_URL=redis://localhost:6379/0

# Agent configuration
AGENT_REGISTRY_URL=http://localhost:8080
ENABLE_TLS=false
CERT_PATH=./certs/dev
```

### IDE Configuration

#### VS Code
Recommended extensions:
- Python
- Go
- Kubernetes
- Docker
- GitLens
- SonarLint

#### IntelliJ IDEA
Recommended plugins:
- Python
- Go
- Kubernetes
- Docker
- SonarLint

## Contributing Process

### Issue Reporting

Before creating a new issue:
1. Search existing issues to avoid duplicates
2. Use the appropriate issue template
3. Provide detailed information including:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details
   - Relevant logs or screenshots

### Feature Requests

For new features:
1. Open a discussion first to gauge interest
2. Create a detailed feature request issue
3. Include:
   - Use case and motivation
   - Proposed solution
   - Alternative approaches considered
   - Implementation complexity estimate

### Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following coding standards

3. **Write tests** for new functionality

4. **Update documentation** as needed

5. **Run the test suite**:
   ```bash
   make test-all
   ```

6. **Commit your changes** with descriptive messages:
   ```bash
   git commit -m "feat: add agent discovery caching mechanism"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a pull request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots or demos if applicable
   - Checklist completion

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Breaking changes documented
- [ ] Commit messages follow convention

## Coding Standards

### Python Code Style

We follow PEP 8 with some modifications:

```python
# Good example
class AgentManager:
    """Manages agent lifecycle and communication."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agents: Dict[str, Agent] = {}
        self.logger = logging.getLogger(__name__)
    
    async def register_agent(self, agent: Agent) -> bool:
        """Register a new agent with the platform.
        
        Args:
            agent: The agent instance to register
            
        Returns:
            True if registration successful, False otherwise
            
        Raises:
            AgentRegistrationError: If registration fails
        """
        try:
            await self._validate_agent(agent)
            self.agents[agent.id] = agent
            self.logger.info(f"Agent {agent.id} registered successfully")
            return True
        except ValidationError as e:
            self.logger.error(f"Agent validation failed: {e}")
            raise AgentRegistrationError(f"Failed to register agent: {e}")
```

#### Code Formatting
- Use `black` for code formatting
- Use `isort` for import sorting
- Use `flake8` for linting
- Maximum line length: 88 characters

#### Type Hints
- Use type hints for all function parameters and return values
- Use `typing` module for complex types
- Use `Optional` for nullable values

### Go Code Style

Follow standard Go conventions:

```go
// Package agent provides core agent functionality
package agent

import (
    "context"
    "fmt"
    "log"
    
    "github.com/happyfuckingai/felicias-finance/pkg/config"
)

// Manager handles agent lifecycle operations
type Manager struct {
    config *config.Config
    agents map[string]*Agent
    logger *log.Logger
}

// NewManager creates a new agent manager instance
func NewManager(cfg *config.Config) *Manager {
    return &Manager{
        config: cfg,
        agents: make(map[string]*Agent),
        logger: log.New(os.Stdout, "agent-manager: ", log.LstdFlags),
    }
}

// RegisterAgent registers a new agent with the platform
func (m *Manager) RegisterAgent(ctx context.Context, agent *Agent) error {
    if err := m.validateAgent(agent); err != nil {
        return fmt.Errorf("agent validation failed: %w", err)
    }
    
    m.agents[agent.ID] = agent
    m.logger.Printf("Agent %s registered successfully", agent.ID)
    return nil
}
```

### JavaScript/TypeScript Code Style

Use Prettier and ESLint:

```typescript
// Good example
interface AgentConfig {
  id: string;
  capabilities: string[];
  endpoint: string;
}

class AgentClient {
  private config: AgentConfig;
  private httpClient: HttpClient;

  constructor(config: AgentConfig) {
    this.config = config;
    this.httpClient = new HttpClient(config.endpoint);
  }

  async sendMessage(message: Message): Promise<Response> {
    try {
      const response = await this.httpClient.post('/messages', message);
      return response.data;
    } catch (error) {
      throw new AgentCommunicationError(`Failed to send message: ${error.message}`);
    }
  }
}
```

### Commit Message Convention

We use Conventional Commits:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Maintenance tasks

Examples:
```
feat(agent): add automatic agent discovery
fix(security): resolve certificate validation issue
docs(api): update authentication documentation
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
├── performance/   # Performance tests
├── security/      # Security tests
└── fixtures/      # Test data and fixtures
```

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from felicias_finance.agent import AgentManager

class TestAgentManager:
    """Test suite for AgentManager class."""
    
    @pytest.fixture
    def agent_manager(self):
        """Create AgentManager instance for testing."""
        config = Mock()
        return AgentManager(config)
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing."""
        agent = Mock()
        agent.id = "test-agent-001"
        agent.capabilities = ["test:capability"]
        return agent
    
    async def test_register_agent_success(self, agent_manager, mock_agent):
        """Test successful agent registration."""
        # Arrange
        agent_manager._validate_agent = Mock(return_value=True)
        
        # Act
        result = await agent_manager.register_agent(mock_agent)
        
        # Assert
        assert result is True
        assert mock_agent.id in agent_manager.agents
        agent_manager._validate_agent.assert_called_once_with(mock_agent)
    
    async def test_register_agent_validation_failure(self, agent_manager, mock_agent):
        """Test agent registration with validation failure."""
        # Arrange
        agent_manager._validate_agent = Mock(side_effect=ValidationError("Invalid agent"))
        
        # Act & Assert
        with pytest.raises(AgentRegistrationError):
            await agent_manager.register_agent(mock_agent)
```

### Integration Tests

```python
import pytest
import asyncio
from felicias_finance.testing import TestCluster

@pytest.mark.integration
class TestAgentCommunication:
    """Integration tests for agent communication."""
    
    @pytest.fixture(scope="class")
    async def test_cluster(self):
        """Set up test cluster."""
        cluster = TestCluster()
        await cluster.start()
        yield cluster
        await cluster.stop()
    
    async def test_agent_to_agent_communication(self, test_cluster):
        """Test communication between agents."""
        # Deploy test agents
        banking_agent = await test_cluster.deploy_agent("banking", {
            "capabilities": ["banking:balance"]
        })
        crypto_agent = await test_cluster.deploy_agent("crypto", {
            "capabilities": ["crypto:price"]
        })
        
        # Test communication
        response = await banking_agent.send_message(
            recipient=crypto_agent.id,
            action="crypto:price",
            parameters={"symbol": "BTC"}
        )
        
        assert response.status == "success"
        assert "price" in response.data
```

### Test Coverage

Maintain minimum test coverage:
- **Unit tests**: 90% coverage
- **Integration tests**: 80% coverage
- **Critical paths**: 100% coverage

Run coverage reports:
```bash
make test-coverage
```

## Security Considerations

### Security Review Process

All contributions undergo security review:

1. **Automated scanning**: Code is automatically scanned for vulnerabilities
2. **Manual review**: Security team reviews security-sensitive changes
3. **Penetration testing**: Major features undergo penetration testing

### Security Guidelines

#### Sensitive Data Handling
```python
# Good: Use environment variables for secrets
import os
database_password = os.getenv('DATABASE_PASSWORD')

# Bad: Hardcoded secrets
database_password = "hardcoded-password"  # Never do this
```

#### Input Validation
```python
# Good: Validate all inputs
def process_agent_message(message: dict) -> dict:
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "pattern": "^[a-z]+:[a-z_]+$"},
            "parameters": {"type": "object"}
        },
        "required": ["action"]
    }
    
    validate(message, schema)
    return process_validated_message(message)
```

#### Error Handling
```python
# Good: Don't expose sensitive information
try:
    result = authenticate_agent(credentials)
except AuthenticationError:
    return {"error": "Authentication failed"}  # Generic message

# Bad: Exposing internal details
except AuthenticationError as e:
    return {"error": f"Database connection failed: {e}"}  # Too specific
```

### Security Testing

Include security tests:
```python
@pytest.mark.security
class TestSecurityFeatures:
    """Security-focused test suite."""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        malicious_input = "'; DROP TABLE users; --"
        with pytest.raises(ValidationError):
            process_user_input(malicious_input)
    
    def test_authentication_bypass_prevention(self):
        """Test authentication bypass prevention."""
        invalid_token = "invalid.jwt.token"
        with pytest.raises(AuthenticationError):
            authenticate_with_token(invalid_token)
```

## Documentation

### Documentation Types

1. **API Documentation**: Auto-generated from code comments
2. **User Guides**: Step-by-step instructions for users
3. **Developer Guides**: Technical documentation for contributors
4. **Architecture Documentation**: System design and architecture

### Writing Guidelines

#### API Documentation
```python
def register_agent(self, agent: Agent) -> bool:
    """Register a new agent with the platform.
    
    This method validates the agent configuration and adds it to the
    active agent registry. The agent must have valid credentials and
    declare its capabilities.
    
    Args:
        agent: The agent instance to register. Must have valid ID,
               capabilities, and authentication credentials.
    
    Returns:
        True if registration successful, False otherwise.
    
    Raises:
        AgentRegistrationError: If agent validation fails or registration
                               encounters an error.
        ValidationError: If agent configuration is invalid.
    
    Example:
        >>> agent = Agent(id="banking-001", capabilities=["banking:read"])
        >>> manager = AgentManager(config)
        >>> success = manager.register_agent(agent)
        >>> print(f"Registration successful: {success}")
        Registration successful: True
    """
```

#### User Documentation
- Use clear, concise language
- Include practical examples
- Provide troubleshooting sections
- Use screenshots and diagrams where helpful

### Documentation Updates

When making changes:
1. Update relevant documentation
2. Add new documentation for new features
3. Update API documentation
4. Review documentation for accuracy

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time chat and community support
- **Email**: security@felicias-finance.dev (security issues only)

### Getting Help

1. **Check documentation**: Start with existing documentation
2. **Search issues**: Look for similar problems or questions
3. **Ask in discussions**: Use GitHub Discussions for questions
4. **Join Discord**: Get real-time help from the community

### Recognition

We recognize contributors through:
- **Contributors file**: Listed in CONTRIBUTORS.md
- **Release notes**: Mentioned in release announcements
- **Community highlights**: Featured in community updates
- **Swag**: Stickers and other items for significant contributions

## Release Process

### Version Numbering

We use Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Schedule

- **Major releases**: Quarterly
- **Minor releases**: Monthly
- **Patch releases**: As needed

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Performance benchmarks run
- [ ] Breaking changes documented
- [ ] Migration guide provided (if needed)
- [ ] Release notes prepared

## Questions?

If you have questions about contributing, please:
1. Check this document first
2. Search existing issues and discussions
3. Create a new discussion if needed
4. Reach out on Discord for real-time help

Thank you for contributing to Felicia's Finance! Your contributions help make this project better for everyone.
