package io.fraudops.common;

/** Kafka topic name registry. Keep in sync across producers and consumers. */
public final class Topics {
    private Topics() {}
    public static final String TRANSACTIONS_RAW = "transactions.raw";
    public static final String FRAUD_SCORES = "fraud.scores";
    public static final String ALERTS_RAISED = "alerts.raised";
}
