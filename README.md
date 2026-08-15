# SaaS Admin Dashboard

A full-stack e-commerce and SaaS admin dashboard with complex state management, real-time features, and comprehensive business management capabilities.

## Tech Stack

### Frontend
- React 18+
- shadcn/ui components
- Tailwind CSS
- Zustand (state management)
- Recharts (analytics visualizations)

### Backend
- FastAPI (Python)
- PostgreSQL
- SQLAlchemy (ORM)
- Pydantic (validation)
- WebSockets (real-time)

### Integrations
- Authentication: Email/password + OAuth (Google/GitHub)
- Payments: PayPal, Razorpay, GPAY, BHIM
- Storage: AWS S3 / Cloudinary
- Email: SendGrid / Resend

### Deployment
- Frontend: Vercel
- Backend: Railway / Render
- Database: Managed PostgreSQL

## Features

- **User Management**: CRUD, RBAC, impersonation, audit logs
- **Product Management**: Complex filtering, searching, inventory
- **Order Management**: One-time purchases, payment processing
- **Subscription Management**: Recurring billing, trials, plans
- **Invoice System**: Generation, tracking, management
- **Analytics Dashboard**: Real-time metrics, financial health, retention
- **Real-time Updates**: WebSocket-powered live dashboards
- **Multi-tenant Support**: Role-based access control

## Roles

- Admin (full access)
- Manager/Editor (business operations)
- Support Staff (customer support)
- Customer/Subscriber (limited access)

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- npm/yarn

### Installation

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Environment Variables

See `.env.example` files in both `backend/` and `frontend/` directories.

### Running Locally

```bash
# Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev
```

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # Configuration, security
│   │   ├── models/    # Database models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── utils/     # Utilities
│   └── tests/         # Backend tests
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/     # Zustand stores
│   │   └── lib/       # Utilities
│   └── tests/         # Frontend tests
└── README.md
```

## MVP Scale Targets

- 100-1,000 concurrent users
- 5,000-10,000 transactional records
- 1-5 GB data volume

## License

MIT
