from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.memory.conversation_context import ConversationContext


def test_to_chat_messages_without_summary():
    messages = [HumanMessage(content="cześć"), AIMessage(content="witaj")]
    context = ConversationContext(summary=None, messages=messages)

    assert context.to_chat_messages() == messages


def test_to_chat_messages_with_summary():
    messages = [HumanMessage(content="nowe pytanie")]
    context = ConversationContext(summary="stare rzeczy", messages=messages)

    result = context.to_chat_messages()

    assert isinstance(result[0], SystemMessage)
    assert "stare rzeczy" in result[0].content
    assert result[1:] == messages
