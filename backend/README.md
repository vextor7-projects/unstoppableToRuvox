Ruvox Backend

This repository contains the backend service for the Ruvox Multi-Chain Wallet and Smart Contract Payment System. It is built with FastAPI and provides a complete API for managing wallets, processing payments, handling compliance, and more, as specified in the project architecture.

Project Overview

The Ruvox backend is a high-performance asynchronous API designed to serve the Ruvox React Native mobile application. Its key responsibilities include:

API Gateway: Providing all endpoints for the mobile client.

Business Logic: Orchestrating complex workflows like payment processing, user verification, and internal ledger management.

Database Interaction: Managing all data persistence with PostgreSQL via SQLAlchemy.

Blockchain Communication: Interacting with Solana, EVM chains (Base, Polygon), and Bitcoin nodes/explorers.

Security: Handling user authentication (JWT), PIN/2FA verification, and secure data encryption.

External Service Integration: Communicating with third-party services like Chainalysis, CoinGecko, and fiat on-ramps.

Asynchronous Tasks: Managing background jobs like balance syncing, processing withdrawals, and sending notifications via Celery.

Tech Stack

Framework: FastAPI

Database: PostgreSQL (with asyncpg)

Migrations: Alembic

Cache / Task Broker: Redis

Background Tasks: Celery

Blockchain: solana-py, web3.py, python-bitcoinlib, anchorpy

Security: passlib[bcrypt], python-jose[cryptography], pyotp

Environment: Poetry, Docker

Local Development Setup

These instructions guide you through setting up the backend for local development.

1. Prerequisites

Poetry

Docker & Docker Compose

Python 3.11

2. Environment Configuration

Clone the repository:

git clone <your-repo-url>
cd ruvox-backend


Create the .env file:
Copy the .env.template (or the one provided) to a new file named .env.

cp .env.template .env


Fill in Secrets:
Open the .env file and fill in all required secrets, especially:

SECRET_KEY (generate with openssl rand -hex 32)

Database variables (should match docker-compose.yml defaults)

Redis variables (should match docker-compose.yml defaults)

Your personal RPC node URLs (e.g., from QuickNode or Alchemy)

API keys for external services (Chainalysis, CoinGecko, etc.)

3. Install Dependencies

Install all project dependencies using Poetry. This will create a local .venv virtual environment.

poetry install


4. Launch Services

Run the database (PostgreSQL) and cache (Redis) services using Docker Compose:

docker-compose up -d db redis


5. Run Database Migrations

With the database container running, apply the initial database schema:

poetry run alembic upgrade head


6. Run the Application

You can now start the FastAPI server with hot-reloading:

poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


The API will be available at http://localhost:8000, and the interactive documentation (Swagger UI) will be at http://localhost:8000/docs.

Running with Docker Compose (Full Stack)

To run the entire backend stack (FastAPI, Celery workers, Beat, Flower, DB, Redis) as defined in docker-compose.yml:

docker-compose up --build


The API will be available at http://localhost:8000 and the Flower (Celery) dashboard at http://localhost:5555.

Running Tests

To run the test suite:

poetry run pytest
