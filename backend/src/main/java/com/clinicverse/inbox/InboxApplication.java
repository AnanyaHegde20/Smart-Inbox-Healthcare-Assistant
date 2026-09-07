package com.clinicverse.inbox;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class InboxApplication {
    public static void main(String[] args) {
        SpringApplication.run(InboxApplication.class, args);
    }
}
