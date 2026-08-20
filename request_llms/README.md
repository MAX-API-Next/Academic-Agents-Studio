P.S. 如果您按照以下步骤成功接入了新的大模型，欢迎发Pull Requests（如果您在自己接入新模型的过程中遇到困难，欢迎加README底部QQ群联系群主）


# 科研绘图接口说明

页面中的“绘图功能区”使用独立的 OpenAI 兼容 Images API，不经过普通聊天模型的 `request_llms/bridge_*.py` 流程。接入或更换图片服务时，通常无需新增聊天模型 bridge，而应配置以下项目：

```python
IMAGE_API_URL = "https://api.aiearth.dev/v1/images/generations"
IMAGE_MODEL = "gpt-image-2"
IMAGE_TIMEOUT_SECONDS = 180
```

服务器环境变量分别为 `GPT_ACADEMIC_IMAGE_API_URL`、`GPT_ACADEMIC_IMAGE_MODEL` 和 `GPT_ACADEMIC_IMAGE_TIMEOUT_SECONDS`。绘图默认复用 `API_KEY` / `GPT_ACADEMIC_API_KEY`，令牌需要拥有所配置图片模型的访问权限。接口适配代码位于 `shared_utils/image_generation.py`，后台任务管理位于 `shared_utils/image_jobs.py`。


# 如何接入其他本地大语言模型

1. 复制`request_llms/bridge_llama2.py`，重命名为你喜欢的名字

2. 修改`load_model_and_tokenizer`方法，加载你的模型和分词器（去该模型官网找demo，复制粘贴即可）

3. 修改`llm_stream_generator`方法，定义推理模型（去该模型官网找demo，复制粘贴即可）

4. 命令行测试
    - 修改`tests/test_llms.py`（聪慧如您，只需要看一眼该文件就明白怎么修改了）
    - 运行`python tests/test_llms.py`

5. 测试通过后，在`request_llms/bridge_all.py`中做最后的修改，把你的模型完全接入到框架中（聪慧如您，只需要看一眼该文件就明白怎么修改了）

6. 修改`LLM_MODEL`配置，然后运行`python main.py`，测试最后的效果


# 如何接入其他在线大语言模型

1. 复制`request_llms/bridge_zhipu.py`，重命名为你喜欢的名字

2. 修改`predict_no_ui_long_connection`

3. 修改`predict`

4. 命令行测试
    - 修改`tests/test_llms.py`（聪慧如您，只需要看一眼该文件就明白怎么修改了）
    - 运行`python tests/test_llms.py`

5. 测试通过后，在`request_llms/bridge_all.py`中做最后的修改，把你的模型完全接入到框架中（聪慧如您，只需要看一眼该文件就明白怎么修改了）

6. 修改`LLM_MODEL`配置，然后运行`python main.py`，测试最后的效果
