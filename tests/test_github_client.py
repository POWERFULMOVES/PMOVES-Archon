"""Unit tests for GitHub Client

Tests token minting, PR listing, and error handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

from python.src.agent_work_orders.github_integration.github_client import GitHubClient
from python.src.agent_work_orders.models import GitHubOperationError


@pytest.mark.unit
class TestGitHubClient:
    """GitHubClient unit tests."""

    @pytest.fixture
    def mock_credentials(self, monkeypatch):
        """Mock GitHub App credentials."""
        monkeypatch.setenv("GH_APP_ID", "123456")
        monkeypatch.setenv("GH_APP_INSTALLATION_ID", "789012")
        monkeypatch.setenv("GH_APP_SEC", """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA2test-----END RSA PRIVATE KEY-----""")

    @pytest.fixture
    def client(self, mock_credentials):
        """Create GitHubClient instance."""
        return GitHubClient(use_app_token=False)

    @pytest.mark.asyncio
    async def test_parse_repository_url_full(self, client):
        """Test parsing full GitHub URL."""
        result = client._parse_repository_url("https://github.com/owner/repo")
        assert result == ("owner", "repo")

    @pytest.mark.asyncio
    async def test_parse_repository_url_short(self, client):
        """Test parsing short owner/repo format."""
        result = client._parse_repository_url("owner/repo")
        assert result == ("owner", "repo")

    @pytest.mark.asyncio
    async def test_parse_repository_url_git_extension(self, client):
        """Test parsing URL with .git extension."""
        result = client._parse_repository_url("https://github.com/owner/repo.git")
        assert result == ("owner", "repo")

    @pytest.mark.asyncio
    async def test_parse_repository_url_invalid(self, client):
        """Test parsing invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid"):
            client._parse_repository_url("not-a-url")

    @pytest.mark.asyncio
    async def test_get_token_with_valid_credentials(self, mock_credentials):
        """Test token minting with valid credentials."""
        client = GitHubClient(use_app_token=True)

        with patch("python.src.agent_work_orders.github_integration.mint_github_token.mint_installation_token") as mock_mint:
            mock_mint.return_value = "test_token_123"

            token = await client._get_token()
            assert token == "test_token_123"
            # Verify cached
            assert client._token == "test_token_123"

    @pytest.mark.asyncio
    async def test_get_token_falls_back_to_error_without_credentials(self):
        """Test token minting raises error without credentials."""
        client = GitHubClient(use_app_token=True)

        with patch("python.src.agent_work_orders.github_integration.mint_github_token.mint_installation_token") as mock_mint:
            mock_mint.side_effect = KeyError("GH_APP_ID")

            with pytest.raises(GitHubOperationError, match="unavailable"):
                await client._get_token()

    @pytest.mark.asyncio
    async def test_list_pull_requests_with_app_token(self, mock_credentials):
        """Test listing PRs via GitHub App token."""
        client = GitHubClient(use_app_token=True)

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "number": 123,
                "title": "Test PR",
                "state": "open",
                "user": {"login": "testuser"},
                "created_at": "2026-03-14T00:00:00Z",
                "updated_at": "2026-03-14T00:00:00Z",
                "html_url": "https://github.com/POWERFULMOVES/test/pull/123",
                "base": {"ref": "main"},
                "head": {"ref": "feature"},
                "additions": 100,
                "deletions": 50,
                "changed_files": 3,
                "comments": 0,
                "review_comments": 0,
            }
        ]

        with patch("requests.get", return_value=mock_response):
            with patch.object(client, "_should_use_app_token", return_value=True):
                result = await client.list_pull_requests("POWERFULMOVES/test")

        assert len(result) == 1
        assert result[0]["number"] == 123

    @pytest.mark.asyncio
    async def test_list_pull_requests_fallback_to_gh_cli(self, client):
        """Test falling back to gh CLI when App token unavailable."""
        client = GitHubClient(use_app_token=True)

        # Mock subprocess to return gh CLI output
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.stdout = b'[{"number": 456, "title": "GH CLI PR"}]'
        mock_process.stderr = b""

        with patch.object(client, "_should_use_app_token", return_value=False):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                result = await client.list_pull_requests("POWERFULMOVES/test")

        assert len(result) == 1
        assert result[0]["number"] == 456

    @pytest.mark.asyncio
    async def test_list_pull_requests_handles_api_errors(self, mock_credentials):
        """Test error handling when API request fails."""
        client = GitHubClient(use_app_token=True)

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch("requests.get", return_value=mock_response):
            with patch.object(client, "_should_use_app_token", return_value=True):
                with pytest.raises(GitHubOperationError, match="API request failed"):
                    await client.list_pull_requests("POWERFULMOVES/test")
