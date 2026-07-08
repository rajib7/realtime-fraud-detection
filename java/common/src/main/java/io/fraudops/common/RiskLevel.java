package io.fraudops.common;

public enum RiskLevel {
    SAFE, SUSPICIOUS, FRAUD;

    public String decision() {
        return switch (this) {
            case SAFE -> "approve";
            case SUSPICIOUS -> "review";
            case FRAUD -> "block";
        };
    }
}
