from pathlib import Path
import tempfile
import uuid

import requests


class ImageDownloader:

    def __init__(self, timeout=15):
        self.timeout = timeout

    def download(self, image_urls):
        if not isinstance(image_urls, list):
            return []

        downloaded_files = []

        for url in image_urls:
            if not url:
                continue

            try:
                response = requests.get(
                    url,
                    timeout=self.timeout
                )

                response.raise_for_status()

                content_type = (
                    response.headers.get(
                        "Content-Type",
                        ""
                    ).lower()
                )

                if "image" not in content_type:
                    continue

                suffix = self._get_suffix(
                    content_type
                )

                file_path = (
                    Path(tempfile.gettempdir())
                    / f"toolhunter_{uuid.uuid4().hex}{suffix}"
                )

                file_path.write_bytes(
                    response.content
                )

                if file_path.stat().st_size == 0:
                    file_path.unlink(
                        missing_ok=True
                    )
                    continue

                downloaded_files.append(
                    str(file_path)
                )

            except requests.RequestException:
                continue

            except Exception:
                continue

        return downloaded_files

    def _get_suffix(self, content_type):
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp"
        }

        return mapping.get(
            content_type,
            ".img"
        )
