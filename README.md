# Alpaca Trader

A comprehensive trading platform built with microservices architecture for algorithmic trading using the Alpaca API.

## Architecture

This is a monorepo containing:

- **apps/api** - REST API server for trading operations
- **apps/engine** - Core trading engine with strategy execution
- **apps/web** - Web interface for monitoring and management
- **packages/core** - Shared utilities and common functionality
- **packages/strategies** - Trading strategy implementations
- **infra/** - Azure infrastructure as code
- **tests/** - Integration and end-to-end tests

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Make

## Quick Start

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd alpaca-trader
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies**
   ```bash
   # Python dependencies
   pip install -r requirements.txt
   
   # Node.js dependencies (if web app exists)
   npm install
   ```

3. **Start development environment**
   ```bash
   make dev-up
   ```

## Available Commands

- `make fmt` - Format code in all packages
- `make lint` - Run linting checks
- `make test` - Run test suites
- `make run-api` - Start the API server
- `make run-engine` - Start the trading engine
- `make build-docker` - Build Docker images
- `make dev-up` - Start development environment

## Configuration

Copy `.env.example` to `.env` and configure your environment variables:

- Alpaca API credentials
- Database connections
- Service endpoints
- Logging levels

## Development

Each service can be developed independently:

```bash
# API development
cd apps/api
python -m uvicorn main:app --reload

# Engine development
cd apps/engine
python main.py

# Web development (if applicable)
cd apps/web
npm run dev
```

## Testing

Run tests for all services:
```bash
make test
```

Or test individual components:
```bash
cd apps/api && python -m pytest
cd apps/engine && python -m pytest
```

## Deployment

Infrastructure is managed with Terraform in the `infra/` directory. See deployment documentation for details.

## Contributing

1. Follow the existing code style
2. Run `make fmt` and `make lint` before committing
3. Ensure all tests pass with `make test`
4. Update documentation as needed