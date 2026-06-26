import os
import uuid
import httpx
from datetime import datetime
from typing import Optional, List, Dict
from minio import Minio
from io import BytesIO

from backend.config import settings


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def save_screenshot(self, page, listing_id: str) -> Optional[str]:
        path = f"screenshots/{listing_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        try:
            screenshot_bytes = await page.screenshot(full_page=True)
            self.client.put_object(
                self.bucket,
                path,
                BytesIO(screenshot_bytes),
                length=len(screenshot_bytes),
                content_type="image/png",
            )
            return path
        except Exception as e:
            print(f"Screenshot save error: {e}")
            return None

    async def save_html(self, page, listing_id: str) -> Optional[str]:
        path = f"html/{listing_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
        try:
            html = await page.content()
            self.client.put_object(
                self.bucket,
                path,
                BytesIO(html.encode()),
                length=len(html.encode()),
                content_type="text/html",
            )
            return path
        except Exception as e:
            print(f"HTML save error: {e}")
            return None

    async def download_image(self, url: str, listing_id: str, index: int = 0) -> Optional[Dict]:
        path = f"images/{listing_id}/{index}.jpg"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.content
                    self.client.put_object(
                        self.bucket,
                        path,
                        BytesIO(data),
                        length=len(data),
                        content_type=resp.headers.get("content-type", "image/jpeg"),
                    )
                    return {
                        "original_url": url,
                        "storage_path": path,
                        "file_size": len(data),
                        "content_type": resp.headers.get("content-type", "image/jpeg"),
                    }
        except Exception as e:
            print(f"Image download error for {url}: {e}")
        return None

    def get_url(self, path: str) -> str:
        if not path:
            return ""
        if settings.minio_secure:
            return f"https://{settings.minio_endpoint}/{self.bucket}/{path}"
        return f"http://{settings.minio_endpoint}/{self.bucket}/{path}"


storage_service = StorageService()
