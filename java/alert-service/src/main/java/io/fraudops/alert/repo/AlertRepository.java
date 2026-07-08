package io.fraudops.alert.repo;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;

import java.util.List;
import java.util.Optional;

public interface AlertRepository extends MongoRepository<AlertDoc, String> {
    Optional<AlertDoc> findByAlertId(String alertId);

    @Query(value = "{}", sort = "{ raisedAt: -1 }")
    List<AlertDoc> findRecent(org.springframework.data.domain.Pageable pageable);
}
