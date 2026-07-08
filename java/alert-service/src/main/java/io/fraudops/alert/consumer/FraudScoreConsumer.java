package io.fraudops.alert.consumer;

import io.fraudops.alert.repo.AlertDoc;
import io.fraudops.alert.repo.AlertRepository;
import io.fraudops.common.AlertEvent;
import io.fraudops.common.FraudScoreEvent;
import io.fraudops.common.RiskLevel;
import io.fraudops.common.Topics;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.UUID;

/**
 * Consumes fraud.scores. Raises an alert on any FRAUD-level event and
 * publishes it to alerts.raised. Suspicious/safe events are dropped.
 */
@Component
public class FraudScoreConsumer {

    private static final Logger log = LoggerFactory.getLogger(FraudScoreConsumer.class);

    private final AlertRepository repo;
    private final KafkaTemplate<String, AlertEvent> producer;
    private final MeterRegistry meter;

    public FraudScoreConsumer(AlertRepository repo,
                              KafkaTemplate<String, AlertEvent> producer,
                              MeterRegistry meter) {
        this.repo = repo;
        this.producer = producer;
        this.meter = meter;
    }

    @KafkaListener(topics = Topics.FRAUD_SCORES, containerFactory = "kafkaListenerContainerFactory")
    public void onScore(FraudScoreEvent evt) {
        if (evt.riskLevel() != RiskLevel.FRAUD) return;

        String severity = evt.fraudScore() >= 0.9 ? "critical"
                : evt.fraudScore() >= 0.75 ? "high" : "medium";

        AlertEvent alert = new AlertEvent(
                "al_" + UUID.randomUUID().toString().replace("-", "").substring(0, 12),
                evt.txId(), evt.userId(), evt.amount(),
                evt.merchantCategory(), evt.country(),
                evt.fraudScore(), severity, evt.reasons(),
                evt.decision(), Instant.now(), false);

        repo.save(new AlertDoc(alert.alertId(), alert.txId(), alert.userId(),
                alert.amount(), alert.merchantCategory(), alert.country(),
                alert.fraudScore(), alert.severity(), alert.reasons(),
                alert.decision(), alert.raisedAt(), false));

        producer.send(Topics.ALERTS_RAISED, alert.userId(), alert);

        meter.counter("fraudops.alerts.raised", "severity", severity).increment();
        log.info("alert {} raised on tx {} severity={} score={}",
                alert.alertId(), alert.txId(), severity, alert.fraudScore());
    }
}
