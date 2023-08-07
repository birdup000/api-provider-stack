import requests
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

class APIClient:
    def __init__(self):
        self.endpoints = {}
        self.api_keys = {}
        self.provider_index = 0

    def add_endpoint(self, name, url, requires_api_key=False):
        self.endpoints[name] = {'url': url, 'requires_api_key': requires_api_key}

    def set_api_key(self, endpoint_name, api_key):
        self.api_keys[endpoint_name] = api_key

    def rotate_provider(self):
        self.provider_index = (self.provider_index + 1) % len(self.endpoints)

    def make_request(self, endpoint_name, method, payload=None, headers=None):
        if endpoint_name not in self.endpoints:
            raise ValueError("Invalid endpoint name")

        endpoint = self.endpoints[endpoint_name]
        requires_api_key = endpoint['requires_api_key']

        if requires_api_key and endpoint_name not in self.api_keys:
            raise ValueError("API key is required for this endpoint")

        url = endpoint['url']
        api_key = self.api_keys.get(endpoint_name)

        if method == 'GET':
            response = requests.get(url, params=payload, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=payload, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=payload, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, params=payload, headers=headers)
        else:
            raise ValueError("Invalid request method")

        # Handle response and return the result
        return response

app = FastAPI()
client = APIClient()

# Add OpenAI endpoint
client.add_endpoint('openai', 'https://api.openai.com/v1', requires_api_key=True)

# Set OpenAI API key
client.set_api_key('openai', 'YOUR_OPENAI_API_KEY')

@app.post("/v1/chat/completions")
async def chat_completion(model: str, messages: list, max_tokens: Optional[int] = None, temperature: Optional[float] = None):
    # Rotate the provider
    client.rotate_provider()

    # Get the endpoint URL for the current provider
    endpoint_url = client.endpoints[list(client.endpoints.keys())[client.provider_index]]['url']

    # Make the OpenAI request
    response = client.make_request('openai', 'POST', {
        "model": model,
        "prompt": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }, headers={"Authorization": f"Bearer {client.api_keys['openai']}"})

    # Return the response
    return response.json()
