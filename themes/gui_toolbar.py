import gradio as gr
from toolbox import get_conf
from request_llms.model_provider import ALL_MODEL_PROVIDERS, group_models_by_provider
from shared_utils.web_config import (
    CREDENTIAL_CONFIG_KEYS,
    DEFAULT_CREDENTIAL_PROVIDER,
    credential_status,
)

def define_gui_toolbar(AVAIL_LLM_MODELS, LLM_MODEL, INIT_SYS_PROMPT, THEME, AVAIL_THEMES, AVAIL_FONTS, ADD_WAIFU, help_menu_description, js_code_for_toggle_darkmode):
    with gr.Floating(
        init_x="0%",
        init_y="0%",
        visible=True,
        width="100%",
        drag="forbidden",
        variant="compact",
        elem_id="tooltip",
        elem_classes="app-navbar",
    ):
        with gr.Row():
            with gr.Tab("文件", elem_id="navbar-upload-panel"):
                gr.Markdown("请上传本地文件/压缩包供“函数插件区”功能调用。请注意: 上传文件后会自动把输入区修改为相应路径。")
                file_upload_2 = gr.Files(label="任何文件, 推荐上传压缩文件(zip, tar)", file_count="multiple", elem_id="elem_upload_float")

            with gr.Tab("模型", elem_id="navbar-model-panel"):
                provider_groups = group_models_by_provider(AVAIL_LLM_MODELS)
                provider_dropdown = gr.Dropdown(
                    [ALL_MODEL_PROVIDERS, *provider_groups],
                    value=ALL_MODEL_PROVIDERS,
                    interactive=True,
                    elem_id="elem_model_provider_sel",
                    label="模型厂商 / 接入渠道",
                ).style(container=False)
                md_dropdown = gr.Dropdown(
                    AVAIL_LLM_MODELS,
                    value=LLM_MODEL,
                    interactive=True,
                    elem_id="elem_model_sel",
                    label="模型",
                ).style(container=False)
                top_p = gr.Slider(minimum=-0, maximum=1.0, value=1.0, step=0.01,interactive=True, label="Top-p (nucleus sampling)", elem_id="elem_top_p")
                temperature = gr.Slider(minimum=-0, maximum=2.0, value=1.0, step=0.01, interactive=True, label="Temperature", elem_id="elem_temperature")
                max_length_sl = gr.Slider(minimum=256, maximum=1024*32, value=4096, step=128, interactive=True, label="Local LLM MaxLength", elem_id="elem_max_length_sl")
                system_prompt = gr.Textbox(show_label=True, lines=2, placeholder=f"System Prompt", label="System prompt", value=INIT_SYS_PROMPT, elem_id="elem_prompt")
                temperature.change(None, inputs=[temperature], outputs=None,
                    _js="""(temperature)=>gpt_academic_gradio_saveload("save", "elem_temperature", "js_temperature_cookie", temperature)""")
                system_prompt.change(None, inputs=[system_prompt], outputs=None,
                    _js="""(system_prompt)=>gpt_academic_gradio_saveload("save", "elem_prompt", "js_system_prompt_cookie", system_prompt)""")
                md_dropdown.change(None, inputs=[md_dropdown], outputs=None,
                    _js="""(md_dropdown)=>gpt_academic_gradio_saveload("save", "elem_model_sel", "js_md_dropdown_cookie", md_dropdown)""")

            with gr.Tab("外观", elem_id="navbar-appearance-panel"):
                theme_dropdown = gr.Dropdown(AVAIL_THEMES, value=THEME, label="更换UI主题").style(container=False)
                fontfamily_dropdown = gr.Dropdown(AVAIL_FONTS, value=get_conf("FONT"), elem_id="elem_fontfamily", label="更换字体类型").style(container=False)
                fontsize_slider = gr.Slider(minimum=5, maximum=25, value=15, step=1, interactive=True, label="字体大小(默认15)", elem_id="elem_fontsize")
                checkboxes = gr.CheckboxGroup(["基础功能区", "函数插件区", "浮动输入区", "输入清除键", "插件参数区"], value=["基础功能区", "函数插件区"], label="显示/隐藏功能区", elem_id='cbs').style(container=False)
                opt = ["自定义菜单", "主标题", "副标题", "显示logo"]
                value=["主标题", "副标题", "显示logo"]
                if ADD_WAIFU: opt += ["添加Live2D形象"]; value += ["添加Live2D形象"]
                checkboxes_2 = gr.CheckboxGroup(opt, value=value, label="显示/隐藏自定义菜单", elem_id='cbsc').style(container=False)
                dark_mode_btn = gr.Button("切换界面明暗 ☀", variant="secondary").style(size="sm")
                dark_mode_btn.click(None, None, None, _js=js_code_for_toggle_darkmode)
                open_new_tab = gr.Button("打开新对话", variant="secondary").style(size="sm")
                open_new_tab.click(None, None, None, _js=f"""()=>duplicate_in_new_window()""")
                fontfamily_dropdown.select(None, inputs=[fontfamily_dropdown], outputs=None,
                    _js="""(fontfamily)=>{gpt_academic_gradio_saveload("save", "elem_fontfamily", "js_fontfamily", fontfamily); gpt_academic_change_chatbot_font(fontfamily, null, null);}""")
                fontsize_slider.change(None, inputs=[fontsize_slider], outputs=None,
                    _js="""(fontsize)=>{gpt_academic_gradio_saveload("save", "elem_fontsize", "js_fontsize", fontsize); gpt_academic_change_chatbot_font(null, fontsize, null);}""")

            with gr.Tab("设置", elem_id="navbar-settings-panel"):
                settings_provider = gr.Dropdown(
                    list(CREDENTIAL_CONFIG_KEYS),
                    value=DEFAULT_CREDENTIAL_PROVIDER,
                    interactive=True,
                    elem_id="settings_api_provider",
                    label="密钥厂商",
                ).style(container=False)
                settings_api_key = gr.Textbox(
                    type="password",
                    label="新 API Key",
                    placeholder="留空则保持现有密钥",
                    elem_id="settings_api_key",
                )
                settings_clear_api_key = gr.Checkbox(
                    value=False,
                    label="清除该厂商已保存的密钥",
                    elem_id="settings_clear_api_key",
                )
                settings_default_model = gr.Dropdown(
                    AVAIL_LLM_MODELS,
                    value=LLM_MODEL,
                    interactive=True,
                    elem_id="settings_default_model",
                    label="默认模型（重启后生效）",
                ).style(container=False)
                settings_save = gr.Button("保存设置", variant="primary", elem_id="settings_save")
                settings_status = gr.Markdown(
                    credential_status(DEFAULT_CREDENTIAL_PROVIDER),
                    elem_id="settings_status",
                )
                settings_provider.change(
                    credential_status,
                    inputs=[settings_provider],
                    outputs=[settings_status],
                )

            with gr.Tab("帮助", elem_id="navbar-help-panel"):
                gr.Markdown(help_menu_description)
    return (
        checkboxes, checkboxes_2, max_length_sl, theme_dropdown, system_prompt,
        file_upload_2, provider_dropdown, md_dropdown, top_p, temperature,
        settings_provider, settings_api_key, settings_clear_api_key,
        settings_default_model, settings_save, settings_status,
    )
