#!/bin/bash
# CI Pipeline Script

set -e

echo "Running Java tests with coverage..."
cd crm-backend
./mvnw test jacoco:report
echo "Java test coverage report generated at crm-backend/target/site/jacoco/index.html"
cd ..

echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Waiting for services..."
sleep 30

echo "Checking consumer logs for Kafka messages..."
docker-compose logs consumer | grep "\[KAFKA RAW\]" | head -10

echo "CI pipeline completed."
