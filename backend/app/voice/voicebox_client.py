import json

import httpx

VOICEBOX_BASE_URL = "http://127.0.0.1:17493"
STREAM_TIMEOUT_SECONDS = 120.0


class VoiceboxGenerationError(Exception):
    pass


class VoiceboxClient:
    def __init__(self, base_url: str = VOICEBOX_BASE_URL) -> None:
        self._base_url = base_url

    async def list_profiles(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._base_url}/profiles")
            response.raise_for_status()
            return response.json()

    async def speak(self, text: str, profile: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/speak",
                json={"text": text, "profile": profile},
                headers={"X-Voicebox-Client-Id": "ai-workspace"},
            )
            response.raise_for_status()
            generation_id = response.json()["id"]

        return await self._stream_until_complete(generation_id)

    async def _stream_until_complete(self, generation_id: str) -> dict:
        url = f"{self._base_url}/generate/{generation_id}/status"

        async with httpx.AsyncClient(timeout=STREAM_TIMEOUT_SECONDS) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    payload = json.loads(line.removeprefix("data: "))

                    if payload["status"] == "completed":
                        return payload
                    if payload["status"] == "failed":
                        raise VoiceboxGenerationError(
                            payload.get("error")
                            or "Generation failed with no error message"
                        )

        raise VoiceboxGenerationError(
            f"Stream for generation {generation_id} ended without a terminal status"
        )

    async def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/transcribe",
                files={"file": (filename, audio_bytes)},
            )
            response.raise_for_status()
            return response.json()["text"]