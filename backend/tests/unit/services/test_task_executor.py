"""
Testes unitários do task_executor — foco em is_action_intent()
e validações puras sem chamar DB.
"""

import pytest
from app.services.task_executor import ACTION_INTENTS, is_action_intent


class TestIsActionIntent:
    @pytest.mark.parametrize("intent", sorted(ACTION_INTENTS))
    def test_known_action_intents_return_true(self, intent: str):
        assert is_action_intent(intent) is True

    @pytest.mark.parametrize("intent", [
        "grade_query",
        "attendance_query",
        "schedule_query",
        "payslip_query",
        "faq",
        "greeting",
        "farewell",
        "unknown",
        "verification",
        "feedback_response",
    ])
    def test_non_action_intents_return_false(self, intent: str):
        assert is_action_intent(intent) is False

    def test_empty_string_returns_false(self):
        assert is_action_intent("") is False

    def test_random_string_returns_false(self):
        assert is_action_intent("this_does_not_exist") is False

    def test_action_intents_set_is_not_empty(self):
        assert len(ACTION_INTENTS) > 0

    def test_generate_boleto_is_action(self):
        assert is_action_intent("generate_boleto") is True

    def test_slide_generate_is_action(self):
        assert is_action_intent("slide_generate") is True

    def test_schedule_appointment_is_action(self):
        assert is_action_intent("schedule_appointment") is True

    def test_cancel_appointment_is_action(self):
        assert is_action_intent("cancel_appointment") is True
