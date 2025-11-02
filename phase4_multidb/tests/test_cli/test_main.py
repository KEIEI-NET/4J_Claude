"""
Tests for CLI main entry point
"""

from unittest.mock import patch, MagicMock

import pytest

from multidb_analyzer.cli.main import main, cli


class TestMainFunction:
    """Tests for main() function"""

    @patch('multidb_analyzer.cli.main.cli')
    def test_main_success(self, mock_cli):
        """Test main function success"""
        mock_cli.return_value = None

        # Should not raise
        try:
            main()
        except SystemExit:
            pass  # Expected for normal execution

    @patch('multidb_analyzer.cli.main.cli')
    def test_main_keyboard_interrupt(self, mock_cli):
        """Test main function with keyboard interrupt"""
        mock_cli.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch('multidb_analyzer.cli.main.cli')
    def test_main_general_exception(self, mock_cli):
        """Test main function with general exception"""
        mock_cli.side_effect = Exception("Test error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1


class TestMainModule:
    """Tests for __main__ execution"""

    def test_main_module_callable(self):
        """Test that main is callable"""
        assert callable(main)

    def test_cli_group_exists(self):
        """Test that CLI group exists"""
        assert cli is not None
        assert hasattr(cli, 'name')
