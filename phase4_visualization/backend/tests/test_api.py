"""
Tests for FastAPI Endpoints

Phase 4 Visualization - APIエンドポイントのテスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from ..api.main import app


@pytest.fixture
def mock_neo4j_client():
    """モックNeo4jクライアント"""
    with patch('backend.api.main.neo4j_client') as mock_client:
        # ヘルスチェックを常に成功させる
        mock_client.health_check.return_value = True
        yield mock_client


@pytest.fixture
def client(mock_neo4j_client):
    """テストクライアント"""
    return TestClient(app)


class TestHealthCheck:
    """ヘルスチェックのテスト"""

    def test_health_check_success(self, client, mock_neo4j_client):
        """ヘルスチェック - 成功"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['neo4j_connected'] is True
        assert data['version'] == '4.0.0'

    def test_health_check_neo4j_down(self, client, mock_neo4j_client):
        """ヘルスチェック - Neo4jダウン"""
        mock_neo4j_client.health_check.return_value = False

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'degraded'
        assert data['neo4j_connected'] is False


class TestImpactAnalysis:
    """影響範囲分析APIのテスト"""

    def test_impact_analysis_success(self, client, mock_neo4j_client):
        """影響範囲分析 - 成功"""
        # モックデータ
        mock_neo4j_client.get_impact_range.return_value = [
            {
                'path': 'OrderService.java',
                'name': 'OrderService.java',
                'language': 'java',
                'distance': 1,
                'weight': 0.9,
                'risk_contribution': 0.9
            }
        ]

        mock_neo4j_client.get_file_dependencies.return_value = {
            'file': {
                'id': '1',
                'labels': ['File'],
                'properties': {
                    'path': 'UserService.java',
                    'name': 'UserService.java',
                    'language': 'java',
                    'size': 2048,
                    'complexity': 45.2
                }
            },
            'dependencies': [],
            'dependents': []
        }

        request_data = {
            'target_type': 'file',
            'target_path': 'UserService.java',
            'depth': 3,
            'include_indirect': True
        }

        response = client.post("/api/impact-analysis", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data['target']['path'] == 'UserService.java'
        assert data['impact_summary']['total_affected_files'] == 1
        assert data['impact_summary']['risk_level'] in ['low', 'medium', 'high']
        assert len(data['affected_files']) == 1

    def test_impact_analysis_file_not_found(self, client, mock_neo4j_client):
        """影響範囲分析 - ファイルが見つからない"""
        mock_neo4j_client.get_file_dependencies.return_value = {
            'file': None,
            'dependencies': [],
            'dependents': []
        }

        request_data = {
            'target_type': 'file',
            'target_path': 'NonExistent.java',
            'depth': 3,
            'include_indirect': True
        }

        response = client.post("/api/impact-analysis", json=request_data)

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()


class TestDependencies:
    """依存関係取得APIのテスト"""

    def test_get_dependencies_success(self, client, mock_neo4j_client):
        """依存関係取得 - 成功"""
        mock_neo4j_client.get_file_dependencies.return_value = {
            'file': {
                'id': '1',
                'labels': ['File'],
                'properties': {
                    'path': 'UserService.java',
                    'name': 'UserService.java',
                    'language': 'java'
                }
            },
            'dependencies': [
                {
                    'id': '2',
                    'labels': ['File'],
                    'properties': {'path': 'DatabaseService.java'}
                }
            ],
            'dependents': [
                {
                    'id': '3',
                    'labels': ['File'],
                    'properties': {'path': 'OrderService.java'}
                }
            ]
        }

        response = client.get("/api/dependencies/UserService.java")

        assert response.status_code == 200
        data = response.json()

        assert data['file']['path'] == 'UserService.java'
        assert data['dependencies']['dependency_count'] == 1
        assert data['dependencies']['dependent_count'] == 1


class TestCircularDependencies:
    """循環依存検出APIのテスト"""

    def test_circular_dependencies_found(self, client, mock_neo4j_client):
        """循環依存検出 - 検出あり"""
        mock_neo4j_client.find_circular_dependencies.return_value = [
            {
                'cycle_id': 'cycle-1',
                'cycle_length': 3,
                'nodes': ['A.java', 'B.java', 'C.java'],
                'severity': 'high'
            }
        ]

        response = client.get("/api/circular-dependencies")

        assert response.status_code == 200
        data = response.json()

        assert data['total_cycles'] == 1
        assert len(data['circular_dependencies']) == 1
        assert '解消' in data['recommendation']

    def test_circular_dependencies_none_found(self, client, mock_neo4j_client):
        """循環依存検出 - 検出なし"""
        mock_neo4j_client.find_circular_dependencies.return_value = []

        response = client.get("/api/circular-dependencies")

        assert response.status_code == 200
        data = response.json()

        assert data['total_cycles'] == 0
        assert 'ありません' in data['recommendation']


class TestPathFinder:
    """パスファインダーAPIのテスト"""

    def test_path_finder_path_found(self, client, mock_neo4j_client):
        """パスファインダー - パス発見"""
        mock_neo4j_client.find_path.return_value = [
            {
                'length': 2,
                'nodes': [
                    {'type': 'File', 'name': 'A.java', 'path': 'A.java'},
                    {'type': 'File', 'name': 'B.java', 'path': 'B.java'},
                    {'type': 'File', 'name': 'C.java', 'path': 'C.java'}
                ],
                'relationships': [
                    {'type': 'DEPENDS_ON', 'strength': 0.9},
                    {'type': 'DEPENDS_ON', 'strength': 0.8}
                ]
            }
        ]

        request_data = {
            'source': 'A.java',
            'target': 'C.java',
            'max_depth': 5
        }

        response = client.post("/api/path-finder", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data['total_paths_found'] == 1
        assert data['shortest_path_length'] == 2
        assert len(data['paths']) == 1

    def test_path_finder_no_path(self, client, mock_neo4j_client):
        """パスファインダー - パスなし"""
        mock_neo4j_client.find_path.return_value = []

        request_data = {
            'source': 'A.java',
            'target': 'Z.java',
            'max_depth': 5
        }

        response = client.post("/api/path-finder", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data['total_paths_found'] == 0
        assert data['shortest_path_length'] == 0
