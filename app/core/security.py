import os
import re
import uuid
from pathlib import Path
from typing import List, Optional, Union
from fastapi import HTTPException, status
from app.core.config import settings


class SecurityException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class FileSizeExceededException(HTTPException):
    def __init__(self, detail: str = "File size exceeds allowed maximum limit."):
        super().__init__(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail)


class InvalidFileException(HTTPException):
    def __init__(self, detail: str = "Invalid file format or corrupted file."):
        super().__init__(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=detail)


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes an uploaded filename to prevent directory traversal and invalid characters.
    Generates a secure UUID-prefixed clean filename.
    """
    if not filename:
        return f"{uuid.uuid4().hex}.tif"

    # Strip any directory paths
    base_name = os.path.basename(filename)
    
    # Remove path traversal characters
    base_name = base_name.replace("..", "").replace("/", "").replace("\\", "")

    # Extract extension
    parts = base_name.rsplit(".", 1)
    if len(parts) == 2:
        name_part, ext_part = parts
        ext = f".{ext_part.lower()}"
    else:
        name_part = parts[0]
        ext = ".tif"

    # Clean the name part
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name_part).strip("_")
    if not clean_name:
        clean_name = "raster"

    # Prepend UUID for absolute uniqueness
    unique_id = uuid.uuid4().hex[:8]
    return f"{unique_id}_{clean_name}{ext}"


def validate_file_extension(filename: str, allowed_extensions: Optional[List[str]] = None) -> str:
    """
    Validates that the file extension is allowed.
    Returns the lowercased extension.
    """
    allowed = allowed_extensions or settings.ALLOWED_EXTENSIONS
    suffix = Path(filename).suffix.lower()

    if not suffix or suffix not in allowed:
        raise InvalidFileException(
            f"File extension '{suffix}' is not supported. Allowed extensions: {', '.join(allowed)}"
        )

    return suffix


def validate_file_size(size_bytes: int, max_mb: Optional[int] = None) -> None:
    """
    Validates that the file size is within acceptable limits.
    """
    max_allowed = (max_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    if size_bytes > max_allowed:
        raise FileSizeExceededException(
            f"File size {size_bytes / (1024 * 1024):.1f}MB exceeds the maximum limit of {max_mb or settings.MAX_UPLOAD_SIZE_MB}MB."
        )


def validate_safe_path(requested_path: Union[str, Path], allowed_base_dirs: Optional[List[Union[str, Path]]] = None) -> Path:
    """
    Validates that a requested file path does not attempt directory traversal
    and resides strictly within one of the whitelisted base directories.
    """
    path_str = str(requested_path)
    if ".." in path_str or "\x00" in path_str:
        raise SecurityException("Directory traversal attack detected in file path.")

    resolved_path = Path(path_str).resolve()

    if allowed_base_dirs:
        resolved_bases = [Path(b).resolve() for b in allowed_base_dirs]
        is_safe = any(
            resolved_path == b or b in resolved_path.parents
            for b in resolved_bases
        )
        if not is_safe:
            raise SecurityException(f"Access to path outside allowed storage directories is forbidden: {resolved_path.name}")

    return resolved_path

