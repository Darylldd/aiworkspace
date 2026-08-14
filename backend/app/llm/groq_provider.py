import json
import os
from collections.abc import AsyncIterator

from groq import AsyncGroq, BadRequestError

from app.llm.base import LLMProvider
from app.tools.registry import ToolRegistry

DEFAULT_MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = (
    "You have access to real, working tools for checking the time, "
    "listing files, reading files, and searching files. These are "
    "genuine function calls that execute real code, not simulated or "
    "hypothetical. When a task requires current information or file "
    "access, call the appropriate tool rather than guessing, refusing, "
    "or generating placeholder content. If a tool call is rejected or "
    "returns an error, report that error honestly rather than "
    "inventing plausible-looking output."
)


class GroqProvider(LLMProvider):
    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to backend/.env"
            )
        self._client = AsyncGroq(api_key=api_key)
        self._tool_registry = tool_registry

    async def complete(self, message: str) -> str:
        response = await self._client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": message}],
        )
        return response.choices[0].message.content or ""

    async def stream(self, message: str) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": message}],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def complete_with_tools(self, message: str) -> str:
        if self._tool_registry is None:
            return await self.complete(message)

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]

        response_message = await self._create_completion_with_retry(
            messages, use_tools=True
        )

        if not response_message.tool_calls:
            return response_message.content or ""

        messages.append(response_message.model_dump(exclude_none=True))

        for tool_call in response_message.tool_calls:
            tool = self._tool_registry.get(tool_call.function.name)
            if tool is None:
                result = f"Error: tool '{tool_call.function.name}' not found"
            else:
                raw_arguments = tool_call.function.arguments
                parsed_arguments = (
                    json.loads(raw_arguments) if raw_arguments else {}
                )
                arguments = (
                    parsed_arguments
                    if isinstance(parsed_arguments, dict)
                    else {}
                )
                result = await tool.execute(**arguments)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

        final_message = await self._create_completion_with_retry(
            messages, use_tools=False
        )
        return final_message.content or ""

    async def _create_completion_with_retry(
        self, messages: list[dict], use_tools: bool
    ):
        kwargs = {"model": DEFAULT_MODEL, "messages": messages}
        if use_tools and self._tool_registry is not None:
            kwargs["tools"] = self._tool_registry.to_groq_schemas()

        try:
            response = await self._client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except BadRequestError as error:
            if "tool_use_failed" not in str(error):
                raise

            retry_kwargs = dict(kwargs)
            retry_kwargs["temperature"] = 0.3
            response = await self._client.chat.completions.create(
                **retry_kwargs
            )
            return response.choices[0].message

    async def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        transcription = await self._client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3-turbo",
        )
        return transcription.text