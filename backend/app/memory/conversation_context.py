from dataclasses import dataclass

from langchain_core.messages import BaseMessage, SystemMessage

from app.models.chat_message import ChatMessage


@dataclass
class ConversationContext:
    summary: str | None
    messages: list[ChatMessage]

    def to_chat_messages(self) -> list[BaseMessage]:
        if not self.summary:
            return list(self.messages)

        return [
            SystemMessage(
                content=(
                    "Summary of the earlier part of the conversation. "
                    "Use it as historical context:\n"
                    f"{self.summary}"
                )
            ),
            *self.messages,
        ]
