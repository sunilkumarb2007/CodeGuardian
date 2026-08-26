package com.codeguardian.orderservice;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

@Configuration
public class OrderServiceConfig {

    @Bean
    RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
