from app.core.security.PII_detector import PIIDetector
from app.core.security.output_validator import OutputValidator
from app.core.security.security_pipeline import SecurityPipeline


def test_detect_finds_email_in_polish_text():
    detector = PIIDetector()

    found = detector.detect("kontakt jan@test.com")

    assert found == {"email": ["jan@test.com"]}


def test_mask_uses_presidio_default_markers():
    detector = PIIDetector()

    masked = detector.mask("kontakt jan@test.com")

    assert masked == "kontakt <EMAIL_ADDRESS>"
    assert "jan@test.com" not in masked


def test_security_pipeline_masks_input_pii():
    pipeline = SecurityPipeline()

    allowed, cleaned, notes = pipeline.check_input("kontakt jan@test.com")

    assert allowed is True
    assert "jan@test.com" not in cleaned
    assert "<EMAIL_ADDRESS>" in cleaned
    assert any("email" in note for note in notes)


def test_user_message_stored_original_in_db_masked_in_redis():
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.memory.conversation_memory import ConversationMemory
    from app.services.conversation.session import ConversationSession

    memory = MagicMock(spec=ConversationMemory)
    memory.append_message = AsyncMock()
    tokenizer = MagicMock()
    tokenizer.get_tokens_sum.return_value = 1

    created_message = MagicMock()
    created_message.id = 42
    created_message.role = "user"
    created_message.text = "kontakt jan@test.com"
    created_message.created_at = "2026-01-01T00:00:00Z"

    session = ConversationSession(
        "conv-1",
        "user-1",
        memory=memory,
        tokenizer=tokenizer,
    )
    session._conversation = MagicMock()
    session._conversation.update_conversation_window_size = AsyncMock()

    with patch("app.services.conversation.session.Message.create", new=AsyncMock(return_value=created_message)):
        import asyncio

        asyncio.run(
            session.add_message(
                "user",
                "kontakt jan@test.com",
                llm_text="kontakt <EMAIL_ADDRESS>",
            )
        )

    memory.append_message.assert_awaited_once_with(
        "conv-1",
        "user",
        "kontakt <EMAIL_ADDRESS>",
        message_id=42,
    )


def test_output_validator_masks_pii():
    validator = OutputValidator()

    cleaned, warnings = validator.validate("Twój email to jan@test.com")

    assert "jan@test.com" not in cleaned
    assert "<EMAIL_ADDRESS>" in cleaned
    assert any("email" in warning for warning in warnings)
