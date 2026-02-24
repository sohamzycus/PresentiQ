"""
Smart Error Handler - Handles various errors during image generation

Main features:
1. Content policy violation - Auto-replace sensitive words
2. Timeout handling - Simplify prompt and retry
3. API error handling - Exponential backoff retry
4. Fallback - Generate text-only or simple background slides
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error type enum"""
    CONTENT_POLICY = "content_policy"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Recovery action enum"""
    MODIFY_PROMPT = "modify_prompt"
    SIMPLIFY_PROMPT = "simplify_prompt"
    RETRY_WITH_DELAY = "retry_with_delay"
    USE_FALLBACK = "use_fallback"
    ABORT = "abort"


@dataclass
class ErrorAnalysis:
    """Error analysis result"""
    error_type: ErrorType
    severity: str  # "low", "medium", "high", "critical"
    recovery_action: RecoveryAction
    modified_prompt: Optional[str]
    retry_delay: float
    max_retries: int
    should_retry: bool
    fallback_data: Optional[Dict]
    message: str


class SmartErrorHandler:
    """Smart error handler"""

    # Content policy sensitive words and replacements
    SENSITIVE_WORDS = {
        "violence": "peace",
        "war": "cooperation",
        "weapon": "tool",
        "attack": "interact",
        "kill": "resolve",
        "death": "change",
        "blood": "energy",
        "nude": "natural",
        "sexy": "elegant",
        "drug": "substance",
        "gambling": "entertainment"
    }

    # Content policy violation fallback prompts
    CONTENT_POLICY_FALLBACKS = {
        "violence": {
            "modifier": "peaceful, harmonious, collaborative atmosphere",
            "background": "soft gradient background with abstract shapes"
        },
        "adult": {
            "modifier": "professional business environment, corporate setting",
            "background": "clean minimalist background"
        },
        "political": {
            "modifier": "neutral, objective, balanced presentation",
            "background": "subtle geometric pattern background"
        },
        "default": {
            "modifier": "abstract geometric shapes, clean minimal design",
            "background": "simple gradient or solid color background"
        }
    }

    def __init__(self):
        """Initialize error handler"""
        self.error_history: List[Dict] = []

    def analyze_error(
        self,
        error_response: Dict,
        original_prompt: str,
        attempt: int = 0
    ) -> ErrorAnalysis:
        """
        Analyze error and generate recovery strategy

        Args:
            error_response: API error response
            original_prompt: Original prompt
            attempt: Current attempt count

        Returns:
            ErrorAnalysis: Error analysis result
        """
        error_code = error_response.get("code", -1)
        error_message = str(error_response.get("message", "")).lower()
        error_type = self._classify_error(error_code, error_message)

        # Record error history
        self.error_history.append({
            "type": error_type.value,
            "code": error_code,
            "message": error_message,
            "attempt": attempt
        })

        # Generate recovery strategy based on error type
        if error_type == ErrorType.CONTENT_POLICY:
            return self._handle_content_policy_error(original_prompt, attempt)

        elif error_type == ErrorType.TIMEOUT:
            return self._handle_timeout_error(original_prompt, attempt)

        elif error_type == ErrorType.RATE_LIMIT:
            return self._handle_rate_limit_error(original_prompt, attempt)

        elif error_type == ErrorType.API_ERROR:
            return self._handle_api_error(original_prompt, attempt, error_message)

        elif error_type == ErrorType.NETWORK_ERROR:
            return self._handle_network_error(original_prompt, attempt)

        else:
            return self._handle_unknown_error(original_prompt, attempt)

    def _classify_error(self, error_code: int, error_message: str) -> ErrorType:
        """Classify error type"""
        # Gemini API error code
        if error_code == 5:
            return ErrorType.CONTENT_POLICY

        # Timeout keywords
        if any(kw in error_message for kw in ["timeout", "timed out"]):
            return ErrorType.TIMEOUT

        # Rate limit
        if any(kw in error_message for kw in ["rate limit", "too many requests", "429"]):
            return ErrorType.RATE_LIMIT

        # Network error
        if any(kw in error_message for kw in ["connection", "network", "dns"]):
            return ErrorType.NETWORK_ERROR

        # API error (4xx, 5xx)
        if 400 <= error_code < 600:
            return ErrorType.API_ERROR

        return ErrorType.UNKNOWN

    def _handle_content_policy_error(
        self,
        original_prompt: str,
        attempt: int
    ) -> ErrorAnalysis:
        """Handle content policy violation error"""
        # Detect violation type
        violation_type = self._detect_violation_type(original_prompt)
        fallback = self.CONTENT_POLICY_FALLBACKS.get(
            violation_type,
            self.CONTENT_POLICY_FALLBACKS["default"]
        )

        if attempt == 0:
            # First attempt: try replacing sensitive words
            modified_prompt = self._sanitize_prompt(original_prompt)
            return ErrorAnalysis(
                error_type=ErrorType.CONTENT_POLICY,
                severity="high",
                recovery_action=RecoveryAction.MODIFY_PROMPT,
                modified_prompt=modified_prompt,
                retry_delay=0.5,
                max_retries=2,
                should_retry=True,
                fallback_data=None,
                message="Content policy violation detected, replaced sensitive words"
            )

        elif attempt == 1:
            # Second attempt: use abstract description
            abstract_prompt = self._create_abstract_prompt(original_prompt, fallback)
            return ErrorAnalysis(
                error_type=ErrorType.CONTENT_POLICY,
                severity="high",
                recovery_action=RecoveryAction.SIMPLIFY_PROMPT,
                modified_prompt=abstract_prompt,
                retry_delay=1.0,
                max_retries=2,
                should_retry=True,
                fallback_data=None,
                message="Retrying with abstract description"
            )

        else:
            # Third attempt and beyond: use fallback
            return ErrorAnalysis(
                error_type=ErrorType.CONTENT_POLICY,
                severity="critical",
                recovery_action=RecoveryAction.USE_FALLBACK,
                modified_prompt=None,
                retry_delay=0,
                max_retries=0,
                should_retry=False,
                fallback_data={"type": "gradient_fallback", "style": fallback["background"]},
                message="Content policy violation unrecoverable, using fallback"
            )

    def _handle_timeout_error(
        self,
        original_prompt: str,
        attempt: int
    ) -> ErrorAnalysis:
        """Handle timeout error"""
        if attempt < 3:
            # Simplify prompt and retry
            simplified = self._simplify_prompt(original_prompt)
            delay = 2.0 * (attempt + 1)  # Incremental delay

            return ErrorAnalysis(
                error_type=ErrorType.TIMEOUT,
                severity="medium",
                recovery_action=RecoveryAction.SIMPLIFY_PROMPT,
                modified_prompt=simplified,
                retry_delay=delay,
                max_retries=3,
                should_retry=True,
                fallback_data=None,
                message=f"Request timeout, retrying after {delay}s with simplified prompt"
            )
        else:
            return ErrorAnalysis(
                error_type=ErrorType.TIMEOUT,
                severity="high",
                recovery_action=RecoveryAction.USE_FALLBACK,
                modified_prompt=None,
                retry_delay=0,
                max_retries=0,
                should_retry=False,
                fallback_data={"type": "simple_fallback"},
                message="Multiple timeouts, using fallback"
            )

    def _handle_rate_limit_error(
        self,
        original_prompt: str,
        attempt: int
    ) -> ErrorAnalysis:
        """Handle rate limit error"""
        # Exponential backoff
        delay = min(2 ** (attempt + 1), 60)  # Max 60 seconds

        if attempt < 5:
            return ErrorAnalysis(
                error_type=ErrorType.RATE_LIMIT,
                severity="medium",
                recovery_action=RecoveryAction.RETRY_WITH_DELAY,
                modified_prompt=original_prompt,  # Keep original prompt
                retry_delay=delay,
                max_retries=5,
                should_retry=True,
                fallback_data=None,
                message=f"Rate limit triggered, retrying after {delay}s"
            )
        else:
            return ErrorAnalysis(
                error_type=ErrorType.RATE_LIMIT,
                severity="high",
                recovery_action=RecoveryAction.USE_FALLBACK,
                modified_prompt=None,
                retry_delay=0,
                max_retries=0,
                should_retry=False,
                fallback_data={"type": "simple_fallback"},
                message="Rate limit not recovered, using fallback"
            )

    def _handle_api_error(
        self,
        original_prompt: str,
        attempt: int,
        error_message: str
    ) -> ErrorAnalysis:
        """Handle API error"""
        if attempt < 2:
            return ErrorAnalysis(
                error_type=ErrorType.API_ERROR,
                severity="medium",
                recovery_action=RecoveryAction.RETRY_WITH_DELAY,
                modified_prompt=original_prompt,
                retry_delay=3.0,
                max_retries=2,
                should_retry=True,
                fallback_data=None,
                message=f"API error: {error_message[:50]}, retrying later"
            )
        else:
            return ErrorAnalysis(
                error_type=ErrorType.API_ERROR,
                severity="high",
                recovery_action=RecoveryAction.USE_FALLBACK,
                modified_prompt=None,
                retry_delay=0,
                max_retries=0,
                should_retry=False,
                fallback_data={"type": "error_fallback", "error": error_message},
                message="API error persistent, using fallback"
            )

    def _handle_network_error(
        self,
        original_prompt: str,
        attempt: int
    ) -> ErrorAnalysis:
        """Handle network error"""
        if attempt < 3:
            delay = 5.0 * (attempt + 1)
            return ErrorAnalysis(
                error_type=ErrorType.NETWORK_ERROR,
                severity="medium",
                recovery_action=RecoveryAction.RETRY_WITH_DELAY,
                modified_prompt=original_prompt,
                retry_delay=delay,
                max_retries=3,
                should_retry=True,
                fallback_data=None,
                message=f"Network error, retrying after {delay}s"
            )
        else:
            return ErrorAnalysis(
                error_type=ErrorType.NETWORK_ERROR,
                severity="critical",
                recovery_action=RecoveryAction.ABORT,
                modified_prompt=None,
                retry_delay=0,
                max_retries=0,
                should_retry=False,
                fallback_data={"type": "network_error"},
                message="Network persistently abnormal, aborting"
            )

    def _handle_unknown_error(
        self,
        original_prompt: str,
        attempt: int
    ) -> ErrorAnalysis:
        """Handle unknown error"""
        if attempt < 2:
            return ErrorAnalysis(
                error_type=ErrorType.UNKNOWN,
                severity="medium",
                recovery_action=RecoveryAction.RETRY_WITH_DELAY,
                modified_prompt=original_prompt,
                retry_delay=2.0,
                max_retries=2,
                should_retry=True,
                fallback_data=None,
                message="Unknown error, attempting retry"
            )
        else:
            return ErrorAnalysis(
                error_type=ErrorType.UNKNOWN,
                severity="high",
                recovery_action=RecoveryAction.USE_FALLBACK,
                modified_prompt=None,
                retry_delay=0,
                max_retries=0,
                should_retry=False,
                fallback_data={"type": "unknown_error"},
                message="Unknown error persistent, using fallback"
            )

    def _detect_violation_type(self, prompt: str) -> str:
        """Detect content policy violation type"""
        prompt_lower = prompt.lower()

        violence_keywords = ["violence", "war", "weapon", "attack"]
        adult_keywords = ["sexy", "nude", "adult"]
        political_keywords = ["political", "government"]

        if any(kw in prompt_lower for kw in violence_keywords):
            return "violence"
        elif any(kw in prompt_lower for kw in adult_keywords):
            return "adult"
        elif any(kw in prompt_lower for kw in political_keywords):
            return "political"

        return "default"

    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitize sensitive words"""
        result = prompt

        # Replace sensitive words (case insensitive)
        for sensitive, safe in self.SENSITIVE_WORDS.items():
            pattern = re.compile(re.escape(sensitive), re.IGNORECASE)
            result = pattern.sub(safe, result)

        return result

    def _create_abstract_prompt(self, original_prompt: str, fallback: Dict) -> str:
        """Create abstract prompt"""
        # Extract core info (title etc)
        lines = original_prompt.split("\n")
        title_line = ""
        for line in lines:
            if "title" in line.lower():
                title_line = line
                break

        abstract = f"""Create a professional PPT slide image.

Style: {fallback['modifier']}
Background: {fallback['background']}

Requirements:
- Clean, minimal design
- Professional appearance
- 16:9 aspect ratio
- No text rendering issues

{title_line}
"""
        return abstract

    def _simplify_prompt(self, prompt: str) -> str:
        """Simplify prompt"""
        # Remove detailed description, keep core instructions
        lines = prompt.split("\n")
        simplified_lines = []

        important_keywords = ["title", "slide", "ppt", "style", "color"]

        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in important_keywords):
                simplified_lines.append(line)
            elif len(line.strip()) < 50:  # Keep short lines
                simplified_lines.append(line)

        # Limit total length
        simplified = "\n".join(simplified_lines)
        if len(simplified) > 500:
            simplified = simplified[:500] + "..."

        return simplified

    def create_fallback_slide(self, slide_info: Dict, fallback_type: str = "gradient") -> Dict:
        """
        Create fallback slide

        Args:
            slide_info: Original slide info
            fallback_type: Fallback type

        Returns:
            Dict: Fallback slide data
        """
        return {
            "type": "fallback",
            "fallback_type": fallback_type,
            "title": slide_info.get("title", ""),
            "key_points": slide_info.get("key_points", [])[:3],
            "background": {
                "type": "gradient",
                "colors": ["#1e3c72", "#2a5298"]
            },
            "text_color": "#FFFFFF",
            "message": "This slide was generated using fallback"
        }

    def get_error_summary(self) -> Dict:
        """Get error statistics summary"""
        if not self.error_history:
            return {"total_errors": 0}

        error_counts = {}
        for error in self.error_history:
            error_type = error["type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "error_counts": error_counts,
            "last_error": self.error_history[-1] if self.error_history else None
        }

    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
