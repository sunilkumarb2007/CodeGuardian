package com.codeguardian.gateway;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
public class CheckoutController {

    private final RestTemplate restTemplate;
    private final StructuredLogWriter logWriter;
    private final String orderServiceUrl;

    public CheckoutController(RestTemplate restTemplate,
                              StructuredLogWriter logWriter,
                              @Value("${services.order.base-url}") String orderServiceUrl) {
        this.restTemplate = restTemplate;
        this.logWriter = logWriter;
        this.orderServiceUrl = orderServiceUrl;
    }

    @PostMapping("/checkout")
    public ResponseEntity<CheckoutResponse> checkout(@RequestBody CheckoutRequest request,
                                                     HttpServletRequest httpServletRequest) {
        String requestId = (String) httpServletRequest.getAttribute(RequestIdFilter.REQUEST_ID_HEADER);

        logWriter.log("api-gateway", "request_received", requestId, Map.of(
                "method", "POST",
                "path", "/checkout"
        ));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set(RequestIdFilter.REQUEST_ID_HEADER, requestId);

        try {
            ResponseEntity<CheckoutResponse> response = restTemplate.postForEntity(
                    orderServiceUrl + "/orders/checkout",
                    new HttpEntity<>(request, headers),
                    CheckoutResponse.class
            );

            logWriter.log("api-gateway", "request_succeeded", requestId, Map.of(
                    "status_code", response.getStatusCode().value(),
                    "message", "Checkout completed"
            ));

            return response;
        } catch (HttpStatusCodeException ex) {
            logWriter.log("api-gateway", "request_failed", requestId, Map.of(
                    "status_code", HttpStatus.INTERNAL_SERVER_ERROR.value(),
                    "error_code", "HTTP_500",
                    "message", "Gateway observed downstream HTTP 500"
            ));

            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new CheckoutResponse("FAILED", "Checkout failed in downstream service", "HTTP_500"));
        }
    }
}
