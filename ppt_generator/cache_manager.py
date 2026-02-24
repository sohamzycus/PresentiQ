"""
Cache Manager - PPT generation cache

Main features:
1. Outline cache - Avoid regenerating identical outlines
2. Image cache - Cache generated slide images
3. Incremental update - Only regenerate changed pages
4. Auto cleanup - Periodically clean expired cache
"""

import hashlib
import json
import os
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheManager:
    """PPT generation cache manager"""

    def __init__(
        self,
        cache_dir: str = ".cache/ppt_generator",
        cache_ttl_days: int = 7
    ):
        """
        Initialize cache manager

        Args:
            cache_dir: Cache directory
            cache_ttl_days: Cache TTL in days
        """
        self.cache_dir = Path(cache_dir)
        self.outline_cache_dir = self.cache_dir / "outlines"
        self.image_cache_dir = self.cache_dir / "images"
        self.metadata_file = self.cache_dir / "metadata.json"
        self.cache_ttl = timedelta(days=cache_ttl_days)

        # Create cache directories
        self._ensure_cache_dirs()

        # Load metadata
        self.metadata = self._load_metadata()

    def _ensure_cache_dirs(self):
        """Ensure cache directories exist"""
        self.outline_cache_dir.mkdir(parents=True, exist_ok=True)
        self.image_cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> Dict:
        """Load cache metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        return {"version": "1.0", "entries": {}}

    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def _compute_hash(self, *args) -> str:
        """Compute cache key hash"""
        combined = "||".join(str(arg) for arg in args)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    # ==================== Outline cache ====================

    def get_cached_outline(
        self,
        reference_text: str,
        style_requirements: str,
        model: str
    ) -> Optional[Dict]:
        """
        Get cached outline

        Args:
            reference_text: Reference text
            style_requirements: Style requirements
            model: Model used

        Returns:
            Optional[Dict]: Cached outline, or None if not found or expired
        """
        cache_key = self._compute_hash(reference_text, style_requirements, model)
        cache_file = self.outline_cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            logger.debug(f"Outline cache miss: {cache_key}")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check if expired
            cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
            if datetime.now() - cached_time > self.cache_ttl:
                logger.info(f"Outline cache expired: {cache_key}")
                cache_file.unlink()  # Remove expired cache
                return None

            logger.info(f"Outline cache hit: {cache_key}")
            return cached.get('outline')

        except Exception as e:
            logger.warning(f"Failed to read outline cache: {e}")
            return None

    def cache_outline(
        self,
        reference_text: str,
        style_requirements: str,
        model: str,
        outline: Dict
    ):
        """
        Cache outline

        Args:
            reference_text: Reference text
            style_requirements: Style requirements
            model: Model used
            outline: Generated outline
        """
        cache_key = self._compute_hash(reference_text, style_requirements, model)
        cache_file = self.outline_cache_dir / f"{cache_key}.json"

        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'model': model,
            'text_hash': self._compute_hash(reference_text),
            'style_hash': self._compute_hash(style_requirements),
            'outline': outline
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            # Update metadata
            self.metadata["entries"][cache_key] = {
                "type": "outline",
                "created_at": cache_data['cached_at'],
                "file": str(cache_file)
            }
            self._save_metadata()

            logger.info(f"Outline cached: {cache_key}")

        except Exception as e:
            logger.error(f"Failed to cache outline: {e}")

    # ==================== Image cache ====================

    def get_cached_image(self, prompt_hash: str) -> Optional[str]:
        """
        Get cached image path

        Args:
            prompt_hash: Prompt hash

        Returns:
            Optional[str]: Cached image path, or None if not found
        """
        # Find matching cached image
        for filename in os.listdir(self.image_cache_dir):
            if filename.startswith(prompt_hash):
                cache_path = self.image_cache_dir / filename

                # Check if expired
                mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
                if datetime.now() - mtime > self.cache_ttl:
                    logger.info(f"Image cache expired: {filename}")
                    cache_path.unlink()
                    return None

                logger.info(f"Image cache hit: {filename}")
                return str(cache_path)

        return None

    def cache_image(self, prompt: str, image_path: str) -> str:
        """
        Cache image

        Args:
            prompt: Image generation prompt
            image_path: Original image path

        Returns:
            str: Cached image path
        """
        prompt_hash = self._compute_hash(prompt)
        ext = os.path.splitext(image_path)[1]
        cache_filename = f"{prompt_hash}{ext}"
        cache_path = self.image_cache_dir / cache_filename

        try:
            shutil.copy2(image_path, cache_path)

            # Update metadata
            self.metadata["entries"][prompt_hash] = {
                "type": "image",
                "created_at": datetime.now().isoformat(),
                "file": str(cache_path)
            }
            self._save_metadata()

            logger.info(f"Image cached: {cache_filename}")
            return str(cache_path)

        except Exception as e:
            logger.error(f"Failed to cache image: {e}")
            return image_path

    def get_image_prompt_hash(self, prompt: str) -> str:
        """Get image prompt hash"""
        return self._compute_hash(prompt)

    # ==================== Incremental update ====================

    def get_changed_slides(
        self,
        old_outline: Dict,
        new_outline: Dict
    ) -> List[int]:
        """
        Compare old and new outlines, return indices of slides that need regeneration

        Args:
            old_outline: Old outline
            new_outline: New outline

        Returns:
            List[int]: Indices of slides that need regeneration
        """
        changed_indices = []

        old_slides = old_outline.get('slides', [])
        new_slides = new_outline.get('slides', [])

        for i, new_slide in enumerate(new_slides):
            if i >= len(old_slides):
                # New slide
                changed_indices.append(i)
                continue

            old_slide = old_slides[i]

            # Compare key fields
            if self._slide_changed(old_slide, new_slide):
                changed_indices.append(i)

        logger.info(f"Detected {len(changed_indices)} slides needing regeneration")
        return changed_indices

    def _slide_changed(self, old_slide: Dict, new_slide: Dict) -> bool:
        """Check if slide has changed"""
        # Compare key fields
        key_fields = ['title', 'slide_type', 'key_points', 'content_summary']

        for field in key_fields:
            old_value = old_slide.get(field)
            new_value = new_slide.get(field)

            if old_value != new_value:
                return True

        return False

    def get_cached_slides_for_outline(
        self,
        outline: Dict
    ) -> Dict[int, str]:
        """
        Get cached slide images for outline

        Args:
            outline: Outline

        Returns:
            Dict[int, str]: Slide index -> cached image path mapping
        """
        cached_slides = {}

        for i, slide in enumerate(outline.get('slides', [])):
            # Build cache key for this slide
            slide_key = self._compute_hash(
                slide.get('title', ''),
                slide.get('slide_type', ''),
                str(slide.get('key_points', []))
            )

            cached_path = self.get_cached_image(slide_key)
            if cached_path:
                cached_slides[i] = cached_path

        return cached_slides

    # ==================== Cache cleanup ====================

    def cleanup_expired(self) -> Dict[str, int]:
        """
        Clean expired cache

        Returns:
            Dict: Cleanup statistics
        """
        stats = {
            "outlines_removed": 0,
            "images_removed": 0,
            "bytes_freed": 0
        }

        now = datetime.now()

        # Clean outline cache
        for cache_file in self.outline_cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)

                cached_time = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
                if now - cached_time > self.cache_ttl:
                    size = cache_file.stat().st_size
                    cache_file.unlink()
                    stats["outlines_removed"] += 1
                    stats["bytes_freed"] += size

            except Exception as e:
                logger.warning(f"Failed to clean outline cache: {cache_file}, {e}")

        # Clean image cache
        for cache_file in self.image_cache_dir.iterdir():
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if now - mtime > self.cache_ttl:
                    size = cache_file.stat().st_size
                    cache_file.unlink()
                    stats["images_removed"] += 1
                    stats["bytes_freed"] += size

            except Exception as e:
                logger.warning(f"Failed to clean image cache: {cache_file}, {e}")

        logger.info(f"Cache cleanup complete: removed {stats['outlines_removed']} outlines, "
                   f"{stats['images_removed']} images, "
                   f"freed {stats['bytes_freed'] / 1024:.2f} KB")

        return stats

    def clear_all(self):
        """Clear all cache"""
        try:
            # Delete all cache files
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)

            # Recreate directories
            self._ensure_cache_dirs()

            # Reset metadata
            self.metadata = {"version": "1.0", "entries": {}}
            self._save_metadata()

            logger.info("All cache cleared")

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict: Cache statistics
        """
        outline_count = len(list(self.outline_cache_dir.glob("*.json")))
        image_count = len(list(self.image_cache_dir.iterdir()))

        outline_size = sum(f.stat().st_size for f in self.outline_cache_dir.glob("*.json"))
        image_size = sum(f.stat().st_size for f in self.image_cache_dir.iterdir())

        return {
            "outline_count": outline_count,
            "image_count": image_count,
            "outline_size_kb": outline_size / 1024,
            "image_size_mb": image_size / (1024 * 1024),
            "total_size_mb": (outline_size + image_size) / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
            "ttl_days": self.cache_ttl.days
        }
