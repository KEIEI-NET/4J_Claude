"""
Tests for Neo4j Client

Phase 4 Visualization - Neo4jクライアントのテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from ..neo4j_client.client import Neo4jClient


class TestNeo4jClient:
    """Neo4jClientのテスト"""

    @pytest.fixture
    def mock_driver(self):
        """モックドライバー"""
        with patch('backend.neo4j_client.client.GraphDatabase.driver') as mock:
            driver = MagicMock()
            mock.return_value = driver
            yield driver

    @pytest.fixture
    def client(self, mock_driver):
        """テスト用クライアント"""
        return Neo4jClient(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test"
        )

    def test_initialization(self, mock_driver):
        """初期化のテスト"""
        client = Neo4jClient(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test"
        )

        assert client.driver is not None

    def test_get_file_dependencies_found(self, client, mock_driver):
        """ファイル依存関係の取得 - ファイルが見つかる場合"""
        # モックセッション
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        # モック結果
        mock_file = MagicMock()
        mock_file.__getitem__.side_effect = lambda k: {
            'path': 'UserService.java',
            'name': 'UserService.java',
            'language': 'java'
        }[k]

        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda k: {
            'f': mock_file,
            'dependencies': [],
            'dependents': []
        }[k]

        mock_session.run.return_value.single.return_value = mock_record

        # テスト実行
        result = client.get_file_dependencies('UserService.java')

        assert result['file'] is not None
        assert 'dependencies' in result
        assert 'dependents' in result

    def test_get_file_dependencies_not_found(self, client, mock_driver):
        """ファイル依存関係の取得 - ファイルが見つからない場合"""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        mock_session.run.return_value.single.return_value = None

        result = client.get_file_dependencies('NonExistent.java')

        assert result['file'] is None
        assert result['dependencies'] == []
        assert result['dependents'] == []

    def test_get_impact_range(self, client, mock_driver):
        """影響範囲の取得テスト"""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        # モック結果
        mock_records = [
            {
                'file_path': 'OrderService.java',
                'file_name': 'OrderService.java',
                'language': 'java',
                'distance': 1,
                'weight': 0.9
            },
            {
                'file_path': 'PaymentService.java',
                'file_name': 'PaymentService.java',
                'language': 'java',
                'distance': 2,
                'weight': 0.7
            }
        ]

        mock_session.run.return_value = mock_records

        result = client.get_impact_range('UserService.java', max_depth=3)

        assert len(result) == 2
        assert result[0]['path'] == 'OrderService.java'
        assert result[0]['distance'] == 1

    def test_find_circular_dependencies(self, client, mock_driver):
        """循環依存検出のテスト"""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        mock_records = [
            {
                'cycle': ['A.java', 'B.java', 'C.java', 'A.java'],
                'cycle_length': 3
            }
        ]

        mock_session.run.return_value = mock_records

        result = client.find_circular_dependencies()

        assert len(result) == 1
        assert result[0]['cycle_length'] == 3
        assert result[0]['severity'] in ['high', 'medium', 'low']

    def test_health_check_success(self, client, mock_driver):
        """ヘルスチェック - 成功"""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        mock_record = MagicMock()
        mock_record.__getitem__.return_value = 1
        mock_session.run.return_value.single.return_value = mock_record

        assert client.health_check() is True

    def test_health_check_failure(self, client, mock_driver):
        """ヘルスチェック - 失敗"""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        mock_session.run.side_effect = Exception("Connection failed")

        assert client.health_check() is False

    def test_assess_cycle_severity(self, client):
        """サイクル重要度評価のテスト"""
        assert client._assess_cycle_severity(2) == "high"
        assert client._assess_cycle_severity(5) == "medium"
        assert client._assess_cycle_severity(8) == "low"
