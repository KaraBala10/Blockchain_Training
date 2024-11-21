# Stage 1: Dependencies Installer
FROM python:3.12.4-slim AS dependencies

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    curl \
    gcc \
    libc-dev \
    && apt-get clean

# Set up working directory for dependencies
WORKDIR /deps

# Copy only requirements.txt to leverage Docker caching
COPY ./project/requirements.txt /deps/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Brownie Builder
FROM python:3.12.4-slim AS brownie-builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    curl \
    gcc \
    libc-dev \
    && apt-get clean

# Install Node.js and ganache-cli
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g ganache-cli

# Set up working directory
WORKDIR /project

# Copy Python dependencies from the dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy the rest of the project files
COPY ./project /project/

# Install Brownie (already installed dependencies will not be duplicated)
RUN pip install eth-brownie==1.20.6

# Verify file structure
RUN ls -R /project

# Set environment variable for Brownie password
ENV BROWNIE_PASSWORD=!@#

# Run the script to create the account
RUN brownie run scripts/create_account.py

# Run the deployment script
RUN brownie run scripts/deploy.py --network development

# Stage 3: Django Application
FROM python:3.12.4-slim

WORKDIR /djangoProject

# Copy Django project files
COPY ./djangoProject /djangoProject/

# Copy Python dependencies from the dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy output from Brownie stage
COPY --from=brownie-builder /project/build/contracts/VirtualCurrency.json /djangoProject/build/contracts/VirtualCurrency.json

# Start Django application
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
