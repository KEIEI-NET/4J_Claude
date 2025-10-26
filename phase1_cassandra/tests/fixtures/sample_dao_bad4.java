package com.example.dao;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.ResultSet;
import com.datastax.driver.core.SimpleStatement;

/**
 * 問題あり: Prepared Statementを使用していない
 * 繰り返し実行されるクエリでPrepared Statementを使わないのは非効率
 */
public class ProductDAO {

    private final Session session;

    public ProductDAO(Session session) {
        this.session = session;
    }

    /**
     * 問題: 頻繁に呼ばれるメソッドでPrepared Statementを使用していない
     * 毎回CQLをパースする必要があり、パフォーマンスが低下
     */
    public Product findById(String productId) {
        // 文字列連結でCQLを構築 - SQLインジェクションのリスクもある
        String cql = "SELECT * FROM products WHERE product_id = '" + productId + "'";
        ResultSet rs = session.execute(cql);
        return mapToProduct(rs.one());
    }

    /**
     * 問題: SimpleStatementを使用（Prepared Statementを使うべき）
     */
    public void updatePrice(String productId, double newPrice) {
        SimpleStatement stmt = new SimpleStatement(
            "UPDATE products SET price = ? WHERE product_id = ?",
            newPrice, productId
        );
        session.execute(stmt);
    }

    /**
     * 問題: ループ内で毎回新しいCQLを実行
     * これは極めて非効率的
     */
    public void updateMultipleProducts(List<Product> products) {
        for (Product product : products) {
            String cql = String.format(
                "UPDATE products SET name = '%s', price = %f WHERE product_id = '%s'",
                product.getName(), product.getPrice(), product.getId()
            );
            session.execute(cql);  // 毎回パース！
        }
    }

    /**
     * 問題: 動的にCQLを構築している
     */
    public List<Product> searchProducts(String category, Double minPrice, Double maxPrice) {
        StringBuilder cql = new StringBuilder("SELECT * FROM products WHERE category = '");
        cql.append(category).append("'");

        if (minPrice != null) {
            cql.append(" AND price >= ").append(minPrice);
        }
        if (maxPrice != null) {
            cql.append(" AND price <= ").append(maxPrice);
        }

        ResultSet rs = session.execute(cql.toString());
        return mapToProducts(rs);
    }

    /**
     * 問題: execute()に直接文字列を渡している
     */
    public void insertProduct(Product product) {
        session.execute(
            "INSERT INTO products (product_id, name, category, price) VALUES ('" +
            product.getId() + "', '" +
            product.getName() + "', '" +
            product.getCategory() + "', " +
            product.getPrice() + ")"
        );
    }

    /**
     * 問題: 検索条件が変わるたびに新しいCQLを実行
     */
    public int countProductsByCategory(String category) {
        String cql = "SELECT COUNT(*) FROM products WHERE category = '" + category + "'";
        ResultSet rs = session.execute(cql);
        return (int) rs.one().getLong(0);
    }

    private Product mapToProduct(com.datastax.driver.core.Row row) {
        if (row == null) return null;
        Product product = new Product();
        product.setId(row.getString("product_id"));
        product.setName(row.getString("name"));
        product.setCategory(row.getString("category"));
        product.setPrice(row.getDouble("price"));
        return product;
    }

    private List<Product> mapToProducts(ResultSet rs) {
        List<Product> products = new ArrayList<>();
        for (com.datastax.driver.core.Row row : rs) {
            products.add(mapToProduct(row));
        }
        return products;
    }
}
