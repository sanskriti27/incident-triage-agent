package com.example.repository;

import com.example.model.User;
import org.springframework.stereotype.Repository;
import org.springframework.beans.factory.annotation.Autowired;

@Repository
public class UserRepository {

    @Autowired
    private Database db;

    public User findById(String userId) {
        return db.query(
            "SELECT * FROM users WHERE id = ?", userId
        );
    }
}
