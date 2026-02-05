package dev.chef.crm_backend.producer;

import java.util.Collections;
import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Recover;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import dev.chef.crm_backend.dto.InventoryItem;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class InventoryProducer implements ExternalDataProducer {

	private static final Logger log = LoggerFactory.getLogger(InventoryProducer.class);
	private static final ParameterizedTypeReference<List<InventoryItem>> INVENTORY_LIST_TYPE =
			new ParameterizedTypeReference<>() {};

	private final RestTemplate restTemplate;
	private final KafkaTemplate<String, Object> kafkaTemplate;

	@Value("${integration.inventory.base-url}")
	private String inventoryBaseUrl;

	@Value("${integration.kafka.topics.inventory-data:inventory_data}")
	private String topic;

	public InventoryProducer(RestTemplate restTemplate, KafkaTemplate<String, Object> kafkaTemplate) {
		this.restTemplate = restTemplate;
		this.kafkaTemplate = kafkaTemplate;
	}

	@Override
	public String getSourceName() {
		return "Inventory (products)";
	}

	@Override
	public void produce() {
		List<InventoryItem> items = fetchProducts();
		if (items == null || items.isEmpty()) {
			log.debug("No inventory items to publish");
			return;
		}
		for (InventoryItem item : items) {
			String key = item.id() != null ? item.id() : java.util.UUID.randomUUID().toString();
			kafkaTemplate.send(topic, key, item);
		}
		log.info("Published {} inventory item(s) to topic {}", items.size(), topic);
	}

	@Retryable(
			retryFor = { Exception.class },
			maxAttempts = 4,
			backoff = @Backoff(delay = 1000, multiplier = 2)
	)
	public List<InventoryItem> fetchProducts() {
		String url = inventoryBaseUrl + "/products";
		log.debug("Fetching products from {}", url);
		List<InventoryItem> body = restTemplate.exchange(url, org.springframework.http.HttpMethod.GET, null, INVENTORY_LIST_TYPE).getBody();
		return body != null ? body : Collections.emptyList();
	}

	@Recover
	public List<InventoryItem> fetchProductsRecover(Exception e) {
		log.error("Failed to fetch products from Inventory after retries: {}", e.getMessage());
		return Collections.emptyList();
	}
}
