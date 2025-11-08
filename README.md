# Project Calculator: Pricing Engine and Synchronization Service

## Overview

This repository contains the source code for a comprehensive **Pricing Engine and Synchronization Service** designed for a construction or home-building business. The system is built around a robust database model to manage pricing, materials, and build specifications, and exposes a powerful API for calculating project costs based on detailed input parameters. It also includes a synchronization service for external data integration, specifically with Google Sheets.

The project is structured as a full-stack application with a Python backend, a PostgreSQL database, and a set of Docker configurations for easy deployment.

## Key Features

*   **Advanced Pricing Engine (`src/pricing_engine.py`):** A core service that calculates the final cost of a construction project based on complex inputs such as house dimensions, ceiling type, roof overhang, insulation specifications, and optional add-ons (terrace, porch, windows, doors).
*   **Database Models (`src/models.py`):** Comprehensive SQLAlchemy models defining the project's data structure, including:
    *   `BuildTechnology`, `InsulationBrand`, `InsulationThickness`, `StoreyType`, `Contour`.
    *   Detailed pricing tables: `PriceList`, `AddonPrice`, `WindowPrice`, `DoorPrice`.
    *   Configuration tables: `StandardInclusion`, `GlobalDefault`.
    *   An `PriceAudit` table for tracking changes to pricing entities.
*   **Data Synchronization Service (`src/sync_service.py`):** A dedicated service for synchronizing pricing data from external sources, with explicit support for integration with **Google Sheets**.
*   **API Specification (`API_Spec.json`):** A JSON file detailing the API endpoints, likely for integration with a frontend or external system.
*   **Testing Suite (`tests/`):** A dedicated directory with a stable test suite to ensure the accuracy and reliability of the pricing logic. Includes tests for the pricing engine and utility functions.
*   **Containerized Deployment:** Includes `Dockerfile`, `docker-compose.yml`, and `docker-compose.test.yml` for easy setup and deployment using Docker.

## Project Structure

The repository is organized as follows:

```
.
├── API_Spec.json               # API endpoint specification
├── Dockerfile                  # Docker image definition for the application
├── README.md                   # This file
├── docker-compose.yml          # Docker configuration for production/development
├── docker-compose.test.yml     # Docker configuration for running tests
├── docs/
│   └── GOOGLE_SHEETS_INTEGRATION.md # Documentation on Google Sheets integration
├── requirements.txt            # Python dependencies
└── src/
    ├── main.py                 # Main application entry point (likely FastAPI/Flask)
    ├── database.py             # Database connection and session management
    ├── models.py               # SQLAlchemy ORM models
    ├── pricing_engine.py       # Core logic for cost calculation
    ├── schemas.py              # Pydantic schemas for API request/response validation
    └── sync_service.py         # Logic for synchronizing data from external sources
└── tests/
    ├── conftest.py             # Pytest fixtures and configuration
    ├── run_test.py             # Script to execute the test suite
    ├── test_pricing.py         # Tests for general pricing logic
    └── test_pricing_engine.py  # Specific tests for the core pricing engine
```

## Setup and Installation

The project is designed to be run using Docker and Docker Compose.

### Prerequisites

*   Docker
*   Docker Compose

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/aruxojuyu665/project-calculator.git
    cd project-calculator
    ```

2.  **Configure Environment:**
    Copy the example environment file and fill in your specific database and service credentials.
    ```bash
    cp .env.example .env
    # Edit the .env file
    ```

3.  **Build and Run the Services:**
    This command will build the application image, set up the database, and start the services (API and Sync Service).
    ```bash
    docker-compose up --build
    ```

4.  **Run Tests (Optional):**
    Use the dedicated test compose file to run the test suite.
    ```bash
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    ```

## API Usage

The main application exposes an API for project calculation. Refer to `API_Spec.json` for a detailed specification of all endpoints.

The primary endpoint is likely a `POST` request to `/calculate` which accepts a `CalculateRequestSchema` (defined in `src/schemas.py`) and returns a detailed `CalculateResponseSchema` with the final cost breakdown.

## Data Synchronization

The system is configured to synchronize pricing data. For details on setting up the Google Sheets integration, please refer to the dedicated documentation:

*   [**GOOGLE_SHEETS_INTEGRATION.md**](docs/GOOGLE_SHEETS_INTEGRATION.md)

This document outlines the necessary steps for authentication and data mapping to ensure the pricing engine operates with the latest data.
