package io.fraudops.tx.repo;

import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Document(collection = "transactions")
public record TransactionDoc(
        String txId,
        String userId,
        Double amount,
        String currency,
        String merchant,
        String merchantCategory,
        String country,
        Boolean isForeign,
        Boolean crossBorder,
        Integer hour,
        Double velocity1h,
        Integer distinctCountries24h,
        Instant createdAt
) {}
