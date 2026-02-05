package dev.chef.crm_backend.producer;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;

import dev.chef.crm_backend.dto.CustomerData;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

public class CrmCustomerProducerTest {

	@Mock
	private RestTemplate restTemplate;

	@Mock
	private KafkaTemplate<String, Object> kafkaTemplate;

	private CrmCustomerProducer producer;

	@BeforeEach
	void setUp() {
		MockitoAnnotations.openMocks(this);
		producer = new CrmCustomerProducer(restTemplate, kafkaTemplate);
		ReflectionTestUtils.setField(producer, "crmBaseUrl", "http://localhost:8081");
		ReflectionTestUtils.setField(producer, "topic", "customer_data");
	}

	@Test
	void produce_sendsMessagesForEachCustomer() {
		// Arrange
		List<CustomerData> customers = List.of(
				new CustomerData("1", "Customer 1", "c1@example.com"),
				new CustomerData("2", "Customer 2", "c2@example.com")
		);

		when(restTemplate.exchange(
				anyString(),
				eq(HttpMethod.GET),
				eq(null),
				any(org.springframework.core.ParameterizedTypeReference.class)
		)).thenReturn(ResponseEntity.ok(customers));

		// Act
		producer.produce();

		// Assert
		verify(kafkaTemplate, times(2)).send(eq("customer_data"), anyString(), any());
	}

	@Test
	void produce_doesNothingWhenNoCustomers() {
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

