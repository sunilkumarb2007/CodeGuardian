package com.codeguardian.orderservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
public class OrderCheckoutController {

    private final RestTemplate restTemplate;
    private final StructuredLogWriter logWriter;
    private final String paymentServiceUrl;

    public OrderCheckoutController(RestTemplate restTemplate,
                                   StructuredLogWriter logWriter,
                                   @Value("${services.payment.base-url}") String paymentServiceUrl) {
        this.restTemplate = restTemplate;
        this.logWriter = logWriter;
        this.paymentServiceUrl = paymentServiceUrl;
    }

    @PostMapping("/orders/checkout")
    public ResponseEntity<CheckoutResponse> checkout(@RequestBody CheckoutRequest request,
                                                     @RequestHeader("X-Request-ID") String requestId) {
        logWriter.log("order-service", "request_forwarded", requestId, Map.of(
                "status_code", 200,
                "message", "Forwarding checkout request to payment-service"
        ));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Request-ID", requestId);

        try {
            ResponseEntity<CheckoutResponse> response = restTemplate.postForEntity(
                    paymentServiceUrl + "/payments/charge",
                    new HttpEntity<>(request, headers),
                    CheckoutResponse.class
            );

            logWriter.log("order-service", "checkout_completed", requestId, Map.of(
                    "status_code", response.getStatusCode().value(),
                    "message", "Payment completed"
            ));

            return response;
        } catch (HttpStatusCodeException ex) {
            logWriter.log("order-service", "downstream_failure", requestId, Map.of(
                    "status_code", HttpStatus.INTERNAL_SERVER_ERROR.value(),
                    "error_code", "DOWNSTREAM_PAYMENT_FAILURE",
                    "message", "payment-service returned HTTP 500"
            ));

            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new CheckoutResponse("FAILED", "Payment service failed", "DOWNSTREAM_PAYMENT_FAILURE"));
        }
    }
}
