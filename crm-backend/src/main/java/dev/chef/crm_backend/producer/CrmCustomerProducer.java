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

import dev.chef.crm_backend.dto.CustomerData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class CrmCustomerProducer implements ExternalDataProducer {

	private static final Logger log = LoggerFactory.getLogger(CrmCustomerProducer.class);
	private static final ParameterizedTypeReference<List<CustomerData>> CUSTOMER_LIST_TYPE =
			new ParameterizedTypeReference<>() {};

	private final RestTemplate restTemplate;
	private final KafkaTemplate<String, Object> kafkaTemplate;

	@Value("${integration.crm.base-url}")
	private String crmBaseUrl;

	@Value("${integration.kafka.topics.customer-data:customer_data}")
	private String topic;

	public CrmCustomerProducer(RestTemplate restTemplate, KafkaTemplate<String, Object> kafkaTemplate) {
		this.restTemplate = restTemplate;
		this.kafkaTemplate = kafkaTemplate;
	}

	@Override
	public String getSourceName() {
		return "CRM (customers)";
	}

	@Override
	public void produce() {
		List<CustomerData> customers = fetchCustomers();
		if (customers == null || customers.isEmpty()) {
			log.debug("No customers to publish from CRM");
			return;
		}
		for (CustomerData c : customers) {
			String key = c.id() != null ? c.id() : java.util.UUID.randomUUID().toString();
			kafkaTemplate.send(topic, key, c);
		}
		log.info("Published {} customer(s) to topic {}", customers.size(), topic);
	}

	@Retryable(
			retryFor = { Exception.class },
			maxAttempts = 4,
			backoff = @Backoff(delay = 1000, multiplier = 2)
	)
	public List<CustomerData> fetchCustomers() {
		String url = crmBaseUrl + "/customers";
		log.debug("Fetching customers from {}", url);
		List<CustomerData> body = restTemplate.exchange(url, org.springframework.http.HttpMethod.GET, null, CUSTOMER_LIST_TYPE).getBody();
		return body != null ? body : Collections.emptyList();
	}

	@Recover
	public List<CustomerData> fetchCustomersRecover(Exception e) {
		log.error("Failed to fetch customers from CRM after retries: {}", e.getMessage());
		return Collections.emptyList();
	}
}
