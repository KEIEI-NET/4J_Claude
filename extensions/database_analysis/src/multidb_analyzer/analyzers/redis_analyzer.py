"""
Redis Analyzer for cache operations

Extracts and analyzes Redis cache operations from source code
"""

import re
from typing import List, Optional, Set
from pathlib import Path

from multidb_analyzer.models.database_models import (
    CacheOperation,
    CachePattern,
    DatabaseType,
)


class RedisAnalyzer:
    """Analyzes Redis cache operations in source code"""

    def __init__(self):
        self._known_cache_keys: Set[str] = set()

    def analyze_file(self, file_path: str) -> List[CacheOperation]:
        """
        Extract and analyze all Redis cache operations in a file

        Args:
            file_path: Path to source code file

        Returns:
            List of CacheOperation objects
        """
        operations: List[CacheOperation] = []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Pattern 1: Redis client method calls with string literals
        redis_literal_patterns = [
            (r"redis\.get\(['\"]([^'\"]+)['\"]\)", "get"),  # redis.get("key")
            (r"redis\.set\(['\"]([^'\"]+)['\"],\s*([^)]+)\)", "set"),  # redis.set("key", value)
            (r"redis\.setex\(['\"]([^'\"]+)['\"],\s*([^)]+)\)", "set"),  # redis.setex("key", ttl, value)
            (r"redis\.del\(['\"]([^'\"]+)['\"]\)", "delete"),  # redis.del("key")
            (r"redisTemplate\.opsForValue\(\)\.get\(['\"]([^'\"]+)['\"]\)", "get"),  # Spring Redis
            (r"cache\.get\(['\"]([^'\"]+)['\"]\)", "get"),  # Generic cache.get
            (r"cache\.put\(['\"]([^'\"]+)['\"],\s*([^)]+)\)", "set"),  # Generic cache.put
            (r"cache\.evict\(['\"]([^'\"]+)['\"]\)", "delete"),  # Cache eviction
        ]

        for pattern, op_type in redis_literal_patterns:
            for match in re.finditer(pattern, content):
                line_number = content[: match.start()].count("\n") + 1
                key_pattern = match.group(1)

                # Extract TTL if present
                ttl = self._extract_ttl(match.group(0))

                # Find method context
                method_name = self._find_method_name(content, match.start())

                operation = CacheOperation(
                    operation=op_type,
                    key_pattern=key_pattern,
                    file_path=file_path,
                    line_number=line_number,
                    method_name=method_name,
                    ttl=ttl,
                    missing_ttl=(op_type == "set" and ttl is None),
                )

                operations.append(operation)
                self._known_cache_keys.add(key_pattern)

        # Pattern 2: Redis client method calls with variables
        redis_var_patterns = [
            (r"redis\.get\((\w+)\)", "get"),  # redis.get(variable)
            (r"redis\.set\((\w+),\s*[^)]+\)", "set"),  # redis.set(variable, value)
            (r"redis\.setex\((\w+),\s*[^)]+\)", "set"),  # redis.setex(variable, ttl, value)
            (r"redis\.del\((\w+)\)", "delete"),  # redis.del(variable)
            (r"cache\.get\((\w+)\)", "get"),  # cache.get(variable)
            (r"cache\.put\((\w+),\s*[^)]+\)", "set"),  # cache.put(variable, value)
            (r"cache\.evict\((\w+)\)", "delete"),  # cache.evict(variable)
        ]

        for pattern, op_type in redis_var_patterns:
            for match in re.finditer(pattern, content):
                line_number = content[: match.start()].count("\n") + 1
                var_name = match.group(1)

                # Try to find the variable assignment to get the actual key pattern
                key_pattern = self._resolve_variable(content, var_name, match.start()) or f"[{var_name}]"

                # Extract TTL if present
                ttl = self._extract_ttl(match.group(0))

                # Find method context
                method_name = self._find_method_name(content, match.start())

                operation = CacheOperation(
                    operation=op_type,
                    key_pattern=key_pattern,
                    file_path=file_path,
                    line_number=line_number,
                    method_name=method_name,
                    ttl=ttl,
                    missing_ttl=(op_type == "set" and ttl is None),
                )

                operations.append(operation)
                self._known_cache_keys.add(key_pattern)

        # Pattern 2: @Cacheable annotations (Spring)
        cacheable_operations = self._extract_cacheable_annotations(content, file_path)
        operations.extend(cacheable_operations)

        return operations

    def _resolve_variable(self, content: str, var_name: str, position: int) -> Optional[str]:
        """
        Try to resolve a variable to its string value

        Args:
            content: File content
            var_name: Variable name to resolve
            position: Position where variable is used

        Returns:
            Resolved string value or None
        """
        # Look backward from position for variable assignment
        before_content = content[:position]

        # Pattern: String cacheKey = "user:" + id;
        # Pattern: var cacheKey = "user:" + id;
        # Pattern: cacheKey = "user:" + id;
        patterns = [
            rf'{var_name}\s*=\s*["\']([^"\']+)["\']',  # Simple assignment
            rf'{var_name}\s*=\s*["\']([^"\']+)["\'](?:\s*\+\s*\w+)?',  # With concatenation
        ]

        for pattern in patterns:
            matches = list(re.finditer(pattern, before_content))
            if matches:
                # Get the last match (most recent assignment)
                last_match = matches[-1]
                return last_match.group(1)

        return None

    def _determine_operation_type(self, redis_call: str) -> str:
        """Determine the type of Redis operation"""
        call_lower = redis_call.lower()

        if "get" in call_lower:
            return "get"
        elif "set" in call_lower or "put" in call_lower:
            return "set"
        elif "del" in call_lower or "evict" in call_lower:
            return "delete"
        elif "expire" in call_lower:
            return "expire"

        return "get"  # default

    def _extract_ttl(self, redis_call: str) -> Optional[int]:
        """Extract TTL from Redis call if present"""
        # Look for setex format: redis.setex('key', ttl, value)
        if "setex" in redis_call:
            setex_pattern = r"setex\s*\([^,]+,\s*(\d+)"
            match = re.search(setex_pattern, redis_call)
            if match:
                return int(match.group(1))

        # Look for TTL/expiration time
        ttl_patterns = [
            r"expire[=:]\s*(\d+)",
            r"ttl[=:]\s*(\d+)",
            r",\s*(\d+)\s*\)",  # redis.set("key", value, 3600)
        ]

        for pattern in ttl_patterns:
            match = re.search(pattern, redis_call, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _find_method_name(self, content: str, position: int) -> Optional[str]:
        """Find the method name containing the cache operation"""
        before_position = content[:position]

        method_patterns = [
            r"(?:public|private|protected)?\s+\w+\s+(\w+)\s*\([^)]*\)\s*{[^}]*$",
            r"def\s+(\w+)\s*\([^)]*\):",  # Python
            r"func\s+(\w+)\s*\([^)]*\)",  # Go
        ]

        for pattern in method_patterns:
            match = re.search(pattern, before_position[-1000:])
            if match:
                return match.group(1)

        return None

    def _extract_cacheable_annotations(
        self, content: str, file_path: str
    ) -> List[CacheOperation]:
        """Extract cache operations from @Cacheable, @CachePut, @CacheEvict annotations"""
        operations = []

        # @Cacheable pattern
        cacheable_pattern = r'@Cacheable\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'
        for match in re.finditer(cacheable_pattern, content):
            cache_name = match.group(1)
            line_number = content[: match.start()].count("\n") + 1
            method_name = self._find_method_name(content, match.end())

            operation = CacheOperation(
                operation="get",
                key_pattern=cache_name + ":*",
                file_path=file_path,
                line_number=line_number,
                method_name=method_name,
                cache_pattern=CachePattern.CACHE_ASIDE,
            )
            operations.append(operation)

        # @CachePut pattern
        cache_put_pattern = r'@CachePut\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'
        for match in re.finditer(cache_put_pattern, content):
            cache_name = match.group(1)
            line_number = content[: match.start()].count("\n") + 1
            method_name = self._find_method_name(content, match.end())

            operation = CacheOperation(
                operation="set",
                key_pattern=cache_name + ":*",
                file_path=file_path,
                line_number=line_number,
                method_name=method_name,
                cache_pattern=CachePattern.WRITE_THROUGH,
            )
            operations.append(operation)

        # @CacheEvict pattern
        cache_evict_pattern = r'@CacheEvict\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'
        for match in re.finditer(cache_evict_pattern, content):
            cache_name = match.group(1)
            line_number = content[: match.start()].count("\n") + 1
            method_name = self._find_method_name(content, match.end())

            operation = CacheOperation(
                operation="delete",
                key_pattern=cache_name + ":*",
                file_path=file_path,
                line_number=line_number,
                method_name=method_name,
            )
            operations.append(operation)

        return operations

    def find_invalidation_points(self, key_pattern: str, all_operations: List[CacheOperation]) -> List[str]:
        """
        Find all cache invalidation points for a given key pattern

        Args:
            key_pattern: Cache key pattern to search for
            all_operations: List of all cache operations

        Returns:
            List of method names that invalidate the cache
        """
        invalidation_methods = []

        for op in all_operations:
            if op.operation == "delete" and op.key_pattern == key_pattern:
                if op.method_name:
                    invalidation_methods.append(op.method_name)

        return invalidation_methods

    def detect_cache_pattern(self, operations: List[CacheOperation]) -> Optional[CachePattern]:
        """
        Detect the cache pattern being used

        Args:
            operations: List of cache operations

        Returns:
            Detected cache pattern
        """
        has_get = any(op.operation == "get" for op in operations)
        has_set = any(op.operation == "set" for op in operations)
        has_delete = any(op.operation == "delete" for op in operations)

        if has_get and has_set and has_delete:
            return CachePattern.CACHE_ASIDE
        elif has_get and has_set:
            return CachePattern.READ_THROUGH
        elif has_set:
            return CachePattern.WRITE_THROUGH

        return None

    def get_known_cache_keys(self) -> Set[str]:
        """Get all known cache key patterns"""
        return self._known_cache_keys.copy()
