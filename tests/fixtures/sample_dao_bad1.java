package com.example.dao;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.ResultSet;

/**
 * 問題あり: ALLOW FILTERINGを使用している
 * これは全テーブルスキャンを引き起こし、パフォーマンス問題となる
 */
public class UserSearchDAO {

    private final Session session;

    // 問題: ALLOW FILTERINGを含むCQL定数
    private static final String FIND_BY_EMAIL_CQL = "SELECT * FROM users WHERE email = ? ALLOW FILTERING";
    private static final String FIND_BY_STATUS_CQL = "SELECT * FROM users WHERE status = ? ALLOW FILTERING";
    private static final String SEARCH_USERS_CQL = "SELECT * FROM users WHERE city = ? AND age > ? ALLOW FILTERING";

    public UserSearchDAO(Session session) {
        this.session = session;
    }

    /**
     * 問題: emailでの検索にALLOW FILTERINGを使用
     * これは本番環境で深刻なパフォーマンス問題を引き起こす
     */
    public User findByEmail(String email) {
        ResultSet rs = session.execute(FIND_BY_EMAIL_CQL, email);
        return mapToUser(rs.one());
    }

    /**
     * 問題: statusでの検索にもALLOW FILTERINGを使用
     */
    public List<User> findByStatus(String status) {
        ResultSet rs = session.execute(FIND_BY_STATUS_CQL, status);
        return mapToUsers(rs);
    }

    /**
     * 問題: 複数条件でのALLOW FILTERING
     */
    public List<User> searchUsers(String city, int minAge) {
        ResultSet rs = session.execute(SEARCH_USERS_CQL, city, minAge);
        return mapToUsers(rs);
    }

    private User mapToUser(com.datastax.driver.core.Row row) {
        if (row == null) return null;
        User user = new User();
        user.setUserId(row.getString("user_id"));
        user.setName(row.getString("name"));
        user.setEmail(row.getString("email"));
        return user;
    }

    private List<User> mapToUsers(ResultSet rs) {
        List<User> users = new ArrayList<>();
        for (com.datastax.driver.core.Row row : rs) {
            users.add(mapToUser(row));
        }
        return users;
    }
}
