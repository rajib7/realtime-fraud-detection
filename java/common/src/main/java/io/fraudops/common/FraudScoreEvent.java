package io.fraudops.common;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.time.Instant;
import java.util.List;

/** Wire format for messages on the fraud.scores topic. */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record FraudScoreEvent(
        String txId,
        String userId,
        Double amount,
        String merchantCategory,
        String country,
        Double mlScore,
        Double ruleScore,
        Double fraudScore,
        RiskLevel riskLevel,
        String decision,
        List<String> reasons,
        Double scoringLatencyMs,
        String modelVersion,
        Instant scoredAt
) {}
