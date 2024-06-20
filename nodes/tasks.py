import base64
import os
from textwrap import dedent

import folder_paths
from griptape.artifacts import BaseArtifact, TextArtifact
from griptape.drivers import (
    AmazonBedrockImageQueryDriver,
    AnthropicImageQueryDriver,
    DummyAudioTranscriptionDriver,
    DummyImageQueryDriver,
    OpenAiAudioTranscriptionDriver,
    OpenAiImageGenerationDriver,
)
from griptape.engines import (
    AudioTranscriptionEngine,
    ImageQueryEngine,
    PromptImageGenerationEngine,
    VariationImageGenerationEngine,
)
from griptape.loaders import AudioLoader, ImageLoader
from griptape.structures import Agent, Pipeline, Workflow
from griptape.tasks import (
    AudioTranscriptionTask,
    CodeExecutionTask,
    CsvExtractionTask,
    ImageQueryTask,
    JsonExtractionTask,
    PromptImageGenerationTask,
    PromptTask,
    TextSummaryTask,
    ToolkitTask,
    ToolTask,
    VariationImageGenerationTask,
)
from griptape.utils import load_file
from schema import Schema

from ..py.griptape_config import get_config
from .agent import model_check
from .base_audio_task import gtUIBaseAudioTask
from .base_image_task import gtUIBaseImageTask
from .base_task import gtUIBaseTask
from .utilities import convert_tensor_to_base_64, image_path_to_output

default_prompt = "{{ input_string }}"
OPENAI_API_KEY = get_config("env.OPENAI_API_KEY")


class gtUIPromptTask(gtUIBaseTask): ...


class gtUICsvExtractionTask(gtUIBaseTask):
    @classmethod
    def INPUT_TYPES(s):
        inputs = super().INPUT_TYPES()
        inputs["optional"].update(
            {
                "driver": ("DRIVER",),
                "columns": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "Column 1, Column 2, Column 3",
                    },
                ),
            }
        )

        return inputs

    def run(self, STRING, columns=None, input_string=None, agent=None):
        if not agent:
            agent = Agent()
        prompt_text = self.get_prompt_text(STRING, input_string)
        try:
            if columns:
                column_list = columns.split(",")
            else:
                column_list = ["Column 1"]
            agent.add_task(
                CsvExtractionTask(prompt_text, args={"column_names": column_list})
            )
        except Exception as e:
            print(e)
        result = agent.run()
        # This returns a CSVRowArtifact object, which is not directly usable in ComfyUI
        # So we convert it to a string
        formatted_string = "\n".join(
            [
                ", ".join(
                    [f"{key.strip()}: {value}" for key, value in artifact.value.items()]
                )
                for artifact in result.output_task.output
            ]
        )

        return (formatted_string, agent)


class gtUIJsonExtractionTask(gtUIBaseTask):
    @classmethod
    def INPUT_TYPES(s):
        default_schema = '{"users": [{"name": str, "age": int, "location": str}]}'
        inputs = super().INPUT_TYPES()
        inputs["optional"].update(
            {
                "driver": ("DRIVER",),
                "schema": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": default_schema,
                    },
                ),
            }
        )

        return inputs

    def run(self, STRING, schema=None, input_string=None, agent=None):
        if not agent:
            agent = Agent()
        prompt_text = self.get_prompt_text(STRING, input_string)
        try:
            if schema:
                print(schema)
                template_schema = Schema(schema).json_schema("TemplateSchema")
            else:
                print("damn")
                template_schema = Schema({}).json_schema("TemplateSchema")
            agent.add_task(
                JsonExtractionTask(
                    prompt_text, args={"template_schema": template_schema}
                )
            )
        # TODO - error extracting json
        except Exception as e:
            print(e)
        result = agent.run()
        output = result.output_task.output
        print(output)

        return (str(output.value), agent)


class gtUIPromptImageGenerationTask(gtUIBaseTask):
    @classmethod
    def INPUT_TYPES(s):
        inputs = super().INPUT_TYPES()
        inputs["optional"].update({"driver": ("DRIVER",)})
        return inputs

    RETURN_TYPES = (
        "IMAGE",
        "AGENT",
        "STRING",
    )
    RETURN_NAMES = ("IMAGE", "AGENT", "file_path")
    CATEGORY = "Griptape/Images"

    def run(
        self,
        STRING,
        driver=None,
        input_string=None,
        agent=None,
    ):
        if not agent:
            agent = Agent()

        prompt_text = self.get_prompt_text(STRING, input_string)
        if not driver:
            driver = OpenAiImageGenerationDriver(
                model="dall-e-3", quality="hd", style="natural", api_key=OPENAI_API_KEY
            )
        # Create an engine configured to use the driver.
        engine = PromptImageGenerationEngine(
            image_generation_driver=driver,
        )

        try:
            output_dir = folder_paths.get_temp_directory()

            agent.add_task(
                PromptImageGenerationTask(
                    input=prompt_text,
                    image_generation_engine=engine,
                    output_dir=output_dir,
                )
            )
        except Exception as e:
            print(e)
        result = agent.run()
        filename = result.output_task.output.name
        image_path = os.path.join(output_dir, filename)

        # Get the image in a format ComfyUI can read
        output_image, output_mask = image_path_to_output(image_path)

        return (output_image, agent, image_path)


class gtUIPromptImageVariationTask(gtUIBaseImageTask):
    @classmethod
    def INPUT_TYPES(s):
        inputs = super().INPUT_TYPES()
        inputs["optional"].update({"driver": ("DRIVER",)})
        del inputs["optional"]["agent"]
        return inputs

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("IMAGE", "FILE_PATH")
    CATEGORY = "Griptape/Images"

    def run(
        self,
        STRING,
        image,
        driver=None,
        input_string=None,
    ):
        agent = Agent()
        final_image = convert_tensor_to_base_64(image)
        if not final_image:
            return ("No image provided", agent)

        prompt_text = self.get_prompt_text(STRING, input_string)
        if not driver:
            driver = OpenAiImageGenerationDriver(
                api_key=OPENAI_API_KEY,
                model="dall-e-2",
            )
        # Create an engine configured to use the driver.
        engine = VariationImageGenerationEngine(
            image_generation_driver=driver,
        )
        image_artifact = ImageLoader().load(base64.b64decode(final_image))
        try:
            output_dir = folder_paths.get_temp_directory()

            agent.add_task(
                VariationImageGenerationTask(
                    input=(prompt_text, image_artifact),
                    image_generation_engine=engine,
                    output_dir=output_dir,
                )
            )
        except Exception as e:
            print(e)
        try:
            result = agent.run()
        except Exception as e:
            print(e)
        filename = result.output_task.output.name
        image_path = os.path.join(output_dir, filename)
        # Get the image in a format ComfyUI can read
        output_image, output_mask = image_path_to_output(image_path)

        return (output_image, image_path)


class gtUIAudioTranscriptionTask(gtUIBaseAudioTask):
    CATEGORY = "Griptape/Audio"

    def run(self, audio, driver=None):
        try:
            audio_artifact = AudioLoader().load(load_file(audio))
        except Exception as e:
            print(f"Error loading audio file: {e}")
        if audio_artifact:
            if not driver:
                audio_transcription_driver = OpenAiAudioTranscriptionDriver(
                    model="whisper-1"
                )
            else:
                audio_transcription_driver = driver

            # If the driver is a DummyAudioTranscriptionDriver we'll return a nice error message
            if isinstance(audio_transcription_driver, DummyAudioTranscriptionDriver):
                return (
                    dedent(
                        """
                    I'm sorry, this agent doesn't have access to a valid AudioTranscriptionDriver.
                    You might want to try using a different Agent Configuration.

                    Reach out for help on Discord (https://discord.gg/gnWRz88eym) if you would like some help.
                    """,
                    ),
                )
            engine = AudioTranscriptionEngine(
                audio_transcription_driver=audio_transcription_driver
            )
            # prompt_text = self.get_prompt_text(STRING, input_string)

            task = AudioTranscriptionTask(
                input=lambda _: audio_artifact,
                audio_transcription_engine=engine,
            )
            pipeline = Pipeline()
            try:
                pipeline.add_task(task)
                result = pipeline.run()
            except Exception as e:
                print(e)
            output = result.output_task.output.value
        else:
            output = "No audio provided"
        return (output,)


class gtUIImageQueryTask(gtUIBaseImageTask):
    CATEGORY = "Griptape/Images"

    def run(
        self,
        STRING,
        image,
        input_string=None,
        agent=None,
    ):
        final_image = convert_tensor_to_base_64(image)
        if final_image:
            if not agent:
                agent = Agent()

            image_query_driver = agent.config.image_query_driver

            # If the driver is a DummyImageQueryDriver we'll return a nice error message
            if isinstance(image_query_driver, DummyImageQueryDriver):
                return (
                    dedent("""
                    I'm sorry, this agent doesn't have access to a valid ImageQueryDriver.
                    You might want to try using a different Agent Configuration.

                    Reach out for help on Discord (https://discord.gg/gnWRz88eym) if you would like some help.
                    """),
                    agent,
                )
            engine = ImageQueryEngine(image_query_driver=image_query_driver)
            image_artifact = ImageLoader().load(base64.b64decode(final_image))

            prompt_text = self.get_prompt_text(STRING, input_string)

            # If the driver is AmazonBedrock or Anthropic, the prompt_text cannot be empty
            if prompt_text.strip() == "":
                if isinstance(
                    image_query_driver,
                    (AmazonBedrockImageQueryDriver, AnthropicImageQueryDriver),
                ):
                    prompt_text = "Describe this image"

            task = ImageQueryTask(
                input=(prompt_text, [image_artifact]), image_query_engine=engine
            )
            try:
                agent.add_task(task)
            except Exception as e:
                print(e)
            result = agent.run()
            output = result.output_task.output.value
        else:
            output = "No image provided"
        return (output, agent)


def do_start_task(task: CodeExecutionTask) -> BaseArtifact:
    return TextArtifact(str(task.input))


class gtUIParallelImageQueryTask(gtUIBaseImageTask):
    CATEGORY = "Griptape/Images"

    def run(
        self,
        STRING,
        image,
        input_string=None,
        agent=None,
    ):
        final_image = convert_tensor_to_base_64(image)
        if final_image:
            if not agent:
                agent = Agent()

            image_query_driver = agent.config.image_query_driver
            rulesets = agent.rulesets
            # If the driver is a DummyImageQueryDriver we'll return a nice error message
            if isinstance(image_query_driver, DummyImageQueryDriver):
                return (
                    dedent("""
                    I'm sorry, this agent doesn't have access to a valid ImageQueryDriver.
                    You might want to try using a different Agent Configuration.

                    Reach out for help on Discord (https://discord.gg/gnWRz88eym) if you would like some help.
                    """),
                    agent,
                )
            engine = ImageQueryEngine(image_query_driver=image_query_driver)
            image_artifact = ImageLoader().load(base64.b64decode(final_image))

            prompt_text = self.get_prompt_text(STRING, input_string)

            # If the driver is AmazonBedrock or Anthropic, the prompt_text cannot be empty
            if prompt_text.strip() == "":
                if isinstance(
                    image_query_driver,
                    (AmazonBedrockImageQueryDriver, AnthropicImageQueryDriver),
                ):
                    prompt_text = "Describe this image"

            structure = Workflow(rulesets=rulesets)
            start_task = CodeExecutionTask("Start", run_fn=do_start_task, id="START")
            end_task = PromptTask(
                "Concatenate just the output values of the tasks, separated by two newlines: {{ parent_outputs }}",
                id="END",
                prompt_driver=agent.config.prompt_driver,
                rulesets=rulesets,
            )
            structure.add_task(start_task)
            structure.add_task(end_task)

            prompts = prompt_text.split("\n")
            prompt_tasks = []
            for prompt in prompts:
                # task = ToolTask(tool=ImageQueryClient(off_prompt=True), rulesets=rulesets)
                task = ImageQueryTask(
                    input=(prompt, [image_artifact]), image_query_engine=engine
                )
                prompt_tasks.append(task)

            structure.insert_tasks(start_task, prompt_tasks, end_task)
            result = structure.run()
            output = result.output_task.output.value
        else:
            output = "No image provided"
        return (output, agent)


class gtUITextSummaryTask(gtUIBaseTask):
    def run(self, STRING, input_string=None, agent=None):
        if not agent:
            agent = Agent()
        prompt_text = self.get_prompt_text(STRING, input_string)
        try:
            agent.add_task(TextSummaryTask(prompt_text))
        except Exception as e:
            print(e)
        result = agent.run()
        return (result.output_task.output.value, agent)


class gtUIToolTask(gtUIBaseTask):
    @classmethod
    def INPUT_TYPES(s):
        inputs = super().INPUT_TYPES()

        # Update optional inputs to include 'tool' and adjust others as necessary
        inputs["optional"].update(
            {
                "tool": ("TOOL_LIST",),
            }
        )
        return inputs

    def run(
        self,
        STRING,
        tool=[],
        input_string=None,
        agent=None,
    ):
        if not agent:
            agent = Agent()

        prompt_text = self.get_prompt_text(STRING, input_string)

        # Figure out what tool to use.
        # If none are provided, check the agent for tools
        # if the agent doesn't have any, then we won't use any tools.
        agent_tools = []
        agent_tools = agent.tools

        if len(tool) > 0:
            agent_tool = tool[0]
        elif len(agent_tools) > 0:
            agent_tool = agent_tools[0]
        else:
            agent_tool = None

        if agent_tool:
            # No point in using off_prompt if we're using a ToolTask - it's not supported
            agent_tool.off_prompt = False
            task = ToolTask(prompt_text, tool=agent_tool)
        else:
            task = PromptTask(prompt_text)

        try:
            agent.add_task(task)
        except Exception as e:
            print(e)
        result = agent.run()
        return (result.output_task.output.value, agent)


class gtUIToolkitTask(gtUIBaseTask):
    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()

        # Update optional inputs to include 'tool' and adjust others as necessary
        inputs["optional"].update(
            {
                "tools": ("TOOL_LIST",),
            }
        )
        return inputs

    def run(
        self,
        STRING,
        tools=[],
        input_string=None,
        agent=None,
    ):
        prompt_text = self.get_prompt_text(STRING, input_string)

        if len(tools) == 0:
            return super().run(STRING, input_string, agent)

        # if the tool is provided, keep going
        if not agent:
            agent = Agent()

        if model_check(agent):
            return (
                dedent(
                    """
                I'm sorry, this agent uses a simple model that can't handle ToolkitTasks.
                You might want to try using a different Agent Configuration, or use a simple ToolTask instead.

                Reach out for help on Discord (https://discord.gg/gnWRz88eym) if you would like some help.
                """
                ),
                agent,
            )
        task = ToolkitTask(prompt_text, tools=tools)
        try:
            agent.add_task(task)
        except Exception as e:
            print(e)
        result = agent.run()
        return (result.output_task.output.value, agent)
