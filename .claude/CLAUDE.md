# KLDAFinTech - Claude Code Configuration

## Environment Overview
**KLDAFinTech** is the financial technology division of KLDA Technologies OÜ.

This repository contains multiple financial projects:
- **RateRadar.com**: Financial information platform (primary project)
- [Future projects...]

---

## Repository Structure
```
C:\Users\PC\Desktop\KLDAFinTech\
├── RateRadar.com/          # Main subscription platform
│   ├── 00-PLANNING/
│   ├── 01-DESIGN/
│   ├── 02-BACKEND/
│   ├── 03-FRONTEND/
│   ├── 04-INFRASTRUCTURE/
│   ├── 05-CAMPAIGNS/
│   ├── 06-DOCS/
│   ├── 07-TESTS/
│   └── 08-LEGAL/
└── [Future projects]/
```

---

## Important Context

### **KLDAFinTech vs CRM KoLor**
- **KLDAFinTech**: Financial technology projects (this repo)
- **CRM KoLor**: Separate repository for dental clinic CRM
- **NO OVERLAP** between these two environments

### **KLDA Technologies OÜ**
- Estonian registered entity
- Focus areas:
  1. Financial technology platforms
  2. Advertising infrastructure services
  3. Digital marketing solutions
  4. Business intelligence tools

---

## Current Active Project: RateRadar.com

**Mission**: Information-only platform providing:
- Real-time market data
- Economic calendars
- News aggregation
- Loan rate comparisons (no applications)

**User Model**:
- Free Navigators (via ad campaigns)
- Premium Subscribers (€9.99/month)

**Tech Stack**:
- Backend: Node.js + Express, Python
- Frontend: Vue 3 + Vite + Tailwind CSS
- Database: PostgreSQL + TimescaleDB
- APIs: Polygon.io, Economic Calendar APIs

---

## Development Guidelines

### Code Standards
- Follow each project's structure strictly
- Use ES6+ JavaScript/TypeScript
- Vue 3 Composition API for frontend
- RESTful API design for backend
- Document all endpoints

### Git Workflow
- Main branch: `main`
- Feature branches: `feature/<project>/<name>`
- Example: `feature/rateradar/loan-calculator`

### Commit Format
```
<type>(<project>): <description>

Examples:
feat(rateradar): Add loan comparison tool
fix(rateradar): Fix chart rendering issue
docs(rateradar): Update API documentation
```

---

## Navigation

When working on a specific project, navigate to its folder:
```bash
cd RateRadar.com
```

Each project has its own README.md and documentation.
