package com.example.dao;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.PreparedStatement;
import com.datastax.driver.core.BoundStatement;
import com.datastax.driver.core.ResultSet;
import com.datastax.driver.core.ConsistencyLevel;

/**
 * 問題のないCassandra DAOの例
 * - パーティションキーを使用
 * - Prepared Statementを使用
 * - ALLOW FILTERINGなし
 */
public class UserDAO {

    private final Session session;
    private final PreparedStatement selectByIdStmt;
    private final PreparedStatement insertStmt;

    public UserDAO(Session session) {
        this.session = session;

        // Prepared Statementを事前準備
        this.selectByIdStmt = session.prepare(
            "SELECT * FROM users WHERE user_id = ?"
        );
        this.selectByIdStmt.setConsistencyLevel(ConsistencyLevel.QUORUM);

        this.insertStmt = session.prepare(
            "INSERT INTO users (user_id, name, email, created_at) VALUES (?, ?, ?, ?)"
        );
    }

    public User findById(String userId) {
        // パーティションキー（user_id）を使用
        BoundStatement bound = selectByIdStmt.bind(userId);
        ResultSet rs = session.execute(bound);
        return mapToUser(rs.one());
    }

    public void insert(User user) {
        BoundStatement bound = insertStmt.bind(
            user.getUserId(),
            user.getName(),
            user.getEmail(),
            user.getCreatedAt()
        );
        session.execute(bound);
    }

    private User mapToUser(com.datastax.driver.core.Row row) {
        if (row == null) return null;
        User user = new User();
        user.setUserId(row.getString("user_id"));
        user.setName(row.getString("name"));
        user.setEmail(row.getString("email"));
        user.setCreatedAt(row.getTimestamp("created_at"));
        return user;
    }
}
