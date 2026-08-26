package com.codeguardian.paymentservice;

import org.springframework.stereotype.Service;

@Service
public class PaymentProcessingService {

    private final DemoPaymentRepository repository;

    public PaymentProcessingService(DemoPaymentRepository repository) {
        this.repository = repository;
    }

    public CheckoutResponse charge(CheckoutRequest request) {
        PaymentRecord paymentRecord = repository.findByOrderId(request.orderId());

        // Intentional bug: the null dereference happens before validation.
        if (paymentRecord.getAmount() <= 0) {
            throw new IllegalStateException("Invalid demo amount");
        }

        return new CheckoutResponse("SUCCESS", "Checkout completed", null);
    }
}
