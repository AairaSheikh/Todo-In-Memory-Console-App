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
