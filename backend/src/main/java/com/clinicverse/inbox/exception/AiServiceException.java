package com.clinicverse.inbox.exception;

public class AiServiceException extends RuntimeException {
    private final int statusCode;

    public AiServiceException(String message, int statusCode) {
        super(message);
        this.statusCode = statusCode;
    }

    public AiServiceException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 500;
    }

    public int getStatusCode() { return statusCode; }
}
