# Systems Integration Specialist - Event-Driven Data Pipeline

Scalable integration pipeline using Java/Spring Boot producers and Python consumers with Kafka message queue.

## Architecture

```
CRM API (Node.js/Fastify)     Inventory API (Node.js/Fastify)
        ↓                              ↓
        └─────── crm-backend (Java/Spring Boot) ────┘
                        ↓
                    Kafka Topics
                (customer_data, inventory_data)
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
    Consumer (Python)            Consumer-Web (Django)
    - Merge data
    - Idempotency                
    - Send to Analytics
```

### Components

1. **CRM API** (`crm-api/`) - Node.js REST API exposing 1000 customers at `/customers`
2. **Inventory API** (`inventory/`) - Node.js/Fastify REST API exposing 10 products at `/products`
3. **CRM Backend** (`crm-backend/`) - Java/Spring Boot producer polling APIs every 360ms, publishing to Kafka
4. **Consumer Service** (`consumer-service/`) - Python/Django consuming from Kafka, merging data, sending to analytics
5. **Kafka + Zookeeper** - Message broker for async communication
6. **Redis** - Idempotency tracking cache

## Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) k6 for load testing

### Run System

```bash
### How to run all the services
- Install docker in your device
- Disable tomcat service if alread installed in your device and uses a default port 
- If running it for the first run the following commands in the order 
- clone the repository 
- change to repository folder to be the current working directory and run the command below 

docker compose down -v
docker system prune -af --volumes
docker compose up  --build

- Open a new tab and in the same directory , go to crm-backend and run
mvn spring-boot:run

- If not running for the first time , go inside the cloned project directory
docker-compose up
- Open a new tab and in the same directory , go to crm-backend and run
mvn spring-boot:run



# View consumer Kafka logs and confirm it is successful
# Checking the process terminal 
<img width="1374" height="600" alt="image" src="https://github.com/user-attachments/assets/1c75c193-e089-490f-9a5b-cdb8d55be07c" />

<img width="1374" height="600" alt="image" src="https://github.com/user-attachments/assets/e4259a73-2b8f-42f1-b605-4355a3ac46d3" />

- You can also check the logs
docker-compose logs -f consumer | grep "\[KAFKA RAW\]"

# Stopping the services 
docker-compose down
```

### Run Load Tests

```bash
# CRM API test
docker-compose --profile testing up k6-crm

# Inventory API test
docker-compose --profile testing up k6-inventory
```

### Run Unit Tests

```bash
# Java tests
cd crm-backend && ./mvnw test
```

## Key Features

### 1. **Reliable Delivery**
- **Retry logic**: Java producers retry failed API calls (4 attempts, exponential backoff)
- **Idempotency**: Python consumers use Redis hash-based deduplication
- **Manual commit**: Kafka offsets committed only after successful processing

### 2. **Scalability**
- **Throughput**: Configured for 10,000+ records/hour (360ms poll interval)
- **Horizontal scaling**: Stateless consumer design supports `docker-compose up --scale consumer=3`
- **Load testing**: k6 tests simulate 100 concurrent users with <500ms p95 latency

### Data Flow**
- Producers fetch from REST APIs → Publish to Kafka topics
- Consumers merge customer + inventory data → Send to Analytics System

## Scalability Strategies

### Current Implementation (10+ systems)
- **Event-driven architecture**: Kafka decouples producers/consumers
- **Async processing**: Non-blocking message consumption
- **Idempotency**: Hash-based duplicate detection in Redis

## Integration Concept

### Java → Python via Kafka

**Why Kafka?**
- Language-agnostic protocol (Java producers, Python consumers coexist)
- Decoupled systems (producers/consumers evolve independently)
- Buffering & replay (Kafka retains messages, consumers catch up at own pace)

**Data Flow:**
1. Spring Boot `@Scheduled` jobs poll REST APIs every 360ms
2. RestTemplate fetches JSON, serializes to Kafka topics
3. Python Confluent Kafka consumer polls topics asynchronously
4. Django processes messages, merges data, calls Analytics REST API

**Async Processing:**
- Java: `@Retryable` handles transient API failures
- Idempotency: SHA256 hash of message content stored in Redis (TTL 24h)

## Configuration

### Environment Variables

**crm-backend** (`application.properties`):
```properties
integration.crm.base-url=http://crm-api:8081
integration.inventory.base-url=http://inventory:8082
integration.kafka.bootstrap-servers=kafka:29092
integration.producers.poll-interval-ms=360
```

**consumer-service** (environment):
```
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
REDIS_HOST=redis
```

### Ports
- CRM API: `8081`
- Inventory API: `8082`
- Consumer Web: `8000`
- Kafka: `9092` (host), `29092` (container)
- Zookeeper: `2181`

## Testing

### Manual Validation
```bash
# Check Kafka message flow
docker-compose logs -f consumer | grep "\[KAFKA RAW\]"

# Verify 10k records/hour (should see ~3 messages/second)
docker-compose logs consumer | grep "INFO.*Published" | wc -l
```

### Load Testing Results
- **Throughput**: 10,000+ records/hour achieved
- **Latency**: p95 < 500ms for all API endpoints
- **Error rate**: < 1% under 100 concurrent users

**Load tests flooding logs:**
```bash
docker-compose stop k6-crm k6-inventory
```
