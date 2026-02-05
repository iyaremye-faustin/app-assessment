package dev.chef.crm_backend.producer;

import java.util.List;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Runs all registered {@link ExternalDataProducer} beans on a schedule.
 */
@Component
@ConditionalOnProperty(name = "integration.producers.enabled", havingValue = "true", matchIfMissing = true)
public class ProducerScheduler {

	private static final Logger log = LoggerFactory.getLogger(ProducerScheduler.class);

	private final List<ExternalDataProducer> producers;

	public ProducerScheduler(List<ExternalDataProducer> producers) {
		this.producers = producers;
		log.info("Producer scheduler registered {} producer(s)", producers.size());
	}

	@Scheduled(fixedDelayString = "${integration.producers.poll-interval-ms:10000}")
	public void runProducers() {
		for (ExternalDataProducer producer : producers) {
			try {
				log.debug("Running producer: {}", producer.getSourceName());
				producer.produce();
			} catch (Exception e) {
				log.error("Producer {} failed: {}", producer.getSourceName(), e.getMessage(), e);
			}
		}
	}
}
