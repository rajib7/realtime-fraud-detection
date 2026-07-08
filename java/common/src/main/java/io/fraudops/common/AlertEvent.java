package io.fraudops.common;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.time.Instant;
import java.util.List;

/** Wire format for messages on the alerts.raised topic. */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AlertEvent(
        String alertId,
        String txId,
        String userId,
        Double amount,
        String merchantCategory,
        String country,
        Double fraudScore,
        String severity,          // "medium" | "high" | "critical"
        List<String> reasons,
        String decision,
        Instant raisedAt,
        Boolean acknowledged
) {}
