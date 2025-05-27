.PHONY: dev backend frontend test test-backend test-frontend clean install

# Development - run both frontend and backend concurrently
dev:
	@echo "Starting development servers..."
	@cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd frontend && npm run dev & \
	wait

# Backend only
backend:
	@echo "Starting backend server..."
	@cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend only
frontend:
	@echo "Starting frontend server..."
	@cd frontend && npm run dev

# Install dependencies
install:
	@echo "Installing dependencies..."
	@cd backend && poetry install
	@cd frontend && npm install

# Run all tests
test: test-backend test-frontend

# Run backend tests
test-backend:
	@echo "Running backend tests..."
	@cd backend && poetry run pytest -q

# Run frontend tests
test-frontend:
	@echo "Running frontend tests..."
	@cd frontend && npm test
	@cd frontend && npx cypress run

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@cd backend && rm -rf .pytest_cache __pycache__ .coverage
	@cd frontend && rm -rf .next node_modules/.cache
	
# Docker build
docker-build:
	@echo "Building Docker images..."
	@docker build -f Dockerfile.backend -t meme-maker-backend .
	@docker build -f Dockerfile.worker -t meme-maker-worker .

# Docker run development stack
docker-dev:
	@echo "Starting development stack with Docker Compose..."
	@docker-compose up --build 