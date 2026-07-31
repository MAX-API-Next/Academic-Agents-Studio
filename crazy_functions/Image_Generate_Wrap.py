
from crazy_functions.Image_Generate import 图片生成_GPT_IMAGE
from crazy_functions.plugin_template.plugin_class_template import GptAcademicPluginTemplate, ArgProperty


class ImageGen_Wrap(GptAcademicPluginTemplate):
    def __init__(self):
        """
        请注意`execute`会执行在不同的线程中，因此您在定义和使用类变量时，应当慎之又慎！
        """
        pass

    def define_arg_selection_menu(self):
        """
        定义插件的二级选项菜单

        第一个参数，名称`main_input`，参数`type`声明这是一个文本框，文本框上方显示`title`，文本框内部显示`description`，`default_value`为默认值；
        第二个参数，名称`advanced_arg`，参数`type`声明这是一个文本框，文本框上方显示`title`，文本框内部显示`description`，`default_value`为默认值；

        """
        gui_definition = {
            "main_input": ArgProperty(
                title="输入图片描述",
                description="描述主体、布局、风格和用途",
                default_value="",
                type="string",
            ).model_dump_json(),
            "resolution": ArgProperty(
                title="尺寸",
                options=["auto", "1024x1024", "1536x1024", "1024x1536"],
                default_value="auto",
                description="auto 将由模型选择",
                type="dropdown",
            ).model_dump_json(),
            "quality": ArgProperty(
                title="质量",
                options=["low", "medium", "high", "auto"],
                default_value="medium",
                description="草稿可选 low，成稿可选 high",
                type="dropdown",
            ).model_dump_json(),
            "output_format": ArgProperty(
                title="格式",
                options=["png", "jpeg", "webp"],
                default_value="png",
                description="PNG 适合论文插图",
                type="dropdown",
            ).model_dump_json(),
        }
        return gui_definition

    def execute(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
        yield from 图片生成_GPT_IMAGE(
            txt,
            llm_kwargs,
            plugin_kwargs,
            chatbot,
            history,
            system_prompt,
            user_request,
        )
