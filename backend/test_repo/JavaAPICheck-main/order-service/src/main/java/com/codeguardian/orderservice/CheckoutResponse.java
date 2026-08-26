package com.codeguardian.orderservice;

public record CheckoutResponse(String status, String message, String errorCode) {
}
