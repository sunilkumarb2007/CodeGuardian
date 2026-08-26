package com.codeguardian.gateway;

public record CheckoutResponse(String status, String message, String errorCode) {
}
