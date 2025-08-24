"""
Text processing utilities for content handling.
"""

import tiktoken

# Global encoding instance
ENCODING = tiktoken.get_encoding("cl100k_base")


def truncate_content_to_token_limit(content: str, max_tokens: int) -> str:
    """Ensures the text sent to the AI does not exceed its maximum token limit."""
    try:
        token_count = len(ENCODING.encode(content))
        if token_count <= max_tokens:
            return content

        # For very long content, make a rough initial cut to speed up the process.
        if token_count > max_tokens * 2:
            bytes_per_token = len(content.encode("utf-8")) / token_count
            target_bytes = int(max_tokens * bytes_per_token * 0.9)
            content = content[:target_bytes]
            token_count = len(ENCODING.encode(content))

        # Fine-tune the truncation to get as close to the token limit as possible.
        if token_count > max_tokens:
            low, high = 0, len(content)
            while high - low > 100:
                mid = (low + high) // 2
                if len(ENCODING.encode(content[:mid])) <= max_tokens:
                    low = mid
                else:
                    high = mid
            content = content[:low]
        return content
    except (ValueError, TypeError) as e:
        print(f"Warning: Error during content truncation: {str(e)}")
        return content[: int(max_tokens * 3)]