package io.fraudops.alert.controller;

import io.fraudops.alert.repo.AlertDoc;
import io.fraudops.alert.repo.AlertRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

@RestController
@RequestMapping("/api/alerts")
public class AlertController {

    private final AlertRepository repo;

    public AlertController(AlertRepository repo) {
        this.repo = repo;
    }

    @GetMapping("/recent")
    public Map<String, Object> recent(@RequestParam(defaultValue = "50") int limit) {
        var items = repo.findRecent(PageRequest.of(0, Math.min(Math.max(limit, 1), 200)));
        return Map.of("total", items.size(), "items", items);
    }

    @PostMapping("/{alertId}/ack")
    public Map<String, Object> ack(@PathVariable String alertId) {
        AlertDoc found = repo.findByAlertId(alertId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND,
                        "Alert " + alertId + " not found"));
        AlertDoc updated = new AlertDoc(
                found.alertId(), found.txId(), found.userId(), found.amount(),
                found.merchantCategory(), found.country(), found.fraudScore(),
                found.severity(), found.reasons(), found.decision(),
                found.raisedAt(), true);
        repo.save(updated);
        return Map.of("ok", true, "alertId", alertId);
    }
}
