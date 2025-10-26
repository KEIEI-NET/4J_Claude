package com.example.repository;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.ResultSet;
import com.datastax.driver.core.PreparedStatement;

/**
 * Order repository for integration testing
 */
public class OrderRepository {

    private final Session session;
    private static final String FIND_BY_USER = "SELECT * FROM orders WHERE user_id = ?";

    public OrderRepository(Session session) {
        this.session = session;
    }

    /**
     * Find orders by user ID - GOOD: Uses prepared statement with partition key
     */
    public List<Order> findByUserId(String userId) {
        PreparedStatement prepared = session.prepare(FIND_BY_USER);
        ResultSet results = session.execute(prepared.bind(userId));
        return mapToOrders(results);
    }

    /**
     * Find orders by status - BAD: Missing partition key
     */
    public List<Order> findByStatus(String status) {
        String query = "SELECT * FROM orders WHERE status = ?";
        PreparedStatement prepared = session.prepare(query);
        ResultSet results = session.execute(prepared.bind(status));
        return mapToOrders(results);
    }

    /**
     * Create order - GOOD: Simple insert
     */
    public void createOrder(Order order) {
        String query = "INSERT INTO orders (order_id, user_id, status, total) VALUES (?, ?, ?, ?)";
        PreparedStatement prepared = session.prepare(query);
        session.execute(prepared.bind(
            order.getId(),
            order.getUserId(),
            order.getStatus(),
            order.getTotal()
        ));
    }

    private List<Order> mapToOrders(ResultSet results) {
        List<Order> orders = new ArrayList<>();
        for (Row row : results) {
            orders.add(mapToOrder(row));
        }
        return orders;
    }

    private Order mapToOrder(Row row) {
        // Mapping logic
        return new Order();
    }
}
