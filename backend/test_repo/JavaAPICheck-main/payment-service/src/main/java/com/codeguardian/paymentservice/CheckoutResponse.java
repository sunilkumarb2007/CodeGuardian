package com.codeguardian.paymentservice;

public record CheckoutResponse(String status, String message, String errorCode) {
}
