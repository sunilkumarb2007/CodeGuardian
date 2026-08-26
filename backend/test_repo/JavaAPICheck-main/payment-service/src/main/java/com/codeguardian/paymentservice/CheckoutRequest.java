package com.codeguardian.paymentservice;

public record CheckoutRequest(Long userId, Long orderId, Double amount) {
}
