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
        try:
            # Check if suggestion exists in cache
            cached = get_cached_suggestion(prompt)
            if cached:
                logger.debug("Cache hit for prompt.")
                return cached

            # Prepare headers and payload for the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            # The 'messages' field is required for Chat Completions API
            payload = {
                "model": "gpt-4o-mini",  # Specify the correct model name
                "messages": [
                    {"role": "user", "content": prompt}  # Use 'messages' for input prompt
                ],
                "max_tokens": 1024,
                "temperature": 0.2,
                "n": 1,
                "stop": None
            }

            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=payload) as response:
                    if response.status == 429:
                        # Handle rate limit exceeded
                        logger.warning("API rate limit exceeded. Retrying after delay.")
                        await asyncio.sleep(5)  # Wait for 5 seconds before retrying
                        return await self.fetch_suggestion(prompt)  # Retry
                    elif response.status != 200:
                        # Log error if request fails
                        error_text = await response.text()
                        logger.error(f"API request failed with status {response.status}: {error_text}")
                        return f"Error: {response.status} - {error_text}"

                    # Parse and return the suggestion from the API response
                    data = await response.json()
                    suggestion = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    set_cached_suggestion(prompt, suggestion)  # Cache the result
                    logger.debug("Suggestion fetched and cached.")
                    return suggestion

        except aiohttp.ClientError as e:
            # Log exception if the API request fails
            logger.exception("API request failed.")
            return f"Error: {str(e)}"
