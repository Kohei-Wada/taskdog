"""Tests for BackupClient."""

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest
from taskdog_client.backup_client import BackupClient


class TestBackupClient:
    """Test cases for BackupClient."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_base = Mock()
        self.mock_base.auth_headers.return_value = {"X-Api-Key": "k"}
        self.client = BackupClient(self.mock_base)

    def test_backup_writes_streamed_chunks(self, tmp_path: Path):
        """backup streams the response body to the output file."""
        response = Mock()
        response.is_success = True
        response.iter_bytes.return_value = [b"chunk-1", b"chunk-2"]

        @contextmanager
        def fake_stream(*args, **kwargs):
            yield response

        self.mock_base.client.stream = fake_stream

        out = tmp_path / "backup.db"
        self.client.backup(out)

        assert out.read_bytes() == b"chunk-1chunk-2"
        # The temp file is renamed away on success.
        assert not (tmp_path / "backup.db.part").exists()

    def test_backup_maps_error_response(self, tmp_path: Path):
        """A non-success response is routed through the base error handler."""
        response = Mock()
        response.is_success = False
        self.mock_base._handle_error.side_effect = RuntimeError("boom")

        @contextmanager
        def fake_stream(*args, **kwargs):
            yield response

        self.mock_base.client.stream = fake_stream

        with pytest.raises(RuntimeError, match="boom"):
            self.client.backup(tmp_path / "backup.db")
        self.mock_base._handle_error.assert_called_once_with(response)
        # No partial file and no corrupt output left behind on failure.
        assert not (tmp_path / "backup.db.part").exists()
        assert not (tmp_path / "backup.db").exists()

    def test_restore_uploads_file_and_returns_dto(self, tmp_path: Path):
        """restore posts a multipart upload and parses the pending result."""
        upload = tmp_path / "snapshot.db"
        upload.write_bytes(b"sqlite-bytes")
        self.mock_base._request_json.return_value = {
            "status": "pending",
            "message": "restart required",
        }

        result = self.client.restore(upload)

        assert result.status == "pending"
        assert result.message == "restart required"
        method, url = self.mock_base._request_json.call_args.args
        assert method == "post"
        assert url == "/api/v1/restore"
        assert "files" in self.mock_base._request_json.call_args.kwargs
