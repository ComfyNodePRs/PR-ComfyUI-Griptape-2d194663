from griptape.config import (
    StructureConfig,
)

# StructureGlobalDriversConfig,
from griptape.drivers import (
    OpenAiChatPromptDriver,
    OpenAiImageGenerationDriver,
    OpenAiImageQueryDriver,
    OpenAiTextToSpeechDriver,
)

from .base_config import gtUIBaseConfig


class gtUIOpenAiCompatibleConfig(gtUIBaseConfig):
    """
    Create an OpenAI Compatible Structure Config
    """

    DESCRIPTION = "OpenAI Compatible Structure Config."

    @classmethod
    def INPUT_TYPES(s):
        inputs = super().INPUT_TYPES()
        del inputs["optional"]["image_generation_driver"]
        inputs["optional"].update(
            {
                "prompt_model": ("STRING", {"default": "gpt-4o"}),
                "image_generation_model": ("STRING", {"default": "dall-e-3"}),
                "image_query_model": ("STRING", {"default": "gpt-4o"}),
                "text_to_speech_model": ("STRING", {"default": "tts-1"}),
                "prompt_base_url": ("STRING", {"default": "https://url/v1"}),
                "api_key": ("STRING", {"default": ""}),
            }
        )
        return inputs

    def create(self, **kwargs):
        prompt_model = kwargs.get("prompt_model", None)
        image_generation_model = kwargs.get("image_generation_model", None)
        image_query_model = kwargs.get("image_query_model", None)
        text_to_speech_model = kwargs.get("text_to_speech_model", None)
        base_url = kwargs.get("prompt_base_url", None)
        api_key = kwargs.get("api_key", None)

        configs = {}
        if prompt_model and base_url and api_key:
            configs["prompt_driver"] = OpenAiChatPromptDriver(
                model=prompt_model,
                base_url=base_url,
                api_key=api_key,
            )
        if image_generation_model and base_url and api_key:
            configs["image_generation_driver"] = OpenAiImageGenerationDriver(
                model=image_generation_model,
                base_url=base_url,
                api_key=api_key,
            )

        if image_query_model and base_url and api_key:
            configs["image_query_driver"] = OpenAiImageQueryDriver(
                model=image_query_model,
                base_url=base_url,
                api_key=api_key,
            )

        if text_to_speech_model and base_url and api_key:
            configs["text_to_speech_driver"] = OpenAiTextToSpeechDriver(
                model=text_to_speech_model,
                base_url=base_url,
                api_key=api_key,
            )
        custom_config = StructureConfig(**configs)

        return (custom_config,)
