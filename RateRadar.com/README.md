# 📊 RateRadar.com

**Real-Time Financial Information Platform**

> Neutral, subscription-based platform providing economic data, market prices, news, and loan rate comparisons.

---

## 🎯 Mission

RateRadar.com is an **information-only platform** that provides:
- Real-time asset prices (stocks, forex, commodities, crypto)
- Economic calendar with global events
- Aggregated financial news
- Loan rate comparison tool

**We do NOT**:
- Provide financial advice
- Process loan applications
- Collect personal financial data
- Offer investment recommendations

---

## 🏗️ Project Structure

```
RateRadar.com/
├── 00-PLANNING/          Planning & specs
├── 01-DESIGN/            UI/UX design
├── 02-BACKEND/           Server-side code
│   ├── api/             Node.js Express API
│   ├── database/        PostgreSQL + TimescaleDB
│   └── data-ingestion/  Python scripts for data fetching
├── 03-FRONTEND/          Vue 3 client app
├── 04-INFRASTRUCTURE/    Docker, deployment
├── 05-CAMPAIGNS/         Marketing campaigns
├── 06-DOCS/              Documentation
├── 07-TESTS/             Testing
└── 08-LEGAL/             Legal documents
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL 14+ with TimescaleDB extension
- Git

### Setup

```bash
# 1. Clone repository
git clone https://github.com/xyVar/RateRadar.com.git
cd RateRadar.com

# 2. Install backend dependencies
cd 02-BACKEND/api
npm install

# 3. Install frontend dependencies
cd ../../03-FRONTEND/app
npm install

# 4. Set up database
psql -U postgres -c "CREATE DATABASE rateradar;"
psql -U postgres -d rateradar -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# 5. Configure environment
cp .env.example .env
# Edit .env with your API keys and database credentials

# 6. Start development servers
# Terminal 1 - Backend:
cd 02-BACKEND/api && npm run dev

# Terminal 2 - Frontend:
cd 03-FRONTEND/app && npm run dev
```

---

## 💰 Subscription Model

### Free Tier (Navigators)
- Limited asset coverage
- Ad-supported
- Basic economic calendar
- Limited loan institutions

### Premium Tier (Subscribers)
- **€9.99/month** or **€99/year**
- Ad-free experience
- Full asset coverage
- Advanced filters & alerts
- Export capabilities

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, Tailwind CSS, Chart.js |
| Backend | Node.js, Express, Python |
| Database | PostgreSQL, TimescaleDB |
| Caching | Redis |
| APIs | Polygon.io, Economic Calendar APIs |
| Deployment | Docker, Nginx, AWS |
| CI/CD | GitHub Actions |

---

## 📚 Documentation

- [API Documentation](06-DOCS/api-documentation.md)
- [Developer Setup](06-DOCS/developer-setup.md)
- [Deployment Guide](06-DOCS/deployment-guide.md)
- [User Guide](06-DOCS/user-guide.md)

---

## 🤝 Contributing

This is a proprietary project by KLDA Technologies OÜ. Internal contributions only.

---

## 📄 License

Copyright © 2025 KLDA Technologies OÜ. All rights reserved.

---

## 📧 Contact

- Website: https://rateradar.com
- Support: support@rateradar.com
- Company: KLDA Technologies OÜ
