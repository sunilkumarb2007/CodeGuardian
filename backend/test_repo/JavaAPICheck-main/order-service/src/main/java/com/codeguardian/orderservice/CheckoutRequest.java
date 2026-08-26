package com.codeguardian.orderservice;

public record CheckoutRequest(Long userId, Long orderId, Double amount) {
}
