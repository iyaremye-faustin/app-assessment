package dev.chef.crm_backend.dto;

import java.util.Map;

/**
 * DTO for product/stock data from the Inventory REST API (/products).
 */
public record InventoryItem(
		String id,
		String name,
		Integer stock,
		Map<String, Object> additional
) {
	public InventoryItem(String id, String name, Integer stock) {
		this(id, name, stock, null);
	}
}
