from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from client.ollama_client import OllamaWrapper

local_ollama: OllamaWrapper = OllamaWrapper()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await local_ollama.ensure_running()
    # Load the ML model
    await local_ollama.pull_models(
        ["deepseek-r1"]
    )
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat_with_model(prompt: str, agent: str):
    response : ChatResponse = await local_ollama.generate_chat_response(
        prompt=prompt,
        agent=agent
    )
    return response

@app.post("/chatstream")
async def stream_chat_with_model(prompt: str, agent: str):
    print(f"received chat request with {agent} on prompt {prompt}")
    stream_list = [stream for stream in await chat_streamer(
        prompt=prompt,
        agent=agent
    )]
    print([stream.response for stream in stream_list])
    return {"stream" : stream_list}
        

@app.get("/models")
async def get_models():
    return await local_ollama.get_models()

async def chat_streamer(prompt: str, agent: str) -> list[any]:
    stream = local_ollama.stream_response(
        prompt=prompt,
        agent=agent
    )
    output = list()
    async for chunk in stream:
        output.append(chunk)
    return output