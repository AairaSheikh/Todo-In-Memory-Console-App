# Environment Setup Guide - Todo Full-Stack Application

## Overview

Your application needs environment variables to connect the frontend to the backend and to configure the backend database and security keys. This guide explains everything in detail.

---

## Part 1: Backend Environment Setup

### What is `.env` file?

The `.env` file is a configuration file that stores sensitive information like database URLs and secret keys. It's NOT pushed to Git (it's in `.gitignore`).

### Step 1: Create Backend `.env` File

1. Navigate to the `backend` folder
2. Create a new file named `.env` (note: no extension, just `.env`)
3. Copy the content from `.env.example` and fill in your values

### Step 2: Fill in Backend Environment Variables

```bash
# backend/.env

# 1. DATABASE_URL - Connection string to your PostgreSQL database
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db

# 2. JWT_SECRET_KEY - Secret key for signing JWT tokens (MUST be random and secure)
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production

# 3. JWT_ALGORITHM - Algorithm for JWT signing (usually HS256)
JWT_ALGORITHM=HS256

# 4. JWT_EXPIRATION_HOURS - How long JWT tokens are valid (in hours)
JWT_EXPIRATION_HOURS=24

# 5. ENVIRONMENT - Development or production
ENVIRONMENT=development
```

### Detailed Explanation of Each Variable:

#### 1. **DATABASE_URL** (PostgreSQL Connection String)

This tells your backend where to find the database.

**Format:**
```
postgresql://username:password@host:port/database_name
```

**Examples:**

**Local Development (using PostgreSQL locally):**
```
postgresql://postgres:password@localhost:5432/todo_db
```

**Neon Serverless PostgreSQL (Cloud):**
```
postgresql://user:password@ep-cool-name.us-east-1.neon.tech/todo_db?sslmode=require
```

**How to get Neon URL:**
1. Go to https://neon.tech
2. Sign up and create a project
3. Create a database named `todo_db`
4. Copy the connection string from the dashboard
5. Paste it in your `.env` file

#### 2. **JWT_SECRET_KEY** (Security Key)

This is a random string used to sign and verify JWT tokens. It's like a password for your tokens.

**How to generate a secure key:**

**Option A: Using Python**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option B: Using Node.js**
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

**Option C: Using OpenSSL**
```bash
openssl rand -hex 32
```

**Example output:**
```
aB3xY9kL2mN5pQ8rS1tU4vW7xY0zC3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5z
```

**Important:** 
- Make it random and long (at least 32 characters)
- Change it in production
- Never share it
- Never commit it to Git

#### 3. **JWT_ALGORITHM**

The algorithm used to sign tokens. Usually `HS256` (HMAC with SHA-256).

```
JWT_ALGORITHM=HS256
```

#### 4. **JWT_EXPIRATION_HOURS**

How long a user stays logged in before needing to log in again.

```
JWT_EXPIRATION_HOURS=24  # User stays logged in for 24 hours
```

#### 5. **ENVIRONMENT**

Tells the app whether it's in development or production mode.

```
ENVIRONMENT=development  # Use "production" when deployed
```

---

## Part 2: Frontend Environment Setup

### Step 1: Create Frontend `.env.local` File

1. Navigate to the `frontend` folder
2. Create a new file named `.env.local` (Next.js uses `.env.local` for local development)
3. Add your backend URL

### Step 2: Fill in Frontend Environment Variables

```bash
# frontend/.env.local

# Backend API URL - Where the frontend sends requests to
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Detailed Explanation:

#### **NEXT_PUBLIC_API_URL** (Backend URL)

This tells your frontend where to find the backend API.

**Format:**
```
http://host:port
```

**Examples:**

**Local Development (Backend running on your computer):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Production (Backend deployed on a server):**
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Important Notes:**
- The `NEXT_PUBLIC_` prefix means this variable is exposed to the browser (it's not secret)
- It must start with `http://` or `https://`
- Make sure the backend is running on this URL before starting the frontend
- In production, use `https://` (secure)

---

## Part 3: Complete Setup Checklist

### Backend Setup

- [ ] Create `backend/.env` file
- [ ] Set `DATABASE_URL` to your PostgreSQL connection string
- [ ] Generate a secure `JWT_SECRET_KEY` using one of the methods above
- [ ] Set `JWT_ALGORITHM=HS256`
- [ ] Set `JWT_EXPIRATION_HOURS=24`
- [ ] Set `ENVIRONMENT=development`

### Frontend Setup

- [ ] Create `frontend/.env.local` file
- [ ] Set `NEXT_PUBLIC_API_URL=http://localhost:8000`

---

## Part 4: Running the Application

### Step 1: Start the Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python run.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Start the Frontend

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Run the frontend development server
npm run dev
```

**Expected output:**
```
> next dev
  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
```

### Step 3: Open in Browser

1. Open http://localhost:3000 in your browser
2. You should see the Todo application
3. Try signing up with an email and password

---

## Part 5: Troubleshooting

### Problem: "Cannot connect to backend"

**Solution:**
1. Make sure backend is running on `http://localhost:8000`
2. Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
3. Make sure it matches the backend URL

### Problem: "Database connection failed"

**Solution:**
1. Check your `DATABASE_URL` in `backend/.env`
2. Make sure PostgreSQL is running
3. Verify the username, password, and database name are correct

### Problem: "Invalid token" or "Unauthorized"

**Solution:**
1. Check that `JWT_SECRET_KEY` is set in `backend/.env`
2. Make sure it's a random, secure string
3. Try logging out and logging back in

### Problem: "Port 8000 already in use"

**Solution:**
```bash
# Kill the process using port 8000
# On Mac/Linux:
lsof -ti:8000 | xargs kill -9

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Part 6: Environment Variables Summary

### Backend (.env)

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@localhost:5432/todo_db` |
| `JWT_SECRET_KEY` | Token signing key | `aB3xY9kL2mN5pQ8rS1tU4vW7xY0zC3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5z` |
| `JWT_ALGORITHM` | Token algorithm | `HS256` |
| `JWT_EXPIRATION_HOURS` | Token validity | `24` |
| `ENVIRONMENT` | Dev/Prod mode | `development` |

### Frontend (.env.local)

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend URL | `http://localhost:8000` |

---

## Part 7: Production Deployment

When deploying to production:

### Backend Changes

1. Change `ENVIRONMENT=production`
2. Use a strong, random `JWT_SECRET_KEY`
3. Use a production PostgreSQL database (like Neon)
4. Use `https://` for all URLs

### Frontend Changes

1. Change `NEXT_PUBLIC_API_URL` to your production backend URL
2. Example: `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`

### Example Production `.env` (Backend)

```bash
DATABASE_URL=postgresql://user:pass@ep-cool-name.us-east-1.neon.tech/todo_db?sslmode=require
JWT_SECRET_KEY=aB3xY9kL2mN5pQ8rS1tU4vW7xY0zC3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5z
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENVIRONMENT=production
```

### Example Production `.env.local` (Frontend)

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Part 8: Security Best Practices

1. **Never commit `.env` files to Git** - They're already in `.gitignore`
2. **Use strong, random keys** - At least 32 characters
3. **Change keys in production** - Don't use development keys
4. **Use HTTPS in production** - Always use `https://` for production URLs
5. **Rotate keys regularly** - Change JWT_SECRET_KEY periodically
6. **Use environment-specific values** - Different keys for dev, staging, production

---

## Quick Start Commands

### Generate JWT Secret Key

```bash
# Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# OpenSSL
openssl rand -hex 32
```

### Start Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### Access Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Summary

1. **Backend `.env`** - Contains database URL and security keys
2. **Frontend `.env.local`** - Contains backend API URL
3. **Never commit** - These files contain secrets
4. **Generate secure keys** - Use random, long strings
5. **Match URLs** - Frontend URL must point to backend URL
6. **Test locally first** - Before deploying to production

You're all set! Your application is now configured and ready to run.
