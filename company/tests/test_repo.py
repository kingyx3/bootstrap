"""Tests for project-repo parsing (pure functions; no network or git)."""
import importlib

import pytest


def _reload_with_repo(monkeypatch, value: str):
    monkeypatch.setenv("PROJECT_REPO", value)
    import config
    import repo
    importlib.reload(config)
    importlib.reload(repo)
    return repo


def test_owner_name_shorthand(monkeypatch):
    repo = _reload_with_repo(monkeypatch, "your-org/your-product")
    assert repo.repo_configured() is True
    assert repo.repo_name() == "your-product"
    assert repo.clone_url() == "https://github.com/your-org/your-product.git"


def test_full_https_url(monkeypatch):
    repo = _reload_with_repo(monkeypatch, "https://github.com/foo/bar.git")
    assert repo.repo_name() == "bar"
    assert repo.clone_url() == "https://github.com/foo/bar.git"


def test_ssh_url(monkeypatch):
    repo = _reload_with_repo(monkeypatch, "git@github.com:foo/baz.git")
    assert repo.repo_name() == "baz"
    assert repo.clone_url() == "git@github.com:foo/baz.git"


def test_unconfigured(monkeypatch):
    repo = _reload_with_repo(monkeypatch, "")
    assert repo.repo_configured() is False


def test_github_mcp_server_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_GITHUB_MCP", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    repo = _reload_with_repo(monkeypatch, "foo/bar")
    assert repo.github_mcp_server() is None


def test_github_mcp_server_when_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_GITHUB_MCP", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    repo = _reload_with_repo(monkeypatch, "foo/bar")
    server = repo.github_mcp_server()
    assert server is not None and server["command"] == "docker"


@pytest.fixture(autouse=True)
def _restore_config(monkeypatch):
    """Reload config/repo back to a clean state after each test."""
    yield
    monkeypatch.delenv("PROJECT_REPO", raising=False)
    import config
    import repo
    importlib.reload(config)
    importlib.reload(repo)
