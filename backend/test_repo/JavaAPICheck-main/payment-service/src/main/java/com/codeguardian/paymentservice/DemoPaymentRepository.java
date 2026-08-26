package com.codeguardian.paymentservice;

import org.springframework.stereotype.Repository;

import java.util.Map;

@Repository
public class DemoPaymentRepository {

    private final Map<Long, PaymentRecord> records = Map.of(
            5002L, new PaymentRecord(5002L, 149.0),
            5003L, new PaymentRecord(5003L, 299.0)
    );

    public PaymentRecord findByOrderId(Long orderId) {
        return records.get(orderId);
    }
}
