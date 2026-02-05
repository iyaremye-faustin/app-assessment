package dev.chef.crm_backend.dto;

import java.util.Map;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/**
 * DTO for customer data from the CRM REST/AP API (/customers).
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record CustomerData(
		String id,
		String name,
		String email,
		Map<String, Object> additional
) {
	public CustomerData(String id, String name, String email) {
		this(id, name, email, null);
	}
}
