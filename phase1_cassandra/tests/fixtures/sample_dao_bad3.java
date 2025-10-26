package com.example.dao;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.BatchStatement;
import com.datastax.driver.core.SimpleStatement;
import java.util.List;

/**
 * 問題あり: 大量のBatch処理
 * 大きすぎるバッチはメモリ問題とタイムアウトを引き起こす
 */
public class BulkOperationDAO {

    private final Session session;
    private static final int MAX_BATCH_SIZE = 100; // 推奨値

    public BulkOperationDAO(Session session) {
        this.session = session;
    }

    /**
     * 問題: 150件のINSERTを1つのバッチで実行
     * 推奨値の100を超えている
     */
    public void bulkInsertProducts(List<Product> products) {
        BatchStatement batch = new BatchStatement();

        // 150件のproductsを全て1つのバッチに追加
        for (Product product : products) {  // products.size() = 150
            String cql = String.format(
                "INSERT INTO products (product_id, name, price, stock) VALUES ('%s', '%s', %f, %d)",
                product.getId(), product.getName(), product.getPrice(), product.getStock()
            );
            batch.add(new SimpleStatement(cql));
        }

        session.execute(batch);  // 150件のバッチ実行 - 問題！
    }

    /**
     * 問題: ループ内で複数のバッチを作成するが、各バッチが大きすぎる
     */
    public void updateInventory(List<InventoryUpdate> updates) {
        BatchStatement batch = new BatchStatement();
        int count = 0;

        for (InventoryUpdate update : updates) {  // updates.size() = 500
            batch.add(new SimpleStatement(
                "UPDATE inventory SET quantity = ? WHERE product_id = ? AND warehouse_id = ?",
                update.getQuantity(), update.getProductId(), update.getWarehouseId()
            ));
            count++;

            // 200件ごとにバッチ実行 - これも大きすぎる
            if (count >= 200) {
                session.execute(batch);
                batch = new BatchStatement();
                count = 0;
            }
        }

        if (batch.size() > 0) {
            session.execute(batch);
        }
    }

    /**
     * 問題: 異なるパーティションへの大量バッチUPDATE
     */
    public void batchUpdateUserStatus(List<String> userIds, String newStatus) {
        BatchStatement batch = new BatchStatement();

        // 300人のユーザーのステータスを1つのバッチで更新
        for (String userId : userIds) {  // userIds.size() = 300
            batch.add(new SimpleStatement(
                "UPDATE users SET status = ? WHERE user_id = ?",
                newStatus, userId
            ));
        }

        session.execute(batch);  // 300件のバッチ - 深刻な問題！
    }

    /**
     * 問題: ログインセッションの一括削除（大量DELETE）
     */
    public void cleanupExpiredSessions(List<String> sessionIds) {
        BatchStatement batch = new BatchStatement();

        // 250件の期限切れセッションを削除
        for (String sessionId : sessionIds) {  // sessionIds.size() = 250
            batch.add(new SimpleStatement(
                "DELETE FROM user_sessions WHERE session_id = ?",
                sessionId
            ));
        }

        session.execute(batch);  // 250件のバッチDELETE
    }
}
