package com.codeguardian.paymentservice;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class PaymentServiceApplicationTests {

    private final MockMvc mockMvc = MockMvcBuilders
            .standaloneSetup(new PaymentController(
                    new PaymentProcessingService(new DemoPaymentRepository()),
                    new StructuredLogWriter()
            ))
            .build();

    @Test
    void deterministicBugReturnsInternalServerError() throws Exception {
        mockMvc.perform(post("/payments/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .header("X-Request-ID", "req-test-bug")
                        .content("""
                                {"userId":101,"orderId":5001,"amount":499.0}
                                """))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.errorCode").value("NULL_OBJECT_ACCESS"));
    }

    @Test
    void knownPaymentRecordCompletesSuccessfully() throws Exception {
        mockMvc.perform(post("/payments/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .header("X-Request-ID", "req-test-success")
                        .content("""
                                {"userId":101,"orderId":5002,"amount":149.0}
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SUCCESS"));
    }
}
