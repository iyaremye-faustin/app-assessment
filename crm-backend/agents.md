Your company manages an e-commerce platform with three systems:

1.​ CRM System: Exposes customer data via REST and SOAP API (/customers)
2.​ Inventory System: Exposes product stock via REST API (/products)
3.​ Analytics System: Accepts data via REST POST (/analytics/data) or CSV upload



Task 1: Java Producers
●​ Implement Java/Spring Boot producers to fetch data from CRM and Inventory.
●​ Publish data to Kafka topics or RabbitMQ queues: customer_data and
inventory_data.
●​ Include retry logic for failed API calls.
●​
Modularize code to allow adding more producer sources easily.

Goal: Build a scalable integration pipeline that:
●​ Uses Java/Spring Boot producers to fetch data from CRM and Inventory.
●​ Publishes the data to a message queue (Kafka or RabbitMQ).
