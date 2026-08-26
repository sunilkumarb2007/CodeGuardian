package com.codeguardian.gateway;

import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.LinkedHashMap;
import java.util.Map;

@Component
public class StructuredLogWriter {

    void log(String service, String eventType, String requestId, Map<String, Object> fields) {
        Map<String, Object> values = new LinkedHashMap<>();
        values.put("timestamp", Instant.now().truncatedTo(ChronoUnit.MILLIS));
        values.put("service", service);
        values.put("event_type", eventType);
        values.put("request_id", requestId);
        values.putAll(fields);

        StringBuilder line = new StringBuilder();
        values.forEach((key, value) -> {
            if (line.length() > 0) {
                line.append(' ');
            }
            line.append(key).append('=').append(value);
        });
        System.out.println(line);
    }
}
