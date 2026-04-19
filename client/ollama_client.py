import asyncio
from os import popen
from typing import AsyncIterator, ClassVar, TextIO
from pydantic import BaseModel, ConfigDict
from ollama import AsyncClient, GenerateResponse,  ProcessResponse,  chat, ChatResponse
from client.model import Model



class OllamaWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


    output: ClassVar[TextIO]
    models:  ClassVar[list[Model]]
    ollama_client: ClassVar[AsyncClient] = AsyncClient()
    

    @classmethod
    async def ensure_running(cls):
        try:
            if await cls.__is_running():
                return
            await asyncio.create_subprocess_shell(
                "ollama serve",
                stdout=cls.output
            )
            # wait briefly for server to come up
            for _ in range(10):
                await asyncio.sleep(0.5)
                if await cls.__is_running():
                    print("Ollama started successfully.")
                    print(cls.output.read())
                    return
        except FileNotFoundError:
            raise RuntimeError("Ollama binary not found. Install it first.")
        except Exception as exc:
            print(exc)
    @classmethod
    async def __is_running(cls) -> bool:
        is_running:bool = False
        try:
            cls.__get_models()
            is_running = True
        except Exception as exc:
            print(exc)
            is_running = False
        finally:
            return is_running
    @classmethod
    def __get_models(cls):
        models_raw = popen(
            cmd="ollama list"
        ).readlines()
        response_objs : list[Model] = list()
        for line in models_raw[1:]:
            split_line = line.split()
            # Need to concatenate some fields which are made up of multiple strings !
            split_line = [*split_line[:2],split_line[2]+split_line[3], " ".join(split_line[4:])]
            response_objs.append(
                Model(
                    name=split_line[0],
                    id = split_line[1],
                    size= split_line[2],
                    modified=split_line[3]
                )
            )
        cls.models = response_objs

    async def get_models(self) -> list[Model]:
        models: list[Model]
        try:
            models = OllamaWrapper.models
        except Exception as e:
            print(e)
            OllamaWrapper.__get_models()
            models = OllamaWrapper.models
        return models
    async def pull_models(self, model_list: list[str]):
        for model in model_list:
            await self.ollama_client.pull(model)
    async def get_running_models(self):
        response: ProcessResponse
        response = await self.ollama_client.ps()
        print(response)

    async def stream_response(self, prompt: str, agent: str):
        response_stream: AsyncIterator[GenerateResponse] = await self.ollama_client.generate(
            model=agent,
            prompt=prompt,
            stream=True
        )
        async for response in response_stream:
            yield response


    async def generate_chat_response(self, prompt: str, agent:  str) -> ChatResponse:
        current_models  = await self.get_models()
        model_names = [model.name.split(":")[0] for model in current_models]
        if agent in model_names:
            return chat(
                model=agent,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
        else:
            raise AttributeError(f"Agent {agent} not found")