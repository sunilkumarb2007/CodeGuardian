package com.codeguardian.paymentservice;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class PaymentController {

    private final PaymentProcessingService paymentProcessingService;
    private final StructuredLogWriter logWriter;

    public PaymentController(PaymentProcessingService paymentProcessingService, StructuredLogWriter logWriter) {
        this.paymentProcessingService = paymentProcessingService;
        this.logWriter = logWriter;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP", "service", "payment-service");
    }

    @PostMapping("/payments/charge")
    public ResponseEntity<CheckoutResponse> charge(@RequestBody CheckoutRequest request,
                                                   @RequestHeader("X-Request-ID") String requestId) {
        logWriter.log("payment-service", "payment_processing", requestId, Map.of(
                "order_id", request.orderId(),
                "status_code", 200,
                "message", "Attempting to resolve demo payment record"
        ));

        CheckoutResponse response = paymentProcessingService.charge(request);
        logWriter.log("payment-service", "payment_completed", requestId, Map.of(
                "status_code", 200,
                "message", "Payment processed"
        ));
        return ResponseEntity.ok(response);
    }

    @ExceptionHandler(NullPointerException.class)
    public ResponseEntity<CheckoutResponse> handleNullPointer(NullPointerException exception,
                                                              HttpServletRequest request) {
        String requestId = request.getHeader("X-Request-ID");
        String effectiveRequestId = requestId == null ? "missing-request-id" : requestId;
        logWriter.log("payment-service", "error", effectiveRequestId, Map.of(
                "status_code", HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "error_code", "NULL_OBJECT_ACCESS",
                "message", "Payment request object was null before validation"
        ));

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new CheckoutResponse("FAILED", "Null object accessed before validation", "NULL_OBJECT_ACCESS"));
    }
}
