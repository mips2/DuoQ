# api_client.py

import aiohttp
import asyncio
from config import Config
from cache_manager import get_cached_suggestion, set_cached_suggestion
from logger import logger

class APIClient:
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.endpoint = Config.API_ENDPOINT
        if not self.api_key:
            logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            raise ValueError("OpenAI API key not found.")

    async def fetch_suggestion(self, prompt):
        cached = get_cached_suggestion(prompt)
        if cached:
            logger.debug("Cache hit for prompt.")
            return cached

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "prompt": prompt,
            "max_tokens": 150,
            "temperature": 0.2,
            "n": 1,
            "stop": None
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.endpoint, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API request failed with status {response.status}: {error_text}")
                        return f"Error: {response.status} - {error_text}"
                    data = await response.json()
                    suggestion = data.get('choices', [{}])[0].get('text', '').strip()
                    set_cached_suggestion(prompt, suggestion)
                    logger.debug("Suggestion fetched and cached.")
                    return suggestion
            except aiohttp.ClientError as e:
                logger.exception("API request failed.")
                return f"Error: {str(e)}"
