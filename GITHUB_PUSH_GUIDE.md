# How to Push Your Todo Project to GitHub

## Step-by-Step Guide

### Step 1: Initialize Git (if not already done)

```bash
# Navigate to your project root directory
cd /path/to/your/project

# Initialize git repository
git init

# Check git status
git status
```

### Step 2: Add Remote Repository

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/AairaSheikh/Todo-In-Memory-Console-App.git

# Verify the remote was added
git remote -v
```

**Expected output:**
```
origin  https://github.com/AairaSheikh/Todo-In-Memory-Console-App.git (fetch)
origin  https://github.com/AairaSheikh/Todo-In-Memory-Console-App.git (push)
```

### Step 3: Create .gitignore File

Create a `.gitignore` file to exclude sensitive files and dependencies:

```bash
# Create .gitignore file
cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.*.local

# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
yarn-debug.log*

# Build outputs
.next/
out/
build/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Database
*.db
*.sqlite

# Hypothesis
.hypothesis/

# Cache
.cache/
EOF
```

### Step 4: Stage All Files

```bash
# Add all files to staging area
git add .

# Check what will be committed
git status
```

### Step 5: Create Initial Commit

```bash
# Create your first commit
git commit -m "Initial commit: Todo Full-Stack Web Application

- Phase 1: In-memory console app with task management
- Phase 2: Full-stack web application with FastAPI backend and Next.js frontend
- Features: User authentication, task CRUD operations, database persistence
- Testing: 45+ property-based tests with comprehensive coverage
- Documentation: Complete setup and deployment guides"
```

### Step 6: Push to GitHub

```bash
# Push to GitHub (main branch)
git branch -M main
git push -u origin main
```

**If you get an authentication error:**

#### Option A: Using Personal Access Token (Recommended)

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token"
3. Select scopes: `repo` (full control of private repositories)
4. Copy the token
5. When prompted for password, paste the token instead

#### Option B: Using SSH Key

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add SSH key to GitHub
# Copy the public key from ~/.ssh/id_ed25519.pub
# Go to GitHub Settings → SSH and GPG keys → New SSH key
# Paste the key

# Change remote to SSH
git remote set-url origin git@github.com:AairaSheikh/Todo-In-Memory-Console-App.git

# Try pushing again
git push -u origin main
```

---

## Complete Commands (Copy & Paste)

### For Windows (PowerShell):

```powershell
# Navigate to project
cd C:\path\to\your\project

# Initialize git
git init

# Add remote
git remote add origin https://github.com/AairaSheikh/Todo-In-Memory-Console-App.git

# Create .gitignore
@"
.env
.env.local
node_modules/
__pycache__/
.next/
.pytest_cache/
.DS_Store
"@ | Out-File -Encoding UTF8 .gitignore

# Stage and commit
git add .
git commit -m "Initial commit: Todo Full-Stack Web Application"

# Push to GitHub
git branch -M main
git push -u origin main
```

### For Mac/Linux:

```bash
# Navigate to project
cd /path/to/your/project

# Initialize git
git init

# Add remote
git remote add origin https://github.com/AairaSheikh/Todo-In-Memory-Console-App.git

# Create .gitignore
cat > .gitignore << 'EOF'
.env
.env.local
node_modules/
__pycache__/
.next/
.pytest_cache/
.DS_Store
EOF

# Stage and commit
git add .
git commit -m "Initial commit: Todo Full-Stack Web Application"

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Verify on GitHub

1. Go to https://github.com/AairaSheikh/Todo-In-Memory-Console-App
2. You should see all your files uploaded
3. Check that `.env` files are NOT visible (they should be in .gitignore)

---

## Project Structure to Push

Your repository should contain:

```
Todo-In-Memory-Console-App/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── routes/
│   │   ├── main.py
│   │   ├── config.py
│   │   └── database.py
│   ├── tests/
│   ├── requirements.txt
│   ├── run.py
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── signin/
│   │   ├── signup/
│   │   ├── dashboard/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   ├── lib/
│   ├── __tests__/
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example
├── src/
│   ├── task.py
│   ├── task_list.py
│   └── console_interface.py
├── tests/
│   ├── test_task.py
│   ├── test_task_list.py
│   ├── test_console_interface.py
│   └── test_properties.py
├── main.py
├── .gitignore
├── README.md
├── ENVIRONMENT_SETUP_GUIDE.md
├── PHASE_2_COMPLETION_SUMMARY.md
└── IMPLEMENTATION_SUMMARY.md
```

---

## Create a Good README.md

Create a `README.md` file in your project root:

```markdown
# Todo Full-Stack Web Application

A complete todo application built with FastAPI backend and Next.js frontend, featuring user authentication, task management, and comprehensive property-based testing.

## Features

- **Phase 1**: In-memory console application with task management
- **Phase 2**: Full-stack web application with:
  - User registration and authentication (JWT)
  - Task CRUD operations
  - PostgreSQL database persistence
  - Responsive Next.js frontend
  - 45+ property-based tests

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- JWT Authentication
- Pytest with Hypothesis

### Frontend
- Next.js 16+
- React
- TypeScript
- Zustand (State Management)
- Axios (HTTP Client)

## Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database URL and JWT secret
python run.py
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your backend URL
npm run dev
```

## Environment Variables

See `ENVIRONMENT_SETUP_GUIDE.md` for detailed setup instructions.

### Backend (.env)
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret key for JWT signing
- `JWT_ALGORITHM`: JWT algorithm (HS256)
- `JWT_EXPIRATION_HOURS`: Token expiration time

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL`: Backend API URL

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/signin` - Login user
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user

### Tasks
- `GET /api/{user_id}/tasks` - List all tasks
- `POST /api/{user_id}/tasks` - Create task
- `GET /api/{user_id}/tasks/{id}` - Get single task
- `PUT /api/{user_id}/tasks/{id}` - Update task
- `DELETE /api/{user_id}/tasks/{id}` - Delete task
- `PATCH /api/{user_id}/tasks/{id}/complete` - Toggle completion

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Documentation

- `ENVIRONMENT_SETUP_GUIDE.md` - Detailed environment setup
- `PHASE_2_COMPLETION_SUMMARY.md` - Project completion summary
- `IMPLEMENTATION_SUMMARY.md` - Implementation details

## License

MIT

## Author

Aaira Sheikh
```

---

## Troubleshooting

### Problem: "fatal: not a git repository"

**Solution:**
```bash
git init
git remote add origin https://github.com/AairaSheikh/Todo-In-Memory-Console-App.git
```

### Problem: "Permission denied (publickey)"

**Solution:** Use HTTPS instead of SSH, or set up SSH keys properly

### Problem: "Updates were rejected because the tip of your current branch is behind"

**Solution:**
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Problem: ".env file is being tracked"

**Solution:**
```bash
# Remove .env from git tracking
git rm --cached .env
git rm --cached backend/.env
git rm --cached frontend/.env.local

# Commit the change
git commit -m "Remove .env files from tracking"
git push
```

---

## After Pushing

1. ✅ Verify files are on GitHub
2. ✅ Check that `.env` files are NOT visible
3. ✅ Add a description to your repository
4. ✅ Add topics: `todo`, `fastapi`, `nextjs`, `react`, `postgresql`
5. ✅ Share the link with others

---

## Next Steps

After pushing to GitHub:

1. **Add Collaborators** (if needed)
   - Go to Settings → Collaborators
   - Add team members

2. **Enable Issues** (for bug tracking)
   - Go to Settings → Features
   - Enable Issues

3. **Add GitHub Actions** (for CI/CD)
   - Create `.github/workflows/tests.yml`
   - Run tests automatically on push

4. **Create Releases**
   - Tag your commits with versions
   - Create release notes

---

## Commands Summary

```bash
# One-time setup
git init
git remote add origin https://github.com/AairaSheikh/Todo-In-Memory-Console-App.git

# For each update
git add .
git commit -m "Your commit message"
git push origin main

# Check status
git status
git log
```

You're all set! Your project is now on GitHub.
