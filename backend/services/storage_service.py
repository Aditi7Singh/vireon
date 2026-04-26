import os
import uuid
from typing import Optional

UPLOADS_DIR = os.getenv("UPLOADS_DIR", "data/uploads")


class LocalStorage:
    """Local filesystem storage backend for development environments."""

    def __init__(self):
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR)

    def save_file(self, content: bytes, filename: str) -> str:
        """Saves file and returns a storage URI."""
        safe_name = f"{uuid.uuid4()}_{filename}"
        path = os.path.join(UPLOADS_DIR, safe_name)
        with open(path, "wb") as f:
            f.write(content)
        return f"storage://vireon-docs/{safe_name}"

    def to_public_url(self, storage_uri: str) -> str:
        return storage_uri


class S3Storage:
    """Optional S3 backend for production deployments.

    This backend is enabled only when `STORAGE_BACKEND=s3` and boto3 is available.
    """

    def __init__(self):
        import boto3

        self.bucket = os.getenv("S3_BUCKET")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.prefix = os.getenv("S3_PREFIX", "documents")
        if not self.bucket:
            raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        self.client = boto3.client("s3", region_name=self.region)

    def save_file(self, content: bytes, filename: str) -> str:
        safe_name = f"{uuid.uuid4()}_{filename}"
        key = f"{self.prefix}/{safe_name}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return f"s3://{self.bucket}/{key}"

    def to_public_url(self, storage_uri: str) -> str:
        # Best effort virtual-hosted URL; private buckets should use signed URLs in a future step.
        path = storage_uri.replace("s3://", "")
        bucket, _, key = path.partition("/")
        return f"https://{bucket}.s3.{self.region}.amazonaws.com/{key}"


def _build_storage():
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend == "s3":
        try:
            return S3Storage()
        except Exception:
            # Fall back to local storage so uploads remain available in dev and CI.
            return LocalStorage()
    return LocalStorage()

storage = _build_storage()
