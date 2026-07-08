package io.fraudops.scoring.client;

import io.fraudops.common.RiskLevel;
import io.fraudops.common.TransactionEvent;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * Client for the external Python ML API.
 *
 * Wrapped in a Resilience4j circuit breaker + time limiter. When the ML
 * service exceeds its p99 latency SLO (or errors), the fallback returns
 * a rule-only score so the pipeline never freezes.
 */
@Component
public class MLModelClient {

    private static final Logger log = LoggerFactory.getLogger(MLModelClient.class);

    private final WebClient client;

    public MLModelClient(WebClient.Builder builder,
                         @Value("${fraudops.ml.base-url:http://ml-model-service:8000}") String baseUrl) {
        this.client = builder.baseUrl(baseUrl).build();
    }

    public record ScoreResponse(
            Double mlScore, Double ruleScore, Double fraudScore,
            RiskLevel riskLevel, String decision,
            List<String> reasons,
            Double scoringLatencyMs, String modelVersion
    ) {}

    @CircuitBreaker(name = "ml-model", fallbackMethod = "fallbackScore")
    @TimeLimiter(name = "ml-model")
    public CompletableFuture<ScoreResponse> score(TransactionEvent tx) {
        return client.post()
                .uri("/score")
                .bodyValue(Map.of(
                        "amount", tx.amount(),
                        "merchant_category", tx.merchantCategory(),
                        "hour", tx.hour(),
                        "is_foreign", tx.isForeign() != null && tx.isForeign(),
                        "cross_border", tx.crossBorder() != null && tx.crossBorder(),
                        "velocity_1h", tx.velocity1h() != null ? tx.velocity1h() : 0.0,
                        "distinct_countries_24h", tx.distinctCountries24h() != null ? tx.distinctCountries24h() : 1
                ))
                .retrieve()
                .bodyToMono(Map.class)
                .map(this::toResponse)
                .timeout(Duration.ofMillis(500))
                .toFuture();
    }

    @SuppressWarnings("unused")
    private CompletableFuture<ScoreResponse> fallbackScore(TransactionEvent tx, Throwable ex) {
        log.warn("ML API unavailable ({}), falling back to rule-only score for tx {}",
                ex.getClass().getSimpleName(), tx.txId());
        double rule = RuleEngine.score(tx);
        List<String> reasons = RuleEngine.reasons(tx);
        RiskLevel level = rule >= 0.75 ? RiskLevel.FRAUD : rule >= 0.5 ? RiskLevel.SUSPICIOUS : RiskLevel.SAFE;
        return CompletableFuture.completedFuture(
                new ScoreResponse(0.0, rule, rule, level, level.decision(),
                        reasons, 0.0, "rule-engine-fallback"));
    }

    @SuppressWarnings("unchecked")
    private ScoreResponse toResponse(Map<String, Object> raw) {
        String risk = (String) raw.getOrDefault("risk_level", "safe");
        return new ScoreResponse(
                ((Number) raw.get("ml_score")).doubleValue(),
                ((Number) raw.get("rule_score")).doubleValue(),
                ((Number) raw.get("fraud_score")).doubleValue(),
                RiskLevel.valueOf(risk.toUpperCase()),
                (String) raw.get("decision"),
                (List<String>) raw.get("reasons"),
                ((Number) raw.get("scoring_latency_ms")).doubleValue(),
                (String) raw.get("model_version")
        );
    }
}
