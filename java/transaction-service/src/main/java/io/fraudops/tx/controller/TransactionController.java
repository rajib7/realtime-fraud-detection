package io.fraudops.tx.controller;

import io.fraudops.common.TransactionEvent;
import io.fraudops.tx.service.TransactionPublisher;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/tx")
public class TransactionController {

    private final TransactionPublisher publisher;

    public TransactionController(TransactionPublisher publisher) {
        this.publisher = publisher;
    }

    @PostMapping("/transactions")
    public ResponseEntity<TransactionEvent> create(@RequestBody @Valid TransactionEvent event) {
        TransactionEvent stored = publisher.ingest(event);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(stored);
    }

    @GetMapping("/transactions/recent")
    public Map<String, Object> recent(@RequestParam(defaultValue = "50") int limit) {
        var items = publisher.recent(limit);
        return Map.of("total", items.size(), "items", items);
    }
}
