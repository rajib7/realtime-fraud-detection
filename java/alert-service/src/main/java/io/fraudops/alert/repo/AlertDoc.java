package io.fraudops.alert.repo;

import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.List;

@Document(collection = "alerts")
public record AlertDoc(
        String alertId,
        String txId,
        String userId,
        Double amount,
        String merchantCategory,
        String country,
        Double fraudScore,
        String severity,
        List<String> reasons,
        String decision,
        Instant raisedAt,
        Boolean acknowledged
) {}
