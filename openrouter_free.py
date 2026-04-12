"""
OpenRouter Free Models Library
ONLY uses free models - no paid models
"""

import os
import requests
from typing import Optional, Dict, Any, List

BASE_URL = "https://openrouter.ai/api/v1"

# ONLY free models - all have :free suffix
FREE_MODELS = {
    "auto": "openrouter/free",  # Free router - auto selects best free model
    "deepseek_r1": "deepseek/deepseek-r1:free",
    "llama_3_3_70b": "meta-llama/llama-3.3-70b-instruct:free",
    "llama_3_2_3b": "meta-llama/llama-3.2-3b-instruct:free",
    "qwen3_80b": "qwen/qwen3-next-80b-a3b-instruct:free",
    "qwen3_coder": "qwen/qwen3-coder:free",
    "gemma_4_31b": "google/gemma-4-31b-it:free",
    "gemma_4_27b": "google/gemma-4-26b-a4b-it:free",
    "mistral_small": "mistralai/mistral-small-3.1-24b:free",
    "nemotron_nano": "nvidia/nemotron-3-nano-30b-a3b:free",
}


class OpenRouterFree:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENROUTER_API_KEY env var or pass api_key"
            )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-project",
            "X-Title": "Your App Name",
        }

    def chat(
        self,
        message: str,
        model: str = "auto",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Dict[str, Any]:
        model_id = FREE_MODELS.get(model, model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "content": data["choices"][0]["message"]["content"],
            "model": data["model"],
            "usage": data.get("usage", {}),
            "raw": data,
        }

    def chat_stream(
        self,
        message: str,
        model: str = "auto",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ):
        model_id = FREE_MODELS.get(model, model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs,
        }

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=self.headers,
            json=payload,
            stream=True,
            timeout=60,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json

                    chunk = json.loads(data)
                    if "choices" in chunk and chunk["choices"]:
                        content = (
                            chunk["choices"][0].get("delta", {}).get("content", "")
                        )
                        if content:
                            yield content

    def list_models(self) -> List[str]:
        return list(FREE_MODELS.keys())


if __name__ == "__main__":
    client = OpenRouterFree()
    print("Available models:", client.list_models())

    result = client.chat("Say hello in one sentence", model="deepseek_r1")
    print(f"Model: {result['model']}")
    print(f"Response: {result['content']}")
