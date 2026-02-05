package dev.chef.crm_backend.producer;

/**
 */
public interface ExternalDataProducer {

	String getSourceName();

	void produce();
}

