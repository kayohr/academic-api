# academic-api

REST API for academic management — simulating a real-world university system.

## Stack

- **Node.js 20 + Fastify** — high-performance REST API
- **PostgreSQL 16** — relational database with versioned migrations
- **Docker + Docker Compose** — fully containerized local environment
- **JWT + RBAC** — authentication with roles: `admin`, `coordenador`, `professor`, `aluno`
- **Python** — data seed scripts and academic performance reports
- **Swagger/OpenAPI** — interactive API documentation

## Domains

| Domain | Entities |
|--------|----------|
| Institution | Campus, Department, Course |
| People | Student, Professor, Staff |
| Academic | Subject, Curriculum, Semester, Class, Enrollment |
| Evaluation | Grade, Attendance, Academic Record |
| Auth | User, Roles, Refresh Token, Audit Log |

## Getting started

```bash
# Copy environment variables
cp .env.example .env

# Start all services
docker-compose up

# API available at
http://localhost:3000

# Health check
curl http://localhost:3000/health
```

## Development

```bash
npm install
npm run dev         # start with hot reload
npm run migrate:up  # apply migrations
npm test            # run tests
```

## Seed data (Python)

```bash
docker-compose --profile seed run seed
# or locally:
cd scripts && pip install -r requirements.txt && python seed.py
```

## API Documentation

Swagger UI available at `http://localhost:3000/docs` after startup.

## Project structure

```
src/
├── modules/        # business domains (auth, aluno, disciplina...)
├── shared/         # error handlers, middlewares, helpers
├── config/         # environment and database config
└── app.js          # Fastify bootstrap
migrations/         # versioned SQL migrations
scripts/            # Python seed and report scripts
tests/              # unit and integration tests
docs/               # OpenAPI spec and schema docs
```

## Issues & Roadmap

See the [GitHub Issues](https://github.com/kayohr/academic-api/issues) for the full development roadmap.
