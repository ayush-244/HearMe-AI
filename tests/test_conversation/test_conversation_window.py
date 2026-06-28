import pytest
from backend.app.reasoning.conversation.conversation_window import ConversationWindow, DEFAULT_WINDOW_SIZE


class TestConversationWindow:
    @pytest.fixture
    def window(self):
        return ConversationWindow(window_size=4)

    def test_get_or_create_new(self, window):
        state = window.get_or_create("conv1")
        assert state.conversation_id == "conv1"
        assert state.recent_messages == []
        assert state.turn_count == 0

    def test_add_message(self, window):
        window.add_message("conv1", "user", "Hello")
        state = window.get_or_create("conv1")
        assert len(state.recent_messages) == 1
        assert state.recent_messages[0]["role"] == "user"
        assert state.recent_messages[0]["content"] == "Hello"
        assert state.turn_count == 1

    def test_add_multiple_messages(self, window):
        window.add_message("conv1", "user", "Q1")
        window.add_message("conv1", "assistant", "A1")
        window.add_message("conv1", "user", "Q2")
        state = window.get_or_create("conv1")
        assert len(state.recent_messages) == 3
        assert state.turn_count == 3

    def test_window_size_limit_sets_flag(self, window):
        for i in range(10):
            window.add_message("conv1", "user", f"Q{i}")
        state = window.get_or_create("conv1")
        assert state.needs_summary_update is True
        assert len(state.recent_messages) == 10

    def test_compress_reduces_to_window_size(self, window):
        for i in range(10):
            window.add_message("conv1", "user", f"Q{i}")
        compressed = window.compress("conv1")
        assert compressed > 0
        state = window.get_or_create("conv1")
        assert len(state.recent_messages) <= 4

    def test_get_history(self, window):
        for i in range(3):
            window.add_message("conv1", "user", f"Q{i}")
            window.add_message("conv1", "assistant", f"A{i}")
        history = window.get_history("conv1")
        assert len(history) == 6

    def test_get_history_with_limit(self, window):
        for i in range(3):
            window.add_message("conv1", "user", f"Q{i}")
            window.add_message("conv1", "assistant", f"A{i}")
        history = window.get_history("conv1", limit=2)
        assert len(history) == 2

    def test_should_summarize_true(self, window):
        for i in range(int(4 * 1.5) + 1):
            window.add_message("conv1", "user", f"Q{i}")
        assert window.should_summarize("conv1") is True

    def test_should_summarize_false(self, window):
        window.add_message("conv1", "user", "Q1")
        assert window.should_summarize("conv1") is False

    def test_compress(self, window):
        for i in range(10):
            window.add_message("conv1", "user", f"Q{i}")
        compressed = window.compress("conv1")
        assert compressed > 0
        state = window.get_or_create("conv1")
        assert len(state.recent_messages) <= 4

    def test_get_summary_default(self, window):
        summary = window.get_summary("conv1")
        assert summary == ""

    def test_set_summary(self, window):
        window.set_summary("conv1", "Conversation about AI")
        assert window.get_summary("conv1") == "Conversation about AI"

    def test_get_turn_count(self, window):
        assert window.get_turn_count("conv1") == 0
        window.add_message("conv1", "user", "Q")
        assert window.get_turn_count("conv1") == 1

    def test_clear(self, window):
        window.add_message("conv1", "user", "Q")
        window.clear("conv1")
        assert window.get_turn_count("conv1") == 0
        assert window.get_summary("conv1") == ""

    def test_get_last_user_message(self, window):
        window.add_message("conv1", "user", "Hello")
        window.add_message("conv1", "assistant", "Hi")
        window.add_message("conv1", "user", "How are you?")
        assert window.get_last_user_message("conv1") == "How are you?"

    def test_get_last_user_message_empty(self, window):
        assert window.get_last_user_message("new_conv") is None

    def test_get_last_assistant_message(self, window):
        window.add_message("conv1", "user", "Hello")
        window.add_message("conv1", "assistant", "Hi there!")
        assert window.get_last_assistant_message("conv1") == "Hi there!"

    def test_get_last_assistant_message_empty(self, window):
        assert window.get_last_assistant_message("new_conv") is None

    def test_get_all_contexts(self, window):
        window.get_or_create("conv1")
        window.get_or_create("conv2")
        contexts = window.get_all_contexts()
        assert "conv1" in contexts
        assert "conv2" in contexts

    def test_get_history_return_copy(self, window):
        window.add_message("conv1", "user", "Q")
        history = window.get_history("conv1")
        history.append({"role": "system", "content": "extra"})
        state = window.get_or_create("conv1")
        assert len(state.recent_messages) == 1

    def test_needs_summary_update_flag(self, window):
        window.add_message("conv1", "user", "Q")
        state = window.get_or_create("conv1")
        assert state.needs_summary_update is False
        for i in range(10):
            window.add_message("conv1", "user", f"Q{i}")
        assert state.needs_summary_update is True

    def test_to_dict(self, window):
        window.add_message("conv1", "user", "Q")
        window.add_message("conv1", "assistant", "A")
        state = window.get_or_create("conv1")
        d = state.to_dict()
        assert d["conversation_id"] == "conv1"
        assert d["turn_count"] == 2
        assert d["message_count"] == 2

    def test_default_window_size(self):
        window = ConversationWindow()
        assert window._window_size == DEFAULT_WINDOW_SIZE

    def test_custom_window_size(self):
        window = ConversationWindow(window_size=10)
        assert window._window_size == 10

    def test_multiple_conversations_independent(self, window):
        window.add_message("a", "user", "Q from A")
        window.add_message("b", "user", "Q from B")
        assert window.get_last_user_message("a") == "Q from A"
        assert window.get_last_user_message("b") == "Q from B"
