.PHONY: help install test lint format clean build up down logs shell

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

test:  ## Run tests
	python -m pytest -v

lint:  ## Run linting
	python -m flake8 backend/ frontend/ --max-line-length=120

format:  ## Format code
	python -m black backend/ frontend/ --line-length=120

clean:  ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

build:  ## Build Docker containers
	docker-compose build

up:  ## Start services
	docker-compose up -d

down:  ## Stop services
	docker-compose down

logs:  ## View logs
	docker-compose logs -f

shell-backend:  ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend:  ## Open shell in frontend container
	docker-compose exec frontend /bin/bash

dev-setup:  ## Set up development environment
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	pip install -r requirements.txt
	@echo "Development environment ready!"

check:  ## Run all checks (lint, test, format)
	python dev.py all

start-dev:  ## Start development servers
	python dev.py start
