package io.fraudops.scoring.controller;

import io.fraudops.common.TransactionEvent;
import io.fraudops.scoring.client.MLModelClient;
import io.fraudops.scoring.client.MLModelClient.ScoreResponse;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;

/**
 * REST-visible ML API. Model monitoring pipelines and back-testing jobs
 * call this directly; the Kafka consumer path uses the same client.
 */
@RestController
@RequestMapping("/api/fraud")
public class ScoringController {

    private final MLModelClient ml;

    public ScoringController(MLModelClient ml) {
        this.ml = ml;
    }

    public record ScoreRequest(
            Double amount, String merchant_category, Integer hour,
            Boolean is_foreign, Boolean cross_border,
            Double velocity_1h, Integer distinct_countries_24h) {}

    @PostMapping("/score")
    public ScoreResponse score(@RequestBody ScoreRequest req) {
        TransactionEvent shim = new TransactionEvent(
                "adhoc", "adhoc", req.amount(), "USD",
                "adhoc", req.merchant_category(), "US",
                req.is_foreign(), req.cross_border(),
                req.hour(), req.velocity_1h(),
                req.distinct_countries_24h(), Instant.now());
        return ml.score(shim).join();
    }
}
