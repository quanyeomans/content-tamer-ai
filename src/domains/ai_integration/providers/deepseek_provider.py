"""
Deepseek Provider Implementation

Extracted for domain architecture.
"""

# Import from shared infrastructure (correct layer)
from shared.infrastructure.filename_config import (
    get_secure_filename_prompt_template,
    get_token_limit_for_provider,
    validate_generated_filename,
)
from ..base_provider import AIProvider

try:
    from openai import OpenAI

    HAVE_OPENAI = True
except ImportError:
    OpenAI = None
    HAVE_OPENAI = False


def get_system_prompt(provider: str) -> str:
    """Get system prompt for provider."""
    from shared.infrastructure.filename_config import DEFAULT_SYSTEM_PROMPTS

    return DEFAULT_SYSTEM_PROMPTS.get(provider, DEFAULT_SYSTEM_PROMPTS["default"])


class DeepseekProvider(AIProvider):
    """Deepseek API provider (OpenAI-compatible)."""

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize Deepseek provider with API key and model."""
        super().__init__(api_key, model)
        if not HAVE_OPENAI or OpenAI is None:
            raise ImportError("Please install OpenAI client: pip install openai")

        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "deepseek"

    def validate_api_key(self) -> bool:
        """Validate API key format."""
        try:
            return bool(self.api_key and len(self.api_key) > 10)
        except Exception:
            return False

    def generate_filename(self, content: str, original_filename: str = "") -> str:
        """Generate intelligent filename using Deepseek API."""
        try:
            prompt = get_secure_filename_prompt_template()

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_system_prompt("deepseek")},
                    {"role": "user", "content": f"{prompt}\n\nContent:\n{content}"},
                ],
                max_tokens=get_token_limit_for_provider(),
                temperature=0.1,
            )

            content_text = response.choices[0].message.content
            if content_text is None:
                raise ValueError("Empty response from Deepseek API")
            raw_filename = content_text.strip()
            return validate_generated_filename(raw_filename)

        except Exception as e:
            self.logger.error("Deepseek filename generation failed: %s", e)
            raise RuntimeError(f"Deepseek error: {str(e)}") from e
