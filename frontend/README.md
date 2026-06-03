# Material Ingestion Frontend

This repository contains the frontend application for the Material Ingestion Pipeline, built with React, Vite, and TypeScript. It provides a user interface to interact with the Python-based backend API, allowing users to trigger ingestion processes, monitor status, and view results.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Node.js** (LTS version recommended, e.g., 18.x or 20.x)
*   **npm** (Node Package Manager, usually comes with Node.js) or **Yarn**

## Setup

Follow these steps to get the frontend application up and running on your local machine.

### 1. Clone the Repository

If you haven't already, clone the `material-ingestion-pipeline` repository. The frontend code resides in the `frontend/` directory.

```bash
git clone https://github.com/siddhant61/material-ingestion-pipeline.git
cd material-ingestion-pipeline/frontend
```

### 2. Install Dependencies

Navigate into the `frontend` directory and install the required Node.js dependencies:

```bash
cd frontend
npm install
# or if you prefer yarn
# yarn install
```

## Running the Development Server

To start the development server, which includes hot module replacement (HMR) for a fast development experience:

```bash
npm run dev
# or
# yarn dev
```

The application will typically be available at `http://localhost:5173` (or another port if 5173 is in use).

**Note on Backend API:**
This frontend application is configured to proxy API requests from `/api` to the backend running at `http://localhost:8000`. Ensure your Python backend (from the `material-ingestion-pipeline` project) is running and accessible at this address for the frontend to function correctly.

## Building for Production

To create a production-ready build of the application:

```bash
npm run build
# or
# yarn build
```

This command will compile the TypeScript code and bundle the assets into the `dist/` directory, ready for deployment.

## Running Tests

The project uses Vitest for unit and component testing.

### Run all tests

To execute all tests once:

```bash
npm test
# or
# yarn test
```

### Run tests in watch mode

To run tests in watch mode (re-runs tests on file changes):

```bash
npm test -- --watch
# or
# yarn test -- --watch
```

### Run tests with UI

To run tests and view results in a browser-based UI:

```bash
npm run test:ui
# or
# yarn test:ui
```

## Linting

To check for linting errors and enforce code style:

```bash
npm run lint
# or
# yarn lint
```