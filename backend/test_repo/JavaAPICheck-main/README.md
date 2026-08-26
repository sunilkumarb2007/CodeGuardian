# JavaAPICheck

`JavaAPICheck` is a small, intentionally broken Java Spring Boot microservice demo repository for exercising the CodeGuardian workflow:

`OBSERVE -> GHOSTTRACE -> FAILURE MEMORY -> AI INVESTIGATION -> PATCH -> GHOST REPLAY -> VALIDATION -> GITHUB PULL REQUEST`

The payment service intentionally contains a deterministic null-object bug so CodeGuardian can reconstruct and repair the failure.

## Architecture

```text
Client
  |
  v
API Gateway :8080
  |
  v
Order Service :8081
  |
  v
Payment Service :8082
  |
  v
In-memory demo repository ("database" layer)
```

## Services

- `gateway`: exposes `POST /checkout` and forwards requests to `order-service`.
- `order-service`: exposes `POST /orders/checkout` and forwards requests to `payment-service`.
- `payment-service`: exposes `POST /payments/charge` and contains the intentional bug.

## Ports

- `8080`: gateway
- `8081`: order-service
- `8082`: payment-service

## Intentional Failure

The root cause is in `payment-service`:

1. The demo repository returns `null` for order `5001`.
2. `PaymentProcessingService` dereferences the returned object before validating it.
3. `payment-service` logs `NULL_OBJECT_ACCESS` and returns HTTP 500.
4. `order-service` logs `DOWNSTREAM_PAYMENT_FAILURE` and returns HTTP 500.
5. `gateway` logs `HTTP_500` and returns HTTP 500 to the client.

This is the buggy baseline by design. Do not fix it on `main`.

## Endpoints

- `gateway`
  - `POST /checkout`
  - `GET /health`
- `order-service`
  - `POST /orders/checkout`
  - `GET /health`
- `payment-service`
  - `POST /payments/charge`
  - `GET /health`

## Run Locally

### Maven Wrapper

```bash
./mvnw clean test
```

### Start Each Service

```bash
./mvnw -pl payment-service spring-boot:run
./mvnw -pl order-service spring-boot:run
./mvnw -pl gateway spring-boot:run
```

### Docker Compose

```bash
docker compose up --build
```

## Reproduce The Failure

```bash
curl -X POST http://localhost:8080/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 101,
    "orderId": 5001,
    "amount": 499.0
  }'
```

### Expected Baseline Response

HTTP `500`

```json
{
  "status": "FAILED",
  "message": "Checkout failed in downstream service",
  "errorCode": "HTTP_500"
}
```

### Successful Demo Request

```bash
curl -X POST http://localhost:8080/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 101,
    "orderId": 5002,
    "amount": 149.0
  }'
```

Expected result: HTTP `200`

## Example Failure Chain

```text
timestamp=2026-08-25T12:00:01.120Z service=api-gateway event_type=request_received request_id=req-abc123 method=POST path=/checkout
timestamp=2026-08-25T12:00:01.150Z service=order-service event_type=request_forwarded request_id=req-abc123 status_code=200 message=Forwarding checkout request to payment-service
timestamp=2026-08-25T12:00:01.180Z service=payment-service event_type=payment_processing request_id=req-abc123 order_id=5001 status_code=200 message=Attempting to resolve demo payment record
timestamp=2026-08-25T12:00:01.181Z service=payment-service event_type=error request_id=req-abc123 status_code=500 error_code=NULL_OBJECT_ACCESS message=Payment request object was null before validation
timestamp=2026-08-25T12:00:01.210Z service=order-service event_type=downstream_failure request_id=req-abc123 status_code=500 error_code=DOWNSTREAM_PAYMENT_FAILURE message=payment-service returned HTTP 500
timestamp=2026-08-25T12:00:01.240Z service=api-gateway event_type=request_failed request_id=req-abc123 status_code=500 error_code=HTTP_500 message=Gateway observed downstream HTTP 500
```

## Request ID Propagation

If the client does not provide `X-Request-ID`, the gateway generates one and forwards it to downstream services. Every log line for the same request uses the same request ID.

## Tests

- `PaymentServiceApplicationTests`: proves the deterministic bug returns HTTP 500 for `orderId=5001` and that a known record like `5002` still succeeds.
- `PaymentPatchRegressionTest`: disabled on purpose. It is the future validation test that should fail before the CodeGuardian patch and pass after the null check is added.

## Intended Repair

The intended repair is small and obvious:

```java
PaymentRecord paymentRecord = repository.findByOrderId(request.orderId());
if (paymentRecord == null) {
    // handle gracefully
}
```

That fix is intentionally not applied in this baseline.

## How CodeGuardian Can Use This Repository

1. Send `POST /checkout` for `orderId=5001`.
2. Observe the gateway HTTP 500.
3. Correlate logs using `request_id`.
4. Trace the root cause to `payment-service`.
5. Generate a patch that adds null validation before dereferencing the record.
6. Re-run the disabled regression test and the active baseline tests.
7. Submit the repair through a feature branch and pull request.
