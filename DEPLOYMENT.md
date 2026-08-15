# Deployment Guide

This guide covers deploying the SaaS Admin Dashboard to production.

## Prerequisites

- PostgreSQL database (managed service recommended)
- Vercel account (for frontend)
- Railway/Render account (for backend)
- OAuth credentials (Google, GitHub)
- Payment gateway credentials (PayPal, Razorpay)
- Storage credentials (AWS S3 or Cloudinary)
- Email service credentials (SendGrid or Resend)

## Backend Deployment (Railway/Render)

### 1. Prepare the Backend

```bash
cd backend
```

### 2. Set Environment Variables

Configure the following environment variables in Railway/Render:

```
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
FRONTEND_URL=https://your-frontend.vercel.app
```

### 3. Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Add PostgreSQL database
railway add postgresql

# Set environment variables
railway variables set DATABASE_URL=$DATABASE_URL
railway variables set SECRET_KEY=$SECRET_KEY
# ... set other variables

# Deploy
railway up
```

### 4. Deploy to Render

```bash
# Install Render CLI
npm install -g render-cli

# Login to Render
render login

# Create web service
render create web-service

# Set build and start commands
# Build: pip install -r requirements.txt
# Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Add environment variables in Render dashboard
# Deploy
render deploy
```

### 5. Run Database Migrations

```bash
# SSH into the service or use Railway CLI
railway run python -m alembic upgrade head
```

## Frontend Deployment (Vercel)

### 1. Prepare the Frontend

```bash
cd frontend
```

### 2. Set Environment Variables

Create `.env.production`:

```
VITE_API_URL=https://your-backend.railway.app
```

### 3. Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

### 4. Configure Custom Domain (Optional)

1. Go to Vercel dashboard
2. Select your project
3. Go to Settings > Domains
4. Add your custom domain
5. Configure DNS records

## Database Setup

### PostgreSQL Configuration

1. Create a managed PostgreSQL instance (Railway, Render, AWS RDS, etc.)
2. Get connection string
3. Set `DATABASE_URL` environment variable
4. Run migrations

### Run Migrations

```bash
cd backend
python -m alembic upgrade head
```

### Seed Initial Data

Create a script to seed initial roles and admin user:

```python
# backend/scripts/seed.py
from app.core.database import SessionLocal
from app.models.user import User, Role
from app.core.security import get_password_hash

db = SessionLocal()

# Create roles
roles = [
    Role(name="admin", description="Full system access"),
    Role(name="manager", description="Business operations"),
    Role(name="support", description="Customer support"),
    Role(name="customer", description="Regular customer"),
]

for role in roles:
    db.add(role)

# Create admin user
admin = User(
    email="admin@example.com",
    username="admin",
    full_name="Admin User",
    hashed_password=get_password_hash("admin_password"),
    is_active=True,
    is_verified=True,
    is_superuser=True,
)

admin.roles.append(db.query(Role).filter(Role.name == "admin").first())
db.add(admin)

db.commit()
```

## OAuth Setup

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `https://your-backend.railway.app/api/v1/auth/google/callback`
6. Copy Client ID and Client Secret

### GitHub OAuth

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App
3. Set Authorization callback URL: `https://your-backend.railway.app/api/v1/auth/github/callback`
4. Copy Client ID and Client Secret

## Payment Gateway Setup

### PayPal

1. Create PayPal Developer account
2. Create REST API app
3. Get Client ID and Client Secret
4. Set environment variables

### Razorpay

1. Create Razorpay account
2. Get Key ID and Key Secret
3. Set environment variables

## Storage Setup

### AWS S3

1. Create AWS account
2. Create S3 bucket
3. Create IAM user with S3 access
4. Get Access Key ID and Secret Access Key
5. Set environment variables

### Cloudinary

1. Create Cloudinary account
2. Get Cloud Name, API Key, and API Secret
3. Set environment variables

## Email Setup

### SendGrid

1. Create SendGrid account
2. Get API Key
3. Verify sender email
4. Set environment variables

### Resend

1. Create Resend account
2. Get API Key
3. Set environment variables

## Monitoring and Logging

### Railway Monitoring

- Railway provides built-in metrics and logs
- Check resource usage in Railway dashboard

### Vercel Analytics

- Vercel provides analytics for frontend
- Enable in Vercel dashboard

### Application Logs

```bash
# View Railway logs
railway logs

# View Render logs
render logs
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **Secrets**: Use platform secret management
3. **HTTPS**: Ensure all services use HTTPS
4. **CORS**: Configure CORS properly
5. **Rate Limiting**: Implement rate limiting for API
6. **Database**: Use managed database with backups

## Troubleshooting

### Backend Issues

```bash
# Check logs
railway logs

# Restart service
railway restart

# SSH into service
railway ssh
```

### Frontend Issues

```bash
# Check Vercel logs
vercel logs

# Redeploy
vercel --prod
```

### Database Issues

```bash
# Check connection
railway run python -c "from app.core.database import engine; print(engine.connect())"

# Run migrations
railway run python -m alembic upgrade head
```

## Scaling

### Backend Scaling

- Increase resources in Railway/Render
- Add caching with Redis
- Use load balancer for high traffic

### Frontend Scaling

- Vercel automatically scales
- Use CDN for static assets
- Implement edge functions

## Backup Strategy

### Database Backups

- Use managed database backups
- Set up automated backups
- Test restore process

### File Backups

- Use S3/Cloudinary for file storage
- Enable versioning
- Regular exports

## Post-Deployment Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] Database migrations run
- [ ] Environment variables configured
- [ ] OAuth providers configured
- [ ] Payment gateways configured
- [ ] Storage configured
- [ ] Email service configured
- [ ] SSL/HTTPS enabled
- [ ] CORS configured
- [ ] Health check passing
- [ ] Monitoring enabled
- [ ] Logging configured
- [ ] Backup strategy in place
- [ ] Test user journeys
- [ ] Load testing performed
