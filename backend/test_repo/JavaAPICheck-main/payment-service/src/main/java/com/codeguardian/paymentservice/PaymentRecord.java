package com.codeguardian.paymentservice;

public class PaymentRecord {

    private final Long orderId;
    private final Double amount;

    public PaymentRecord(Long orderId, Double amount) {
        this.orderId = orderId;
        this.amount = amount;
    }

    public Long getOrderId() {
        return orderId;
    }

    public Double getAmount() {
        return amount;
    }
}
