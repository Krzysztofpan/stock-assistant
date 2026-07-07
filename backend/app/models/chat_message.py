from langchain_core.messages import AIMessage, HumanMessage

from app.tortoise.models.messages import Message, MessageRole

ChatMessage = HumanMessage | AIMessage


def message_from_payload(payload: dict) -> ChatMessage:
    text = payload["text"]
    if payload["role"] == "user":
        return HumanMessage(content=text)
    return AIMessage(content=text)


def message_from_model(message: Message) -> ChatMessage:
    if message.role == MessageRole.USER:
        return HumanMessage(content=message.text)
    return AIMessage(content=message.text)