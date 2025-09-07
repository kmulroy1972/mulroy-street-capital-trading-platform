# Mulroy Street Capital Trading Platform

A professional algorithmic trading platform built with modern web technologies, featuring a real-time dashboard, automated strategy execution, and a powerful admin panel for live configuration changes.

## 🏗️ Architecture Overview

### **Frontend Dashboard**
- **Framework**: Next.js 15.5.2 with Turbopack
- **Language**: TypeScript/React
- **Styling**: Tailwind CSS
- **Deployment**: Azure Static Web Apps
- **Live URL**: https://www.mulroystreetcap.com

### **Admin Panel** 
- **Location**: `/admin` route
- **Purpose**: Submit dashboard modification requests
- **Features**: Real-time change tracking, script generation, automated deployment
- **Status**: ⚠️ **NEEDS DEBUGGING** - Changes don't appear on live site

### **Backend API**
- **Framework**: FastAPI (Python)
- **Database**: JSON file-based storage
- **Hosting**: Azure VM (Ubuntu Linux)
- **Features**: Change management, script generation, automated deployment

### **Trading Engine**
- **Broker**: Alpaca Markets API
- **Strategies**: Mean reversion, momentum scalping
- **Features**: Real-time market data, position management, risk controls

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- Azure CLI
- SSH access to deployment VM

### Local Development

```bash
# Clone the repository
git clone https://github.com/kmulroy1972/mulroy-street-capital-trading-platform.git
cd mulroy-street-capital-trading-platform

# Install frontend dependencies
cd apps/web
npm install

# Start development server
npm run dev
```

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements-base.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and configurations

# Start the API server
cd apps/api
python main.py
```

## 📁 Project Structure

```
├── apps/
│   ├── web/                    # Next.js frontend dashboard
│   │   ├── app/
│   │   │   ├── admin/         # Admin panel for change requests
│   │   │   └── page.tsx       # Main dashboard
│   │   ├── components/
│   │   │   ├── Header.tsx     # Main header component
│   │   │   ├── modules/       # Dashboard modules
│   │   │   └── auth/          # Authentication components
│   │   └── lib/               # Utilities and API clients
│   ├── api/                   # FastAPI backend
│   └── engine/                # Trading engine
├── packages/
│   ├── core/                  # Core trading logic
│   ├── strategies/            # Trading strategies
│   └── monitoring/            # System monitoring
├── infra/                     # Infrastructure as Code (Bicep)
├── scripts/                   # Deployment and utility scripts
└── tests/                     # Test suites
```

## 🔧 Key Features

### **Real-Time Dashboard**
- Live market data and positions
- Performance charts and metrics
- Risk monitoring and alerts
- Order entry and management

### **Admin Panel (⚠️ Currently Non-Functional)**
- Web-based change submission
- Real-time request tracking  
- Automated script generation
- Build and deployment pipeline

### **Trading Engine**
- Multiple strategy support
- Risk management controls
- Production/staging environments
- Comprehensive backtesting

## 🐛 Known Issues

### **Critical: Admin Panel Deployment Disconnect**

**Problem**: Admin panel can submit changes, generate scripts, build successfully, and deploy without errors, but **NO CHANGES appear on the live dashboard**.

**Evidence**:
- ✅ UI works perfectly (form submission, error handling, real-time updates)
- ✅ API processes requests (creates change records, executes scripts)  
- ✅ Build process completes (Next.js compilation succeeds)
- ✅ Deployment succeeds (Azure Static Web Apps confirms upload)
- ❌ **Zero visible changes on live site** https://www.mulroystreetcap.com

**Possible Causes**:
1. Live site served from different source/deployment pipeline
2. Azure Static Web Apps deployment not connected to custom domain  
3. Caching/CDN layer preventing updates from appearing
4. File structure mismatch (editing wrong components)

**Technical Details**:
- VM Location: `172.174.232.173` (SSH access required)
- API Code: `/home/ktmulroy/trading-api/main.py`
- Source Code: `/home/ktmulroy/apps/web/`
- Deployment: Azure Static Web Apps via SWA CLI

**Files for Investigation**:
- `apps/web/app/admin/page.tsx` - Admin panel React component
- VM file: `/home/ktmulroy/trading-api/main.py` - FastAPI backend
- VM file: `/home/ktmulroy/trading-api/working_generators.py` - Script generators  
- VM file: `/home/ktmulroy/admin-changes.json` - Change queue data

## 🚀 Deployment

### **Frontend (Azure Static Web Apps)**
```bash
# Build the project
cd apps/web
npm run build

# Deploy to Azure
npx swa deploy ./out --deployment-token $DEPLOYMENT_TOKEN --env production
```

### **Backend (Azure VM)**
```bash
# SSH to VM
ssh -i ktmulroy-msc-key.pem ktmulroy@172.174.232.173

# Update and restart API
cd /home/ktmulroy/trading-api
git pull
python3 main.py
```

## 📊 API Endpoints

- `POST /api/admin/change-request` - Submit dashboard change
- `GET /api/admin/change-queue` - Get pending changes  
- `POST /api/admin/execute-change/{id}` - Execute specific change
- `GET /api/health` - System health check
- `GET /api/positions` - Current positions
- `GET /api/market-times` - Market hours data

## 🔒 Security & Environment

- Sensitive files excluded via `.gitignore`
- Environment variables for API keys
- SSH key authentication for VM access
- Production/staging environment separation

## 🤝 Contributing

This is a private trading platform. The admin panel functionality is currently broken and requires investigation by an experienced developer familiar with Next.js deployment pipelines and Azure Static Web Apps.

**Priority**: Fix the deployment disconnect preventing admin panel changes from appearing on the live dashboard.

## 📄 License

Private proprietary software. All rights reserved.

## 🆘 Support

The admin panel deployment issue has been extensively debugged without resolution. Professional development assistance is needed to identify why successful builds and deployments don't result in visible changes on the live site.

**Last Updated**: September 2025
