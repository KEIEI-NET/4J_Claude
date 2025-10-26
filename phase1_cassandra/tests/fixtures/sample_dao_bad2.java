package com.example.dao;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.ResultSet;

/**
 * 問題あり: Partition Keyを使用していない
 * これは全ノードスキャンを引き起こす
 */
public class OrderDAO {

    private final Session session;

    // 問題: Partition Keyを使用していないCQL定数
    private static final String FIND_BY_ORDER_NUMBER_CQL = "SELECT * FROM orders WHERE order_number = ?";
    private static final String FIND_BY_CUSTOMER_NAME_CQL = "SELECT * FROM orders WHERE customer_name = ?";
    private static final String GET_ALL_ORDERS_CQL = "SELECT * FROM orders";
    private static final String FIND_BY_DATE_RANGE_CQL = "SELECT * FROM orders WHERE order_date >= ? AND order_date <= ?";

    public OrderDAO(Session session) {
        this.session = session;
    }

    /**
     * 問題: Partition Key (order_id) を使わずにorder_numberで検索
     * order_numberはクラスタリングキーなので、全パーティションをスキャン
     */
    public Order findByOrderNumber(String orderNumber) {
        ResultSet rs = session.execute(FIND_BY_ORDER_NUMBER_CQL, orderNumber);
        return mapToOrder(rs.one());
    }

    /**
     * 問題: セカンダリインデックスのみで検索
     * Partition Keyなしでセカンダリインデックスを使用するのは非効率
     */
    public List<Order> findByCustomerName(String customerName) {
        ResultSet rs = session.execute(FIND_BY_CUSTOMER_NAME_CQL, customerName);
        return mapToOrders(rs);
    }

    /**
     * 問題: 全テーブルスキャン（WHERE句なし）
     */
    public List<Order> getAllOrders() {
        ResultSet rs = session.execute(GET_ALL_ORDERS_CQL);
        return mapToOrders(rs);
    }

    /**
     * 問題: 日付範囲のみでの検索（Partition Keyなし）
     */
    public List<Order> findByDateRange(Date startDate, Date endDate) {
        ResultSet rs = session.execute(FIND_BY_DATE_RANGE_CQL, startDate, endDate);
        return mapToOrders(rs);
    }

    private Order mapToOrder(com.datastax.driver.core.Row row) {
        if (row == null) return null;
        Order order = new Order();
        order.setOrderId(row.getString("order_id"));
        order.setOrderNumber(row.getString("order_number"));
        order.setCustomerName(row.getString("customer_name"));
        return order;
    }

    private List<Order> mapToOrders(ResultSet rs) {
        List<Order> orders = new ArrayList<>();
        for (com.datastax.driver.core.Row row : rs) {
            orders.add(mapToOrder(row));
        }
        return orders;
    }
}
