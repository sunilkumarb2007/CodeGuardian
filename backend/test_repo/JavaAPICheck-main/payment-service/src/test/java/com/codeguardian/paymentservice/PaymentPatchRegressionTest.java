package com.codeguardian.paymentservice;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

@Disabled("Enable after CodeGuardian adds the null check patch.")
@SpringBootTest
class PaymentPatchRegressionTest {

    @Autowired
    private PaymentProcessingService paymentProcessingService;

    @Test
    void knownBugOrderShouldReturnSuccessAfterPatch() {
        CheckoutResponse response = paymentProcessingService.charge(new CheckoutRequest(101L, 5001L, 499.0));
        assertThat(response.status()).isEqualTo("SUCCESS");
    }
}
