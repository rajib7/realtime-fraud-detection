package io.fraudops.common;

import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

import java.time.Instant;

/**
 * Wire format for messages on the transactions.raw topic.
 * Keyed on Kafka by userId to preserve per-user ordering (velocity_1h,
 * distinct_countries_24h features depend on this).
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TransactionEvent(
        String txId,
        @NotBlank String userId,
        @NotNull @Positive Double amount,
        String currency,
        @NotBlank String merchant,
        @NotBlank String merchantCategory,
        String country,
        Boolean isForeign,
        Boolean crossBorder,
        Integer hour,
        Double velocity1h,
        Integer distinctCountries24h,
        Instant createdAt
) {
    public TransactionEvent withDefaults(String generatedTxId, Instant now) {
        return new TransactionEvent(
                txId != null ? txId : generatedTxId,
                userId,
                amount,
                currency != null ? currency : "USD",
                merchant,
                merchantCategory,
                country != null ? country : "US",
                isForeign != null ? isForeign : !"US".equals(country != null ? country : "US"),
                crossBorder != null ? crossBorder : !"US".equals(country != null ? country : "US"),
                hour != null ? hour : now.atZone(java.time.ZoneOffset.UTC).getHour(),
                velocity1h != null ? velocity1h : 0.0,
                distinctCountries24h != null ? distinctCountries24h : 1,
                createdAt != null ? createdAt : now
        );
    }
}
