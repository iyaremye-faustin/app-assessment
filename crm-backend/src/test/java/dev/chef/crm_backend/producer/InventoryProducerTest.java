package dev.chef.crm_backend.producer;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;

import dev.chef.crm_backend.dto.InventoryItem;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

public class InventoryProducerTest {

	@Mock
	private RestTemplate restTemplate;

	@Mock
	private KafkaTemplate<String, Object> kafkaTemplate;

	private InventoryProducer producer;

	@BeforeEach
	void setUp() {
		MockitoAnnotations.openMocks(this);
		producer = new InventoryProducer(restTemplate, kafkaTemplate);
		ReflectionTestUtils.setField(producer, "inventoryBaseUrl", "http://localhost:8082");
		ReflectionTestUtils.setField(producer, "topic", "inventory_data");
	}

	@Test
	void produce_sendsMessagesForEachInventoryItem() {
		List<InventoryItem> items = List.of(
				new InventoryItem("1", "Product 1", 10),
				new InventoryItem("2", "Product 2", 20)
		);

		when(restTemplate.exchange(
				anyString(),
				eq(HttpMethod.GET),
				eq(null),
				any(org.springframework.core.ParameterizedTypeReference.class)
		)).thenReturn(ResponseEntity.ok(items));

		producer.produce();

		verify(kafkaTemplate, times(2)).send(eq("inventory_data"), anyString(), any());
	}

	@Test
	void produce_doesNothingWhenNoInventoryItems() {
		when(restTemplate.exchange(
				anyString(),
				eq(HttpMethod.GET),
				eq(null),
				any(org.springframework.core.ParameterizedTypeReference.class)
		)).thenReturn(ResponseEntity.ok(List.of()));

		producer.produce();

		verify(kafkaTemplate, times(0)).send(anyString(), anyString(), any());
	}
}

