import asyncio
from http.client import HTTPException
import httpx
import json
import logging
from cachetools import TTLCache
from backoff import expo, on_exception
from httpx import HTTPStatusError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self, base_url, cache_ttl=3600):
        self.base_url = base_url
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl)

    @on_exception(
        expo,
        (httpx.HTTPStatusError, httpx.TooManyRedirects),
        max_tries=3,
        max_time=300,
        on_giveup=lambda e: logger.error(f"Max retries reached: {e}")
    )
    async def _make_request(self, url, headers):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    logger.warning(f"Rate limit hit. Waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    raise httpx.HTTPStatusError(
                        f"Rate limit exceeded for {url}", request=response.request, response=response
                    )

                if response.status_code == 204:
                    logger.info(f"204 No Content for URL: {url}")
                    return None

                response.raise_for_status()
                return response.json() if response.content else None

            except httpx.HTTPStatusError as e:
                if e.response and e.response.status_code == 429:
                    raise HTTPException(
                        status_code=429,
                        detail="Too Many Requests. Please try again later."
                    )
                raise e

    async def get_photo_by_tin(self, tin):
        if tin in self.cache:
            logger.info(f"Cache hit for TIN: {tin}")
            return self.cache[tin]

        url = f"{self.base_url}/api/Registration/GetRegistrationInfoByTin/{tin}/en"
        headers = self._get_headers()

        try:
            response = await self._make_request(url, headers)
            if not response:
                return None

            logger.info("raw_data: %s", response)

            # Extract Photo
            photo = ""
            try:
                photo = response.get("AssociateShortInfos", [{}])[0].get("Photo", "")
            except (IndexError, AttributeError, TypeError) as e:
                logger.warning(f"Photo extraction failed: {e}")

            logger.info(f"Photo for TIN {tin}: {photo}")
            self.cache[tin] = photo
            return photo

        except HTTPStatusError as e:
            logger.error(f"Request failed for TIN {tin}: {e}")
            return None

    def _get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://etrade.gov.et/business-license-checker',
        }

# Run this part to test
if __name__ == "__main__":
    async def main():
        scraper = Scraper(base_url="https://etrade.gov.et")
        tin = "0071308693"  # Replace with any TIN you want
        photo = await scraper.get_photo_by_tin(tin)
        print("\n Extracted Photo:", photo)

    asyncio.run(main())