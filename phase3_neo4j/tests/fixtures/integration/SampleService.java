package com.example.service;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.ResultSet;
import com.datastax.driver.core.Row;

/**
 * Sample service for integration testing
 */
public class SampleService {

    private final Session session;

    public SampleService(Session session) {
        this.session = session;
    }

    /**
     * Get user by ID - GOOD: Uses prepared statement
     */
    public User getUserById(String userId) {
        String query = "SELECT * FROM users WHERE user_id = ?";
        PreparedStatement prepared = session.prepare(query);
        ResultSet results = session.execute(prepared.bind(userId));
        Row row = results.one();
        return row != null ? mapToUser(row) : null;
    }

    /**
     * Get users by email - BAD: Uses ALLOW FILTERING
     */
    public List<User> getUsersByEmail(String email) {
        String query = "SELECT * FROM users WHERE email = '" + email + "' ALLOW FILTERING";
        ResultSet results = session.execute(query);
        return mapToUsers(results);
    }

    /**
     * Get all users - BAD: Missing partition key
     */
    public List<User> getAllUsers() {
        String query = "SELECT * FROM users";
        ResultSet results = session.execute(query);
        return mapToUsers(results);
    }

    /**
     * Batch insert users - BAD: Large batch size
     */
    public void batchInsertUsers(List<User> users) {
        BatchStatement batch = new BatchStatement();
        for (User user : users) {
            String query = "INSERT INTO users (user_id, name, email) VALUES (?, ?, ?)";
            PreparedStatement prepared = session.prepare(query);
            batch.add(prepared.bind(user.getId(), user.getName(), user.getEmail()));
        }
        session.execute(batch);
    }

    private User mapToUser(Row row) {
        // Mapping logic
        return new User();
    }

    private List<User> mapToUsers(ResultSet results) {
        // Mapping logic
        return new ArrayList<>();
    }
}
