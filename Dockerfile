# Stage 1: Brownie Builder
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

# Copy only requirements.txt to leverage Docker caching
COPY ./project/requirements.txt /project/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install eth-brownie

# Copy the rest of the project files
COPY ./project /project/

# Verify file structure
RUN ls -R /project

# Set environment variable for Brownie password
ENV BROWNIE_PASSWORD=!@#

# Run the script to create the account
RUN brownie run scripts/create_account.py

# Run the deployment script
RUN brownie run scripts/deploy.py --network development


# Stage 2: Django Application
FROM python:3.12.4-slim

WORKDIR /djangoProject

# Copy Django project files
COPY ./djangoProject /djangoProject/

# Copy output from Brownie stage
COPY --from=brownie-builder /project/build/contracts/VirtualCurrency.json /djangoProject/build/contracts/VirtualCurrency.json

# Install Django dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start Django application
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
