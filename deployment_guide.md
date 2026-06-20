# Cloud Storage & Deployment Guide - Diabetes Prediction System

This guide outlines how to migrate the local SQLite database to a cloud database (PostgreSQL/MySQL) and deploy the full-stack container to the cloud (AWS, Azure, or GCP).

---

## 1. Migrating Database to the Cloud (PostgreSQL / MySQL)

Currently, the application uses local SQLite (`diabetes.db`). To store the data in the cloud, you can provision a managed database instance (such as **AWS RDS**, **Azure SQL Database**, or **GCP Cloud SQL**) and redirect your application.

### Step 1: Install Database Adapter
For PostgreSQL, install `psycopg2-binary` inside the backend env:
```bash
pip install psycopg2-binary
```
For MySQL, install `pymysql`:
```bash
pip install pymysql
```

### Step 2: Update Connection string in [backend/database.py](file:///d:/dps/backend/database.py)
SQLAlchemy abstractly handles table management, so changing the connection URL is all that is required. Update `backend/database.py` to load from an environment variable:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Default to local SQLite, but read from cloud DB URL if configured
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./diabetes.db")

# SQLite needs check_same_thread=False, but cloud databases (PostgreSQL/MySQL) do not.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

When deploying, set the `DATABASE_URL` environment variable:
*   **PostgreSQL**: `postgresql://db_user:db_password@your-rds-endpoint.amazonaws.com:5432/diabetes_db`
*   **MySQL**: `mysql+pymysql://db_user:db_password@your-cloudsql-ip:3306/diabetes_db`

---

## 2. Dockerizing the Application

We have created a **[Dockerfile](file:///d:/dps/Dockerfile)** in the root workspace directory. This bundles the backend FastAPI engine, pre-trains the ML model on the dataset, and packages the frontend files.

To build and test the container locally:
```bash
# Build the Docker image
docker build -t diabetes-prediction-system .

# Run the container (binds container port 8080 to host port 80)
docker run -d -p 80:8080 -e GEMINI_API_KEY="your-api-key" diabetes-prediction-system
```

---

## 3. Cloud Deployment Scenarios (AWS, Azure, GCP)

### Option A: Google Cloud Platform (GCP) - *Recommended / Easiest*
GCP is excellent for serverless container deployment using **Cloud Run** and **Cloud SQL**.

1.  **Create a Cloud SQL (PostgreSQL) Instance**:
    *   Set up a PostgreSQL database and create a database named `diabetes_db`.
2.  **Deploy using Cloud Run**:
    *   Run the command from your workspace:
        ```bash
        gcloud run deploy diabetes-system --source . --allow-unauthenticated
        ```
    *   When prompted, set these Environment Variables:
        *   `DATABASE_URL`: Your PostgreSQL connection string.
        *   `GEMINI_API_KEY`: Your Gemini API Key.
    *   Cloud Run will automatically build, containerize, and deploy the application to a public HTTPS URL.

---

### Option B: Amazon Web Services (AWS)
You can deploy the app to **AWS App Runner** or **AWS Elastic Beanstalk**.

1.  **Provision AWS RDS (PostgreSQL)**:
    *   Launch an RDS PostgreSQL instance in a security group that allows traffic from your App Runner container.
2.  **Deploy to AWS App Runner**:
    *   Push the built docker image to **AWS ECR (Elastic Container Registry)**.
    *   Create a new **App Runner Service** pointing to the ECR image.
    *   Add your environment variables (`DATABASE_URL`, `GEMINI_API_KEY`) under the App Runner configuration console.
    *   AWS App Runner handles SSL, load balancing, and scaling automatically.

---

### Option C: Microsoft Azure
Azure offers simple container deployment using **Azure Container Apps**.

1.  **Azure Database for PostgreSQL**:
    *   Deploy a flexible server instance of PostgreSQL.
2.  **Azure Container Apps**:
    *   Build the image locally and push to **Azure Container Registry (ACR)**.
    *   Create a Container App pointing to the image.
    *   Configure the ingress to accept public traffic on port `8080` and add environment variables for the DB connection string and Gemini key.
