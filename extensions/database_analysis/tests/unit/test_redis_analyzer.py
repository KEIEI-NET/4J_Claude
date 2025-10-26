"""
Unit tests for Redis Analyzer
"""

import pytest
from pathlib import Path

from multidb_analyzer.analyzers.redis_analyzer import RedisAnalyzer
from multidb_analyzer.models.database_models import CacheOperation, CachePattern


class TestRedisAnalyzer:
    """Test cases for RedisAnalyzer"""

    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = RedisAnalyzer()

    def test_analyze_redis_get(self, tmp_path):
        """Test analyzing Redis GET operation"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public User getUser(Long id) {
                String cacheKey = "user:" + id;
                User user = redis.get(cacheKey);
                return user;
            }
        ''')

        operations = self.analyzer.analyze_file(str(test_file))

        assert len(operations) == 1
        assert operations[0].operation == "get"
        assert "user:" in operations[0].key_pattern

    def test_analyze_redis_set(self, tmp_path):
        """Test analyzing Redis SET operation"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void cacheUser(User user) {
                String cacheKey = "user:" + user.getId();
                redis.set(cacheKey, user);
            }
        ''')

        operations = self.analyzer.analyze_file(str(test_file))

        assert len(operations) == 1
        assert operations[0].operation == "set"
        assert operations[0].missing_ttl is True  # No TTL set

    def test_analyze_cache_evict(self, tmp_path):
        """Test analyzing cache eviction"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void deleteUser(Long id) {
                String cacheKey = "user:" + id;
                cache.evict(cacheKey);
            }
        ''')

        operations = self.analyzer.analyze_file(str(test_file))

        assert len(operations) == 1
        assert operations[0].operation == "delete"

    def test_analyze_spring_cacheable(self, tmp_path):
        """Test analyzing Spring @Cacheable annotation"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @Cacheable("users")
            public User findById(Long id) {
                return userRepository.findById(id);
            }
        ''')

        operations = self.analyzer.analyze_file(str(test_file))

        assert len(operations) == 1
        assert operations[0].operation == "get"
        assert operations[0].cache_pattern == CachePattern.CACHE_ASIDE

    def test_analyze_spring_cache_put(self, tmp_path):
        """Test analyzing Spring @CachePut annotation"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @CachePut("users")
            public User updateUser(User user) {
                return userRepository.save(user);
            }
        ''')

        operations = self.analyzer.analyze_file(str(test_file))

        assert len(operations) == 1
        assert operations[0].operation == "set"
        assert operations[0].cache_pattern == CachePattern.WRITE_THROUGH

    def test_analyze_spring_cache_evict(self, tmp_path):
        """Test analyzing Spring @CacheEvict annotation"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            @CacheEvict("users")
            public void deleteUser(Long id) {
                userRepository.deleteById(id);
            }
        ''')

        operations = self.analyzer.analyze_file(str(test_file))

        assert len(operations) == 1
        assert operations[0].operation == "delete"

    def test_find_invalidation_points(self):
        """Test finding cache invalidation points"""
        operations = [
            CacheOperation(
                operation="delete",
                key_pattern="user:*",
                file_path="test.java",
                line_number=10,
                method_name="deleteUser",
            ),
            CacheOperation(
                operation="get",
                key_pattern="user:*",
                file_path="test.java",
                line_number=20,
                method_name="getUser",
            ),
        ]

        invalidation_methods = self.analyzer.find_invalidation_points("user:*", operations)

        assert "deleteUser" in invalidation_methods
        assert len(invalidation_methods) == 1

    def test_detect_cache_pattern(self):
        """Test detecting cache pattern"""
        # Cache-aside pattern
        operations_cache_aside = [
            CacheOperation(operation="get", key_pattern="user:*", file_path="test.java", line_number=10),
            CacheOperation(operation="set", key_pattern="user:*", file_path="test.java", line_number=20),
            CacheOperation(operation="delete", key_pattern="user:*", file_path="test.java", line_number=30),
        ]

        pattern = self.analyzer.detect_cache_pattern(operations_cache_aside)
        assert pattern == CachePattern.CACHE_ASIDE

    def test_get_known_cache_keys(self, tmp_path):
        """Test tracking known cache keys"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void test() {
                redis.get("user:1");
                redis.set("order:1", order);
            }
        ''')

        self.analyzer.analyze_file(str(test_file))
        cache_keys = self.analyzer.get_known_cache_keys()

        assert "user:1" in cache_keys or "order:1" in cache_keys

    def test_resolve_variable_not_found(self):
        """Test variable resolution when variable is not found"""
        content = '''
            public void test() {
                redis.get(unknownVar);
            }
        '''
        result = self.analyzer._resolve_variable(content, "unknownVar", len(content))
        assert result is None

    def test_extract_ttl_with_value(self):
        """Test TTL extraction"""
        # Test with TTL in call
        redis_call = "redis.set('key', value, 3600)"
        ttl = self.analyzer._extract_ttl(redis_call)
        assert ttl == 3600

        # Test with expire keyword
        redis_call2 = "redis.setex('key', expire=7200, value)"
        ttl2 = self.analyzer._extract_ttl(redis_call2)
        assert ttl2 == 7200

    def test_extract_ttl_no_value(self):
        """Test TTL extraction when no TTL present"""
        redis_call = "redis.set('key', value)"
        ttl = self.analyzer._extract_ttl(redis_call)
        assert ttl is None

    def test_determine_operation_type_expire(self):
        """Test operation type determination for expire"""
        op_type = self.analyzer._determine_operation_type("redis.expire('key', 3600)")
        assert op_type == "expire"

    def test_determine_operation_type_default(self):
        """Test operation type determination for unknown operation"""
        op_type = self.analyzer._determine_operation_type("redis.unknown('key')")
        assert op_type == "get"  # default

    def test_find_method_name(self):
        """Test method name extraction"""
        content = '''
            public void cacheUser(Long id) {
                redis.get("user:" + id);
            }
        '''
        position = content.find("redis.get")
        method_name = self.analyzer._find_method_name(content, position)
        assert method_name == "cacheUser"

    def test_find_method_name_not_found(self):
        """Test method name extraction when not found"""
        content = '''redis.get("key")'''
        method_name = self.analyzer._find_method_name(content, 0)
        assert method_name is None

    def test_analyze_redis_setex(self, tmp_path):
        """Test analyzing Redis SETEX operation with TTL"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void cacheWithExpiry(String key, String value) {
                redis.setex(key, 3600, value);
            }
        ''')

        operations = self.analyzer.analyze_file(str(test_file))
        assert len(operations) >= 1
        if operations:
            assert operations[0].operation == "set"

    def test_analyze_redis_del(self, tmp_path):
        """Test analyzing Redis DEL operation"""
        test_file = tmp_path / "test.java"
        test_file.write_text('''
            public void removeFromCache(String key) {
                redis.del(key);
            }
        ''')

        operations = self.analyzer.analyze_file(str(test_file))
        assert len(operations) >= 1
        if operations:
            assert operations[0].operation == "delete"

    def test_resolve_variable_complex(self):
        """Test resolving variable with multiple definitions"""
        content = '''
            String key1 = "old:value";
            // Some code
            String key2 = "user:" + id;
            redis.get(key2);
        '''
        # Should find the most recent definition
        result = self.analyzer._resolve_variable(content, "key2", len(content))
        assert result is not None
        assert "user:" in result

    def test_extract_ttl_from_setex(self):
        """Test TTL extraction from setex"""
        redis_call = "redis.setex('key', 7200, value)"
        ttl = self.analyzer._extract_ttl(redis_call)
        assert ttl == 7200

    def test_determine_operation_type_setex(self):
        """Test operation type for setex"""
        op_type = self.analyzer._determine_operation_type("redis.setex('key', 3600, 'value')")
        assert op_type == "set"

    def test_determine_operation_type_del(self):
        """Test operation type for del"""
        op_type = self.analyzer._determine_operation_type("redis.del('key')")
        assert op_type == "delete"

    def test_detect_cache_pattern_write_through(self):
        """Test detecting write-through cache pattern"""
        operations = [
            CacheOperation(operation="set", key_pattern="user:*", file_path="test.java", line_number=10),
            CacheOperation(operation="set", key_pattern="user:*", file_path="test.java", line_number=20),
        ]

        pattern = self.analyzer.detect_cache_pattern(operations)
        # Write-through involves setting cache
        assert pattern in [CachePattern.WRITE_THROUGH, CachePattern.CACHE_ASIDE]

    def test_find_invalidation_points_multiple(self):
        """Test finding multiple invalidation points"""
        operations = [
            CacheOperation(
                operation="delete",
                key_pattern="user:*",
                file_path="test.java",
                line_number=10,
                method_name="deleteUser",
            ),
            CacheOperation(
                operation="delete",
                key_pattern="user:*",
                file_path="test.java",
                line_number=30,
                method_name="updateUser",
            ),
            CacheOperation(
                operation="get",
                key_pattern="order:*",
                file_path="test.java",
                line_number=50,
                method_name="getOrder",
            ),
        ]

        invalidation_methods = self.analyzer.find_invalidation_points("user:*", operations)
        assert len(invalidation_methods) == 2
        assert "deleteUser" in invalidation_methods
        assert "updateUser" in invalidation_methods
