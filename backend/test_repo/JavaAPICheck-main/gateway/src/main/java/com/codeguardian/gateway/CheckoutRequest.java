package com.codeguardian.gateway;

public record CheckoutRequest(Long userId, Long orderId, Double amount) {
}
