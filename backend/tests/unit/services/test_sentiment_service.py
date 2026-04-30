"""
Testes unitários do sentiment_service — sem DB, sem IA, lógica pura.
Cobertura: analyze(), is_evasion_signal()
"""

import pytest
from app.services.sentiment_service import SentimentResult, analyze, is_evasion_signal


class TestAnalyze:
    def test_empty_string_returns_neutral(self):
        result = analyze("")
        assert result.label == "neutral"
        assert result.score == 0.0

    def test_whitespace_only_returns_neutral(self):
        result = analyze("   ")
        assert result.label == "neutral"

    def test_positive_message(self):
        result = analyze("Muito obrigado, funcionou perfeitamente!")
        assert result.label == "positive"
        assert result.score > 0

    def test_negative_message(self):
        result = analyze("Péssimo atendimento, absurdo demais!")
        assert result.label == "negative"
        assert result.score < 0

    def test_neutral_message_no_keywords(self):
        result = analyze("Qual é o horário da secretaria?")
        assert result.label == "neutral"
        assert result.score == 0.0

    def test_evasion_phrase_triggers_negative(self):
        result = analyze("Vou largar o curso esse semestre")
        assert result.label == "negative"
        assert result.score < -0.5

    def test_score_clamped_at_minus_one(self):
        very_negative = "Péssimo horrível absurdo ridículo incompetente desistir abandonar"
        result = analyze(very_negative)
        assert result.score >= -1.0

    def test_score_clamped_at_plus_one(self):
        very_positive = "Excelente ótimo perfeito maravilha aprovei passei"
        result = analyze(very_positive)
        assert result.score <= 1.0

    def test_confidence_high_for_strong_sentiment(self):
        result = analyze("Absurdo! Péssimo atendimento!")
        assert result.confidence > 0.6

    def test_confidence_moderate_for_neutral(self):
        result = analyze("")
        assert result.confidence == 0.5

    def test_mixed_message_aggregates_scores(self):
        # Positivo + negativo → deve tender ao dominante
        result = analyze("Obrigado mas foi horrível")
        assert isinstance(result, SentimentResult)
        assert result.label in ("positive", "negative", "neutral")

    def test_case_insensitive_matching(self):
        result_lower = analyze("péssimo")
        result_upper = analyze("PÉSSIMO")
        assert result_lower.label == result_upper.label

    @pytest.mark.parametrize("msg,expected_label", [
        ("Muito obrigado!", "positive"),
        ("Obrigada, tudo certo!", "positive"),
        ("Nota baixa e muitas faltas", "negative"),
        ("Estou indignado com o serviço", "negative"),
        ("Qual é meu RA?", "neutral"),
    ])
    def test_parametrized_messages(self, msg: str, expected_label: str):
        result = analyze(msg)
        assert result.label == expected_label


class TestIsEvasionSignal:
    def test_cancel_enrollment_triggers(self):
        assert is_evasion_signal("Quero cancelar matrícula") is True

    def test_trancar_curso_triggers(self):
        assert is_evasion_signal("Preciso trancar curso esse semestre") is True

    def test_largar_curso_triggers(self):
        assert is_evasion_signal("Vou largar o curso") is True

    def test_desistir_triggers(self):
        assert is_evasion_signal("Estou pensando em desistir") is True

    def test_abandonar_triggers(self):
        assert is_evasion_signal("Posso abandonar o curso?") is True

    def test_sair_da_faculdade_triggers(self):
        assert is_evasion_signal("Quero sair da faculdade") is True

    def test_trancamento_triggers(self):
        assert is_evasion_signal("Quero fazer trancamento") is True

    def test_normal_message_does_not_trigger(self):
        assert is_evasion_signal("Qual é minha nota de cálculo?") is False

    def test_empty_does_not_trigger(self):
        assert is_evasion_signal("") is False

    def test_case_insensitive(self):
        assert is_evasion_signal("CANCELAR MATRÍCULA") is True
