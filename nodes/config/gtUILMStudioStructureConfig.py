from griptape.config import (
    StructureConfig,
)

# StructureGlobalDriversConfig,
from griptape.drivers import (
    OpenAiChatPromptDriver,
)

from ..utilities import get_models
from .gtUIBaseConfig import gtUIBaseConfig

lmstudio_port = "1234"
lmstudio_base_url = "http://127.0.0.1"
lmstudio_models = get_models("lmstudio", lmstudio_base_url, lmstudio_port)
if len(lmstudio_models) == 0:
    lmstudio_models.append("")


class gtUILMStudioStructureConfig(gtUIBaseConfig):
    """
    The Griptape LM Studio Structure Config
    """

    DESCRIPTION = (
        "LM Studio Prompt Driver. LMStudio is available at https://lmstudio.ai "
    )

    @classmethod
    def INPUT_TYPES(s):
        inputs = super().INPUT_TYPES()
        inputs["required"].update(
            {
                "model": ((), {}),
                # "model": (
                #     "STRING",
                #     {"default": lmstudio_models[0]},
                # ),
                # "prompt_model": ("STRING", {"default": ""}),
                "base_url": ("STRING", {"default": lmstudio_base_url}),
                "port": (
                    "STRING",
                    {"default": lmstudio_port},
                ),
            },
        )
        return inputs

    def create(self, **kwargs):
        prompt_model = kwargs.get("prompt_model", "")
        base_url = kwargs.get("base_url", lmstudio_base_url)
        port = kwargs.get("port", lmstudio_port)
        temperature = kwargs.get("temperature", 0.7)
        max_attempts = kwargs.get("max_attempts_on_fail", 10)
        stream = kwargs.get("stream", False)
        seed = kwargs.get("seed", 12341)
        custom_config = StructureConfig(
            prompt_driver=OpenAiChatPromptDriver(
                model=prompt_model,
                base_url=f"{base_url}:{port}/v1",
                api_key="lm_studio",
                temperature=temperature,
                max_attempts=max_attempts,
                stream=stream,
                seed=seed,
            ),
        )

        return (custom_config,)
