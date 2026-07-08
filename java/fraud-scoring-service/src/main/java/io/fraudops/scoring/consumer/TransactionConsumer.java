package io.fraudops.scoring.consumer;

import io.fraudops.common.FraudScoreEvent;
import io.fraudops.common.RiskLevel;
import io.fraudops.common.Topics;
import io.fraudops.common.TransactionEvent;
import io.fraudops.scoring.client.MLModelClient;
import io.fraudops.scoring.client.MLModelClient.ScoreResponse;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.time.Instant;

/**
 * Consumer for transactions.raw.
 *
 * For each incoming transaction:
 *   1. Call the ML model API (with circuit breaker fallback).
 *   2. Persist the produced score event to Mongo.
 *   3. Publish to fraud.scores keyed on userId.
 */
@Component
public class TransactionConsumer {

    private static final Logger log = LoggerFactory.getLogger(TransactionConsumer.class);

    private final MLModelClient ml;
    private final KafkaTemplate<String, FraudScoreEvent> producer;
    private final MongoTemplate mongo;
    private final MeterRegistry meter;

    public TransactionConsumer(MLModelClient ml,
                               KafkaTemplate<String, FraudScoreEvent> producer,
                               MongoTemplate mongo,
                               MeterRegistry meter) {
        this.ml = ml;
        this.producer = producer;
        this.mongo = mongo;
        this.meter = meter;
    }

    @KafkaListener(topics = Topics.TRANSACTIONS_RAW, containerFactory = "kafkaListenerContainerFactory")
    public void onTransaction(TransactionEvent tx) {
        try {
            ScoreResponse s = ml.score(tx).join();
            FraudScoreEvent evt = new FraudScoreEvent(
                    tx.txId(), tx.userId(), tx.amount(), tx.merchantCategory(),
                    tx.country(), s.mlScore(), s.ruleScore(), s.fraudScore(),
                    s.riskLevel(), s.decision(), s.reasons(),
                    s.scoringLatencyMs(), s.modelVersion(), Instant.now());
            mongo.getCollection("fraud_scores").insertOne(
                    org.bson.Document.parse(toJson(evt)));
            producer.send(Topics.FRAUD_SCORES, tx.userId(), evt);

            meter.counter("fraudops.scoring.processed",
                    "risk", s.riskLevel().name().toLowerCase()).increment();
            meter.timer("fraudops.scoring.latency").record(
                    java.time.Duration.ofNanos((long) (s.scoringLatencyMs() * 1_000_000)));
        } catch (Exception e) {
            log.error("failed to score tx {}: {}", tx.txId(), e.toString());
            throw e; // let the Kafka error handler apply DLQ policy
        }
    }

    private static String toJson(Object o) {
        try {
            return new com.fasterxml.jackson.databind.ObjectMapper()
                    .findAndRegisterModules().writeValueAsString(o);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
