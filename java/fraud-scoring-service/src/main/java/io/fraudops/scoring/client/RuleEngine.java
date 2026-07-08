package io.fraudops.scoring.client;

import io.fraudops.common.TransactionEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/**
 * Deterministic rule engine — mirrors the Python side exactly.
 * Used as fallback when the ML API is unreachable and also to compose
 * the "reason codes" in every alert.
 */
public final class RuleEngine {
    private RuleEngine() {}

    public static final Set<String> HIGH_RISK_MERCHANTS =
            Set.of("crypto_exchange", "gift_cards", "wire_transfer", "gambling");

    public static double score(TransactionEvent tx) {
        double s = 0.0;
        double amt = tx.amount() == null ? 0.0 : tx.amount();
        if (amt >= 2500) s += 0.45;
        else if (amt >= 1000) s += 0.20;

        if (Boolean.TRUE.equals(tx.isForeign())) s += 0.15;
        if (tx.merchantCategory() != null && HIGH_RISK_MERCHANTS.contains(tx.merchantCategory())) s += 0.35;
        if (tx.velocity1h() != null && tx.velocity1h() >= 6) s += 0.25;
        if (Boolean.TRUE.equals(tx.crossBorder())) s += 0.20;
        if (tx.distinctCountries24h() != null && tx.distinctCountries24h() >= 3) s += 0.20;
        int hour = tx.hour() == null ? 12 : tx.hour();
        if (hour < 5 || hour >= 23) s += 0.08;
        return Math.min(1.0, s);
    }

    public static List<String> reasons(TransactionEvent tx) {
        List<String> r = new ArrayList<>();
        double amt = tx.amount() == null ? 0.0 : tx.amount();
        if (amt >= 2500) r.add("high_amount");
        else if (amt >= 1000) r.add("elevated_amount");
        if (Boolean.TRUE.equals(tx.isForeign())) r.add("foreign_transaction");
        if (tx.merchantCategory() != null && HIGH_RISK_MERCHANTS.contains(tx.merchantCategory()))
            r.add("high_risk_merchant:" + tx.merchantCategory());
        if (tx.velocity1h() != null && tx.velocity1h() >= 6) r.add("high_velocity");
        if (Boolean.TRUE.equals(tx.crossBorder())) r.add("cross_border");
        if (tx.distinctCountries24h() != null && tx.distinctCountries24h() >= 3) r.add("country_hopping");
        int hour = tx.hour() == null ? 12 : tx.hour();
        if (hour < 5 || hour >= 23) r.add("odd_hour");
        if (r.isEmpty()) r.add("nominal_pattern");
        return r;
    }
}
