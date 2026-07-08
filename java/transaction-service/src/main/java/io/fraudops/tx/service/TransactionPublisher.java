package io.fraudops.tx.service;

import io.fraudops.common.TransactionEvent;
import io.fraudops.common.Topics;
import io.fraudops.tx.repo.TransactionDoc;
import io.fraudops.tx.repo.TransactionRepository;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.PageRequest;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

/**
 * Persists each transaction to Mongo and publishes it to transactions.raw.
 * Mongo write happens BEFORE the publish so that if persistence fails, no
 * downstream service ever sees a scoring request for a transaction that
 * isn't in the system of record.
 */
@Service
public class TransactionPublisher {

    private static final Logger log = LoggerFactory.getLogger(TransactionPublisher.class);

    private final KafkaTemplate<String, TransactionEvent> kafka;
    private final TransactionRepository repo;
    private final MeterRegistry meter;

    public TransactionPublisher(KafkaTemplate<String, TransactionEvent> kafka,
                                TransactionRepository repo,
                                MeterRegistry meter) {
        this.kafka = kafka;
        this.repo = repo;
        this.meter = meter;
    }

    public TransactionEvent ingest(TransactionEvent input) {
        TransactionEvent tx = input.withDefaults("tx_" + UUID.randomUUID().toString().replace("-", "").substring(0, 12),
                                                  Instant.now());
        // 1. durability first
        repo.save(new TransactionDoc(
                tx.txId(), tx.userId(), tx.amount(), tx.currency(),
                tx.merchant(), tx.merchantCategory(), tx.country(),
                tx.isForeign(), tx.crossBorder(), tx.hour(),
                tx.velocity1h(), tx.distinctCountries24h(), tx.createdAt()));

        // 2. publish keyed by userId — preserves per-user ordering across
        // partitions, which is required for velocity + country-hopping features.
        kafka.send(Topics.TRANSACTIONS_RAW, tx.userId(), tx);

        meter.counter("fraudops.tx.published").increment();
        log.debug("published tx {} user {} amount {}", tx.txId(), tx.userId(), tx.amount());
        return tx;
    }

    public List<TransactionDoc> recent(int limit) {
        return repo.findRecent(PageRequest.of(0, Math.min(Math.max(limit, 1), 200)));
    }
}
