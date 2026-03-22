<p align="right">
   <strong>中文</strong> | <a href="README.en.md">English</a>
</p>

<div align="center">

<img src="./docs/images/logo.png" width="120" />

# Academic Agents Studio

### 🤖 新一代学术智能体应用服务平台

<p>
<strong>基于AI智能体驱动的学术研究全流程智能化平台</strong><br>
支持论文写作、文献分析、代码解释、多语言翻译等学术场景
</p>

[![Github][Github-image]][Github-url]
[![License][License-image]][License-url]
[![Python][Python-image]][Python-url]
[![Gradio][Gradio-image]][Gradio-url]
[![Stars][Stars-image]][Stars-url]

[Github-image]: https://img.shields.io/badge/GitHub-Repository-black?style=flat-square&logo=github
[License-image]: https://img.shields.io/badge/License-MIT-orange?style=flat-square
[Python-image]: https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python
[Gradio-image]: https://img.shields.io/badge/Gradio-Web%20UI-yellow?style=flat-square
[Stars-image]: https://img.shields.io/github/stars/AcademicAgentsStudio?style=flat-square

[Github-url]: https://github.com/AcademicAgentsStudio
[License-url]: https://github.com/AcademicAgentsStudio/blob/master/LICENSE
[Python-url]: https://www.python.org/
[Gradio-url]: https://gradio.app/
[Stars-url]: https://github.com/AcademicAgentsStudio/stargazers

</div>

---

> 🐾 **免费体验“OpenClaw版学术智能体服务”**  
> 我们全新推出基于 **OpenClaw** 的学术智能体服务，已接入**飞书平台**，支持自然语言对话、实时消息通知、团队协作与文件传输。现在加入飞书群聊，即可**零门槛免费体验**，让24小时待命的科研助手助您高效完成文献调研、数据分析等任务。  
> 📖 **了解更多**：[《快来一起云上免费养一只OpenClaw版学术智能体！》](https://mp.weixin.qq.com/s/XszTRMIHqf9YqKUI9QKb4A) <br>
> 👇 **立即加入飞书群聊**：

<div align="center">

<img src="./docs/feishu_openclaw_academicagent.jpg" width="200" alt="飞书群二维码"/>

</div>


## 🎯 项目简介

**Academic Agents Studio** 是一个面向学术研究人员的新一代学术智能体平台，基于 <a href="https://github.com/QwenLM/Qwen-Agent">Qwen-Agent</a> 框架和 <a href="https://github.com/modelcontextprotocol">MCP (Model Context Protocol)</a> 协议，在<a href="https://github.com/binary-husky/gpt_academic">中科院学术GPT</a>基础平台上构建。专注于为学术研究人员、教育工作者和学生提供全方位的AI智能体辅助服务，通过一站式集成多种学术专用智能体工具，全面提升研究人员的学术研究效率和质量。

### ✨ 核心特色

- 🔬 **学术专精**：针对学术场景深度优化，支持多种学术任务
- 🌐 **多模型支持**：集成GPT、Claude、Gemini、Deepseek、通义千问等主流AI模型
- 🤖 **学术智能体支持**：集成先进的智能体框架和服务协议，支持智能体外部工具调用和学术功能扩展
- 📚 **文档处理**：支持PDF、LaTeX、Markdown等多种格式的智能处理
- 🎨 **界面友好**：基于Gradio构建全新设计的科技感交互界面，支持暗色模式和多种主题
- 🔧 **高度可定制**：支持自定义插件和快捷键，满足个性化需求
- 🚀 **部署简单**：支持本地部署、Docker部署和云端部署
- ⭐ **在线体验**：在线免费体验<a href="https://agents.aiearth.vip">内测版</a>，支持最新研发功能特性，🙂支持GPT、Claude等系列基础模型，欢迎反馈！

### 🏗️ 技术架构
<p align="center">
    <img src="https://qianwen-res.oss-accelerate-overseas.aliyuncs.com/logo_qwen_agent.png" width="400"/>
<p>

#### 🤖智能体系统：

  - 智能体协作: 基于 Qwen-Agent 框架构建的专业化智能体生态
  - 模块化设计: 智能体服务专注特定领域，支持灵活组合
  - 异步处理: 高效的异步任务处理机制
  - 上下文管理: 智能化对话上下文和任务状态管理



#### 🔧MCP 服务集成：

  - 标准化协议: 基于 Model Context Protocol 的工具集成
  - 可扩展架构: 支持自定义 MCP 服务器开发
  - 工具生态: 丰富的预置工具服务
  - 热插拔支持: 动态加载和卸载 MCP 服务


## 🎓 **Academic Agents Studio** 学术智能体功能

<div align="center">

| 功能类别 | 核心功能         | 说明                             |
|---------|--------------|--------------------------------|
| 🏗️ **智能体框架** | Qwen-Agent集成 | 基于先进的Qwen-Agent框架构建专业化智能体生态    |
| | 模块化智能体       | 每个智能体专注特定领域，支持灵活组合和任务协作        |
| | 异步任务处理       | 高效的异步任务处理机制，支持并行智能体调用          |
| | 上下文管理        | 智能化对话上下文和任务状态管理，保持会话连贯性        |
| 🔌 **MCP服务** | 标准化协议        | 基于Model Context Protocol的标准化工具集成 |
| | 可扩展架构        | 支持自定义MCP服务器开发和热插拔部署            |
| | 丰富工具生态       | 预置多种学术专用MCP工具服务                |
| | 动态服务管理       | 支持MCP服务的动态加载、卸载和配置更新           |
| 🤖 **学术智能体** | 外部工具调用       | 支持图表可视化、地图天气、网络搜索等智能体工具        |
| | 工具调用可视化      | 完整显示工具调用的中间过程和执行结果             |
| | 多用户隔离        | 每个用户独立的智能体状态和API密钥，确保隐私安全      |
| | 一键启用         | 通过"学术智能体"按钮快速启用智能体功能           |
| | 免费开放         | 学术智能体服务对学术用户免费开放使用             |
| 🔄 **交互流程** | 透明化执行        | 实时显示智能体思考过程和工具选择逻辑             |
| | 步骤可视化        | 完整展示从用户输入到最终输出的每个处理环节          |
| | 错误诊断         | 详细的错误信息和调试信息，便于问题排查            |
| | 执行日志         | 完整的操作日志记录，支持回溯和分析              |
| 🎨 **界面优化** | 视觉效果优化       | 深蓝色科技风格、多层次阴影效果、实时渐变边框动画，科技感十足 |
| | 交互体验提升       | 更详细的提示信息、自适应文本输入、实时状态提示和智能反馈   |
| | 按钮交互优化       | 3D视觉效果的按钮设计，流畅的状态转换和发光动画       |

</div>

### 🔧 基于中科院学术GPT的固有功能

继承<a href="https://github.com/binary-husky/gpt_academic">中科院学术GPT</a>项目基础组件工具，为学术研究提供必备基础功能：
<div align="center">

| 功能类别 | 核心功能 | 说明 |
|---------|---------|------|
| 📄 **文档处理** | PDF解析翻译 | 一键翻译学术论文，保持格式和公式 |
| | LaTeX处理 | 支持LaTeX论文润色、翻译、语法检查 |
| | Markdown转换 | 智能转换和格式化Markdown文档 |
| 🔍 **学术工具** | Arxiv论文助手 | 快速获取和翻译Arxiv论文 |
| | 文献综述生成 | 基于多篇论文生成综合性文献综述 |
| | 代码解释分析 | 深度解析各种编程语言代码 |
| 🎨 **可视化** | 流程图生成 | 支持Mermaid图表、脑图、甘特图等 |
| | 公式渲染 | LaTeX公式的可视化渲染和编辑 |
| 🔊 **交互增强** | 语音对话 | 实时语音输入和TTS语音输出 |
| | 虚空终端 | 自然语言调用各种插件功能 |
| 💫 **界面优化** | 科技感输入区 | 渐变背景、毛玻璃效果、动态边框发光动画 |
| | 智能交互 | 多行输入、文件拖拽、快捷键提示、状态反馈 |
| 🛠️ **扩展性** | 插件系统 | 丰富的插件库和自定义插件支持 |
| | 主题定制 | 多种界面主题和个性化设置 |

</div>

## 🔄 学术智能体交互流程可视化

<div align="center">

### 透明化学术智能体执行过程：
Academic Agents Studio 提供完整的学术智能体交互流程可视化，让用户清晰了解智能体处理环节：


https://github.com/user-attachments/assets/312812e2-dc75-40b3-a067-37b587384ce3


### **用户输入解析**：
意图识别、任务分解、MCP服务解析、工具匹配。


https://github.com/user-attachments/assets/63224a4d-d895-4e4f-948e-5fdd77216745


### **工具调用过程**：
实时显示调用的工具和服务、展示工具执行状态和进度、完整的请求和响应信息。


https://github.com/user-attachments/assets/a6ec323e-cd70-4495-b17a-b25c80a0d0c3


### **结果处理和整合**：
工具结果的智能整合、格式化和可视化处理、最终结果生成和展示


https://github.com/user-attachments/assets/e0678519-e4b6-48d2-b021-2b3ddad8a91a



</div>

## 🚀 快速开始

### 环境要求

- **Python**: 3.9-3.12
- **操作系统**: Windows、Linux、macOS
- **内存**: 建议4GB以上
- **网络**: 访问AI模型API需要稳定网络连接

### 一键安装 (推荐)

```bash
# 克隆项目
git clone https://github.com/AcademicAgentsStudio.git
cd AcademicAgentsStudio

# 安装依赖
pip install -r requirements.txt

# 配置API Key (在config.py中)
# API_KEY = "your-api-key-here"

# 启动应用
python main.py
```

### Docker 部署

```bash
# 拉取镜像
docker pull aioagitech/academic_agents_studio:latest

# 运行容器（快速开始）
docker run -it -p 7860:7860 --name academic_agents_studio aioagitech/academic_agents_studio:latest sh -c "cd /workspace && python main.py" /bin/bash

# 这里的 sh -c "cd /workspace && python main.py" 可以删掉改为用户手动进入workspace文件夹执行python main.py文件

# 运行容器（设置环境变量：可以设置多个config.py下的环境变量，这里仅以设置网络访问的端口号WEB_PORT和调用模型所需的API_KEY为例）
docker run -it -p 16666:16666 --name academic_agents_studio -e WEB_PORT=16666 -e API_KEY="sk-8fK9m2pQ7xR4sT6yV3nW" aioagitech/academic_agents_studio:latest sh -c "cd /workspace && python main.py" /bin/bash
```

本地访问 `http://localhost:7860` 即可使用。


## 🤖 学术智能体MCP服务支持

### 🛠️ 预配置的免费学术智能体MCP服务

Academic Agents Studio 基于MCP (Model Context Protocol) 协议，预置集成以下专业学术智能体免费服务，覆盖学术研究的核心需求：

| 服务名称 | 功能描述 | 核心能力 | 使用场景 |
|---------|---------|---------|---------|
| **🎨 学术图表可视化**<br>FreeAcademicChart | 专业的学术数据可视化解决方案 | 支持条形图、折线图、饼图、环状图、雷达图等10+种图表类型；高度定制化标签、数据、颜色和样式；符合学术出版标准 | 研究数据可视化、论文图表制作、学术报告配图、数据分析展示 |
| **🔍 网络搜索服务**<br>FreeWebSearch | 智能化学术信息检索与分析系统 | 多模型检索与语义理解；实时互联网全栈信息检索；专业搜索工程框架集成；提升回答准确性和时效性 | 文献调研与综述、最新研究动态跟踪、政策法规查询、背景资料搜集 |
| **✍️ 学术写作服务**<br>FreeAcademicWrite | 专业的学术文本处理和优化平台 | 学术语料润色与语法优化；智能翻译与语言识别；学术英中互译；语法错误检查与拼写校对 | 论文写作与修改、学术报告优化、研究提案润色、国际期刊投稿准备 |
| **📝 结果格式转换**<br>FreeAcademicFormatter | 智能化的工具结果格式转换与优化 | HTML格式化与Markdown转换；使用默认大模型进行格式化处理；优化前端页面可视化效果 | 工具返回结果展示、学术报告内容格式化、数据可视化预处理 |

### 🚀 使用方法

#### 1. **启用学术智能体功能**
```
在界面中点击"学术智能体"按钮
系统将自动检测和配置所有可用的免费学术智能体服务
```

#### 2. **开始智能对话**
```
启用后直接在输入框中提问
AI会自动选择合适的工具进行调用
实时显示工具调用过程和结果
```

#### 3. **示例对话场景**
```
🎨 数据可视化：
"帮我生成近五年AI论文发表数量的趋势图"
"创建一个展示不同学科研究经费占比的饼图"

🔍 信息搜索：
"搜索最新的深度学习在医疗影像中的应用"
"查找关于气候变化对农业影响的近期研究"

✍️ 文本处理：
"润色这段研究方法的描述"
"将这篇英文摘要翻译成中文"
"检查这段引言的语法错误"

📊 格式转换：
"将这个数据分析结果转换成适合报告的格式"
```

### ⚙️ 高级配置与扩展

#### 自定义服务集成
可以通过修改 `mcp_servers.json` 文件添加自定义学术智能体服务：

```python
# 添加新的学术智能体服务
"custom-academic-agent": AcademicAgentConfig(
    name="自定义学术服务",
    url="https://your-academic-agent.com/api",
    headers={"Authorization": "Bearer your-api-key"},
    description="您的自定义学术智能体服务描述",
    enabled=True
)
```

#### 服务配置示例
所有服务均通过统一的配置文件进行管理，支持动态启用和禁用：

```json
{
    "FreeAcademicWrite": {
        "name": "学术智能体免费学术写作服务",
        "url": "https://academicwrite.freemcps.aiearth.vip/sse",
        "headers": {"Authorization": "Bearer aioagi.tech"},
        "description": "专业的学术文本处理和优化服务",
        "enabled": true
    }
}
```

### 🌍 服务支持范围

#### 多语言支持
- **中文**：完整支持简体中文和繁体中文的学术文本处理
- **英文**：专业的英文学术文本语法检查和优化
- **多语种翻译**：支持主要国际语言的学术内容翻译

#### 学科覆盖
- 计算机科学与人工智能
- 生物医学与生命科学  
- 物理学与材料科学
- 化学与化工技术
- 数学与统计学
- 经济学与管理学
- 人文与社会科学

## 📈 更多学术智能体MCP服务

我们正在积极扩展更多专业学术智能体服务，这些服务将通过我们的免费MCP服务项目对外发布。我们致力于为学术研究提供全面、免费的智能体服务，覆盖学术研究的各个环节。

### 🔬 即将推出的服务

- **📚 学术文献管理服务 (FreeAcademicLibrary)** - 智能文献检索与推荐、引用格式自动生成、文献笔记和标注管理、学术知识图谱构建
- **📊 数据分析服务 (FreeAcademicAnalysis)** - 统计分析工具集成、机器学习模型训练、实验数据处理、结果可视化与解释
- **🤖 学术AI助手服务 (FreeAcademicAssistant)** - 个性化研究建议、学术日程管理、同行评议辅助、研究项目规划
- **🌐 学术协作服务 (FreeAcademicCollaboration)** - 跨机构研究协作、学术资源共享、在线学术会议支持、知识产权保护

### 🎯 长期愿景

我们的目标是构建一个完整的**学术智能体（Academic Agents）生态系统**，涵盖学术研究的全生命周期：

1. **研究前期**：文献调研、选题分析、方案设计
2. **研究过程**：数据收集、实验执行、结果分析
3. **成果产出**：论文写作、图表制作、学术发表
4. **知识传播**：学术交流、同行评议、知识共享

### 🌐 项目地址

更多免费的学术智能体MCP服务将通过我们的专项项目对外发布，欢迎关注和Star：

👉 [https://github.com/AcademicAgentsStudio/Academic-Free-MCP-Servers](https://github.com/AcademicAgentsStudio/Academic-Free-MCP-Servers)

在该项目中，您可以找到：

- **📋 最新服务列表**：所有免费学术智能体MCP服务的完整清单
- **🔧 详细配置指南**：包括服务配置文件和API使用说明
- **🚀 快速开始教程**：从零开始部署和使用所有服务
- **📚 完整技术文档**：每个服务的功能说明、使用场景和API文档
- **🔄 更新日志**：服务版本更新和功能增强记录
- **🐛 问题反馈**：通过GitHub Issues报告问题和提出建议
- **💬 社区支持**：加入我们的学术交流群获取实时帮助

### 🆓 服务特色

- **完全免费**：所有学术智能体服务将对学术用户永久免费开放
- **开箱即用**：提供标准化的MCP协议配置，轻松集成到现有工作流
- **持续更新**：基于用户反馈不断优化和扩展服务功能
- **专业支持**：由学术研究背景的技术团队提供专业支持

> 💡 **提示**：关注我们的MCP服务项目，第一时间获取最新服务更新。所有新服务都将在该项目中先行发布，经过社区测试后集成到主平台中。
> 
> **🌟 让我们一起构建更好的学术研究工具生态！**
> 
> **🎯 立即体验**：访问我们的[在线演示版](https://agents.aiearth.vip)体验完整的学术智能体功能！

---


### Ⅰ：Academic Agents Studio 研发版本:
- version 1.0（2025.9.17-2025.10.24）: 
  - **全新学术智能体界面优化与功能集成** - 科技感UI设计、动态边框发光、毛玻璃效果、智能交互提升、学术智能体外部工具调用、多用户会话隔离

- 已知问题
    - 某些浏览器翻译插件干扰此软件前端的运行
    - 官方Gradio目前有很多兼容性问题，请**使用`requirement.txt`安装Gradio**

### Ⅱ：主题
可以通过修改`THEME`选项（config.py）变更主题
1. `Chuanhu-Small-and-Beautiful` [网址](https://github.com/GaiZhenbiao/ChuanhuChatGPT/)

### Ⅲ：本项目的开发分支

1. `master` 分支: 主分支，稳定版
2. 如何[接入其他大模型](request_llms/README.md)

### V：参考与学习

```
代码中参考了很多其他优秀项目中的设计：

# Qwen-Agent:
https://github.com/QwenLM/Qwen-Agent

# Model Context Protocol:
https://github.com/modelcontextprotocol

# GPT Academic:
https://github.com/binary-husky/gpt_academic

# 清华ChatGLM2-6B:
https://github.com/THUDM/ChatGLM2-6B

# 清华JittorLLMs:
https://github.com/Jittor/JittorLLMs

# ChatPaper:
https://github.com/kaixindelele/ChatPaper

# Edge-GPT:
https://github.com/acheong08/EdgeGPT

# ChuanhuChatGPT:
https://github.com/GaiZhenbiao/ChuanhuChatGPT

# Oobabooga one-click installer:
https://github.com/oobabooga/one-click-installers

# More：
https://github.com/gradio-app/gradio
https://github.com/fghrsh/live2d_demo
```

---

## 🌟 加入我们的社区

欢迎加入 **Academic Agents Studio** 学术智能体社区！在这里您可以：

- 💬 **交流使用心得**：分享使用技巧，获取最佳实践
- 🐛 **反馈问题**：报告Bug，提出改进建议
- 🎯 **功能讨论**：参与新功能设计，提出需求建议
- 📚 **学术交流**：与其他学者交流研究心得
- 🚀 **抢先体验**：第一时间体验新功能和版本更新



### 📱 扫码加入群聊

<div align="center">
<table>
<tr>
<td align="center">
<img src="./docs/images/QQ_group.png" width="200" alt="QQ群二维码"/><br>
<strong>🐧 QQ交流群</strong><br>
<em>Academic Agents学术智能体交流群</em>
</td>
<td align="center">
<img src="./docs/images/Wechat_group.png" width="200" alt="微信群二维码"/><br>
<strong>💬 微信交流群</strong><br>
<em>Academic Agents学术智能体交流群</em>
</td>
</tr>
</table>

</div>

> [!TIP]
> **群聊福利**：
> - 🎁 新用户专享配置指南
> - 📖 独家使用教程和模板
> - 🔥 最新功能抢先测试
> - 💡 一对一技术支持
> - 📊 学术资源分享

### 💌 其他联系方式

- 📧 **邮箱**：aioagi@aioagi.tech
- 🐙 **GitHub Issues**：[提交问题和建议](https://github.com/AcademicAgentsStudio/issues)
- 📝 **文档中心**：[在线文档](https://github.com/AcademicAgentsStudio/Academic-Agents-Studio/wiki)

---


<div align="center">

**🎯 Academic Agents Studio 让AI成为您学术研究的得力助手！**

😊 如果这个项目对您有帮助，请给我们一个 ⭐ Star！

[⬆️ 回到顶部](#academic-agents-Studio)

</div>
