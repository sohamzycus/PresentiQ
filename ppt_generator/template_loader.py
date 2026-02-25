"""
PPT Template Preset Loader - Load from YAML config files

Supports loading custom PPT template presets from configs/templates/ directory.
Users can create custom templates by adding new YAML files without modifying code.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class TemplateLoader:
    """
    Template preset loader

    Loads YAML-format template preset files from configs/templates/ directory.
    Supports hot reload and caching.

    YAML template format example:
    ```yaml
    name: "Template Name"
    description: "Template description"
    sequence:
      - title
      - content
      - conclusion_cta
    narrative: "problem_solution_result"
    suggested_slides: 5
    style_hints:  # optional
      background: "Background description"
      typography: "Font description"
      colors:
        - "#000000"
        - "#FFFFFF"
      layout: "Layout description"
      visual: "Visual elements description"
      special: "Special requirements"  # optional
    ```
    """

    def __init__(self, config_dir: str = None):
        """
        Initialize template loader

        Args:
            config_dir: Config directory path. If None, uses configs/templates under project root
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default: look for configs/templates under project root
            self.config_dir = Path(__file__).parent.parent / "configs" / "templates"

        self._cache: Dict[str, Dict] = {}
        self._loaded = False

    def load_all(self) -> Dict[str, Dict]:
        """
        Load all template presets

        Returns:
            Dict[str, Dict]: Template preset dict, key is template name (filename), value is template config
        """
        if self._loaded:
            return self._cache

        if not self.config_dir.exists():
            logger.warning(f"Template config directory does not exist: {self.config_dir}")
            return {}

        for yaml_file in sorted(self.config_dir.glob("*.yaml")):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    preset = yaml.safe_load(f)
                    if preset is None:
                        logger.warning(f"Empty template file: {yaml_file}")
                        continue

                    key = yaml_file.stem  # Filename as key
                    self._cache[key] = preset
                    logger.debug(f"Loaded template: {key} - {preset.get('name', 'Unnamed')}")

            except yaml.YAMLError as e:
                logger.error(f"YAML parse error {yaml_file}: {e}")
            except Exception as e:
                logger.error(f"Failed to load template {yaml_file}: {e}")

        self._loaded = True
        logger.info(f"Loaded {len(self._cache)} template presets")
        return self._cache

    def get_preset(self, name: str) -> Optional[Dict]:
        """
        Get template preset by name

        Args:
            name: Template name (corresponds to YAML filename without extension)

        Returns:
            Template config dict, or None if not found
        """
        self.load_all()
        return self._cache.get(name)

    def list_presets(self) -> List[Dict]:
        """
        List all available template presets

        Returns:
            List[Dict]: Preset list, each item contains key, name, description
        """
        self.load_all()
        return [
            {
                "key": k,
                "name": v.get("name", k),
                "description": v.get("description", "")
            }
            for k, v in self._cache.items()
        ]

    def reload(self) -> Dict[str, Dict]:
        """
        Reload all templates (supports hot update)

        Returns:
            Dict[str, Dict]: Reloaded template preset dict
        """
        self._cache.clear()
        self._loaded = False
        logger.info("Reloading template presets...")
        return self.load_all()

    def add_template_dir(self, extra_dir: str) -> None:
        """
        Add extra template directory (for loading user custom templates)

        Args:
            extra_dir: Extra template directory path
        """
        extra_path = Path(extra_dir)
        if not extra_path.exists():
            logger.warning(f"Extra template directory does not exist: {extra_dir}")
            return

        for yaml_file in sorted(extra_path.glob("*.yaml")):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    preset = yaml.safe_load(f)
                    if preset:
                        key = yaml_file.stem
                        self._cache[key] = preset
                        logger.info(f"Loaded extra template: {key}")
            except Exception as e:
                logger.error(f"Failed to load extra template {yaml_file}: {e}")

    def register_dynamic_template(self, key: str, template: Dict) -> None:
        """
        Register a dynamically generated template at runtime (not persisted to disk).

        Args:
            key: Template key (used as template_preset value)
            template: Template config dict with name, description, sequence, style_hints, etc.
        """
        self.load_all()
        self._cache[key] = template
        logger.info(f"Registered dynamic template: {key} — {template.get('name', key)}")


# Global singleton
_loader: Optional[TemplateLoader] = None


def get_template_loader(config_dir: str = None) -> TemplateLoader:
    """
    Get template loader singleton

    Args:
        config_dir: Config directory path (only effective on first call)

    Returns:
        TemplateLoader: Template loader instance
    """
    global _loader
    if _loader is None:
        _loader = TemplateLoader(config_dir)
    return _loader


def get_template_presets() -> Dict[str, Dict]:
    """
    Get all template presets

    Compatible with original TEMPLATE_PRESETS usage, returns same format dict.

    Returns:
        Dict[str, Dict]: Template preset dict
    """
    return get_template_loader().load_all()


def reload_templates() -> Dict[str, Dict]:
    """
    Reload all templates

    Returns:
        Dict[str, Dict]: Reloaded template preset dict
    """
    return get_template_loader().reload()


def register_dynamic_template(key: str, template: Dict) -> None:
    """
    Register a dynamic template at runtime.

    Args:
        key: Template key
        template: Template config dict
    """
    get_template_loader().register_dynamic_template(key, template)
