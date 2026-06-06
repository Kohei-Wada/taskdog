"""Tests for custom TUI keybinding resolution from cli.toml [keybindings]."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from taskdog.infrastructure.cli_config_manager import CliConfig
from taskdog.tui.app import TaskdogTUI, resolve_keymap


def _make_app(keybindings: dict[str, str]) -> TaskdogTUI:
    api_client = MagicMock()
    api_client.client_id = "test"
    websocket_client = MagicMock()
    websocket_client.connect = AsyncMock()
    websocket_client.disconnect = AsyncMock()
    return TaskdogTUI(
        api_client=api_client,
        websocket_client=websocket_client,
        cli_config=CliConfig(keybindings=keybindings),
    )


class TestBindingIds:
    """Every remappable binding must expose a unique, stable id."""

    def test_core_action_bindings_have_ids(self):
        ids = [b.id for b in TaskdogTUI.BINDINGS if b.id]
        # A representative set of actions users expect to remap.
        for expected in ("quit", "add", "start", "done", "refresh", "show_help"):
            assert expected in ids

    def test_binding_ids_are_unique(self):
        ids = [b.id for b in TaskdogTUI.BINDINGS if b.id]
        assert len(ids) == len(set(ids))


class TestResolveKeymap:
    """resolve_keymap filters config against the set of valid binding ids."""

    def test_keeps_known_ids(self):
        keymap, unknown = resolve_keymap(
            {"start": "ctrl+s", "done": "ctrl+d"}, valid_ids={"start", "done"}
        )
        assert keymap == {"start": "ctrl+s", "done": "ctrl+d"}
        assert unknown == []

    def test_drops_and_reports_unknown_ids(self):
        keymap, unknown = resolve_keymap(
            {"start": "ctrl+s", "bogus": "x"}, valid_ids={"start"}
        )
        assert keymap == {"start": "ctrl+s"}
        assert unknown == ["bogus"]

    def test_empty_config(self):
        keymap, unknown = resolve_keymap({}, valid_ids={"start"})
        assert keymap == {}
        assert unknown == []

    def test_resolves_against_real_app_bindings(self):
        valid_ids = {b.id for b in TaskdogTUI.BINDINGS if b.id}
        keymap, unknown = resolve_keymap({"start": "ctrl+s"}, valid_ids=valid_ids)
        assert keymap == {"start": "ctrl+s"}
        assert unknown == []


class TestKeymapApplied:
    """The configured keymap is applied to the live app on mount."""

    @pytest.mark.asyncio
    async def test_custom_key_overrides_default(self):
        app = _make_app({"start": "ctrl+s"})
        async with app.run_test() as pilot:
            await pilot.pause()
            start_keys = [
                key
                for key, active in app.active_bindings.items()
                if active.binding.action == "start"
            ]
        assert start_keys == ["ctrl+s"]

    @pytest.mark.asyncio
    async def test_unknown_id_warns_and_keeps_defaults(self):
        app = _make_app({"bogus": "z"})
        app.notify = MagicMock()  # type: ignore[method-assign]
        async with app.run_test() as pilot:
            await pilot.pause()
            start_keys = [
                key
                for key, active in app.active_bindings.items()
                if active.binding.action == "start"
            ]
        assert start_keys == ["s"]
        assert any("bogus" in str(call.args[0]) for call in app.notify.call_args_list)
