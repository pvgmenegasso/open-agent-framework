import asyncio
from os import popen
from typing import AsyncIterator, ClassVar, TextIO
from pydantic import BaseModel, ConfigDict
from httpx import AsyncClient
from client.model import Model
import logging

logger = logging.getLogger(__name__)

class OllamaError(Exception):
    pass    



class OllamaWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


    output: ClassVar[TextIO]
    models:  ClassVar[dict[str, Model]]
    ollama_client: ClassVar[AsyncClient | None] = None
    

    @classmethod
    async def is_running(
        cls,
        retries: int = 5,
        delay: float = 1.0 
    ) -> None:
        for attempt in range(1, retries + 1):
            try:
                response = await cls.ollama_client.get("/")
                if response.status_code == 200:
                    logger.info("Ollama is already running.")
                    return
            except httpx.TransportError:
                pass
            await asyncio.sleep(delay)
        raise OllamaError(
            f"Ollama is not running after {retries} attempts. Please start Ollama and try again."
        )
            
    @classmethod
    async def get_models(cls) -> dict[str, Model]:
        response = await cls.ollama_client.get("/api/tags")
        response.raise_for_status()
        models_raw = response.text.splitlines()
        response_objs : dict[str, Model] = {}
        for line in models_raw[1:]:
            split_line = line.split()
            # Need to concatenate some fields which are made up of multiple strings !
            split_line = [*split_line[:2],split_line[2]+split_line[3], " ".join(split_line[4:])]
            model = Model(
                name=split_line[0],
                id = split_line[1],
                size= split_line[2],
                modified=split_line[3]
            )
            response_objs[model.name] = model
        return response_objs

    @classmethod
    async def pull_models(cls, models: list[str]):
        for model in models:
            async with cls.client.stream(
                "POST",
                 "/api/pull", 
                 json={"model": model}
            ) as response:
                response.raise_for_status(context=f"pull model '{model}'")
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    status = data.get("status", "")
                    if "error" in data:
                        raise OllamaError(f"Pull failed for '{model}': {data['error']}")
                    if status:
                        logger.debug("[pull %s] %s", model, status)
            logger.info("Model '%s' ready.", model)

    async def get_models(self) -> dict[str, Model]:
        models: dict[str, Model]
        try:
            models = OllamaWrapper.models
        except Exception as e:
            print(e)
        return await OllamaWrapper.get_models()

    async def pull_models(self, model_list: list[str]):
        for model in model_list:
            await self.ollama_client.pull(model)

    async def get_running_models(self):
        response: ProcessResponse
        response = await self.ollama_client.ps()
        print(response)

        # ------------------------------------------------------------------
    # Chat (non-streaming)
    # ------------------------------------------------------------------

    async def generate_chat_response(
        self,
        prompt: str,
        agent: str,
        history: list[dict] | None = None,
    ) -> dict:
        """
        Send a chat request and return the full response dict.

        POST /api/chat with stream=false.
        """
        messages = _build_messages(prompt=prompt, agent=agent, history=history)
        payload = {
            "model": agent,
            "messages": messages,
            "stream": False,
        }
        response = await self.client.post("/api/chat", json=payload)
        _raise_for_status(response, context=f"chat with model '{agent}'")
        return response.json()

    # ------------------------------------------------------------------
    # Streaming generate
    # ------------------------------------------------------------------

    async def stream_response(
        self,
        prompt: str,
        agent: str,
    ) -> AsyncIterator[dict]:
        """
        Yield response chunks from POST /api/generate with stream=true.

        Each yielded value is a parsed JSON dict matching Ollama's
        GenerateResponse shape.
        """
        payload = {
            "model": agent,
            "prompt": prompt,
            "stream": True,
        }
        async with self.client.stream(
            "POST",
            "/api/generate",
            json=payload,
            timeout=None,
        ) as response:
            _raise_for_status(response, context=f"stream from model '{agent}'")
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Could not parse stream chunk: %r", line)
                    continue
                if "error" in chunk:
                    raise OllamaError(chunk["error"])
                yield chunk
                if chunk.get("done"):
                    break


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _build_messages(
    prompt: str,
    agent: str,
    history: list[dict] | None,
) -> list[dict]:
    """Construct the messages array for /api/chat."""
    messages: list[dict] = []
    # Optionally prepend a system prompt derived from the agent name.
    # Extend this to load from config.json if you define per-agent personas.
    messages.append({"role": "system", "content": f"You are {agent}, a helpful AI assistant."})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})
    return messages