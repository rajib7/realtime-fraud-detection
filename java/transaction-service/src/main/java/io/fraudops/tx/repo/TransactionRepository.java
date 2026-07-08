package io.fraudops.tx.repo;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;

import java.util.List;

public interface TransactionRepository extends MongoRepository<TransactionDoc, String> {
    @Query(value = "{}", sort = "{ createdAt: -1 }")
    List<TransactionDoc> findRecent(org.springframework.data.domain.Pageable pageable);
}
