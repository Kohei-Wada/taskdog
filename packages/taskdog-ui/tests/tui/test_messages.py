"""Tests for TUI messages."""

import unittest

from taskdog.tui.messages import UIUpdateRequested


class TestUIUpdateRequested(unittest.TestCase):
    """Test cases for UIUpdateRequested message."""

    def test_can_create_without_source_action(self):
        """Test creating UIUpdateRequested without source_action."""
        msg = UIUpdateRequested()
        self.assertIsNone(msg.source_action)

    def test_can_create_with_source_action(self):
        """Test creating UIUpdateRequested with source_action."""
        msg = UIUpdateRequested(source_action="toggle_completed")
        self.assertEqual(msg.source_action, "toggle_completed")

    def test_is_textual_message(self):
        """Test that UIUpdateRequested is a Textual Message."""
        from textual.message import Message

        msg = UIUpdateRequested()
        self.assertIsInstance(msg, Message)

    def test_different_instances_are_independent(self):
        """Test that different instances don't share state."""
        msg1 = UIUpdateRequested(source_action="action1")
        msg2 = UIUpdateRequested(source_action="action2")

        self.assertEqual(msg1.source_action, "action1")
        self.assertEqual(msg2.source_action, "action2")


if __name__ == "__main__":
    unittest.main()
