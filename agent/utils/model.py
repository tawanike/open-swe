import os

from langchain.chat_models import init_chat_model

OPENAI_RESPONSES_WS_BASE_URL = "wss://api.openai.com/v1"


def make_model(model_id: str, **kwargs: dict):
    model_kwargs = kwargs.copy()

    # Azure Anthropic: use env vars to configure
    azure_api_key = os.environ.get("AZURE_ANTHROPIC_API_KEY")
    azure_endpoint = os.environ.get("AZURE_ANTHROPIC_ENDPOINT")

    if azure_api_key and azure_endpoint:
        azure_model = os.environ.get("AZURE_ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        azure_api_version = os.environ.get("AZURE_ANTHROPIC_API_VERSION", "2024-10-22")

        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=azure_model,
            anthropic_api_key=azure_api_key,
            anthropic_api_url=azure_endpoint,
            default_headers={"anthropic-version": azure_api_version},
            **{k: v for k, v in model_kwargs.items() if k in ("temperature", "max_tokens")},
        )

    if model_id.startswith("openai:"):
        model_kwargs["base_url"] = OPENAI_RESPONSES_WS_BASE_URL
        model_kwargs["use_responses_api"] = True

    return init_chat_model(model=model_id, **model_kwargs)
