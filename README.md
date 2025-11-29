# 🎯 AI Multi-Agent Interview Simulator for Data Analyst

**数据分析师多面试官智能面试模拟器**

一个面向「数据分析师（Data Analyst）」岗位的多智能体面试模拟系统。通过多个虚拟面试官协同工作，完整还原真实招聘流程，帮助候选人进行高质量的自我练习与能力诊断。

## ✨ 核心功能

### 🤖 多角色面试官协作
- **HR 面试官**: 关注求职动机、简历匹配度、稳定性和沟通表达
- **业务用人经理**: 深挖项目经历，考察业务理解、分析落地和跨部门协作能力
- **技术/分析面试官**: 从统计、SQL、Python、实验设计、指标体系等维度评估技术能力
- **文化契合度面试官**: 评估候选人与团队文化、工作方式、价值观是否匹配
- **终面评审委员会**: 汇总各轮面试结果，给出整体评分、优势分析和改进建议

### 📊 精细化评分体系
- 每位面试官给出 0-10 分量化评分
- 2-4 句针对性改进建议
- 弱项/优势标签系统（如：结构不清晰、SQL细节欠缺、数据思维强等）
- **权重化总分计算**：HR(15%) + 业务经理(25%) + 技术面(35%) + 文化契合度(15%) + 终面(10%)

### 🔄 智能追问机制
- 当回答不够深入时，AI 会自动追问
- 追问深入挖掘你的经历和思考过程
- 帮助你更好地展现自己

### 📄 面试报告导出
- 支持 Markdown / HTML 格式
- 包含完整评分记录、对话历史
- 优劣势分析与改进建议
- 成长追踪对比

### 🧠 长期记忆与个性化诊断
- 为每个用户建立独立档案，记录历史面试表现
- 累积弱项标签，分析长期弱点
- 基于历史数据提供个性化练习建议

## 🚀 快速开始

### 1. 安装依赖

```powershell
cd ai-interview-simulator
pip install -r requirements.txt
```

### 2. 配置 API Key

打开 `config.py`，找到以下行并填入你的 Qwen API Key：

```python
QWEN_API_KEY = "your-api-key-here"  # 替换为你的 API Key
```

> 💡 获取 API Key: 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)

或者通过环境变量设置：

```powershell
$env:QWEN_API_KEY = "your-api-key-here"
```

### 3. 运行面试模拟

**命令行模式：**
```powershell
python main.py
```

**Web UI 模式（推荐）：**
```powershell
python web/app.py
```
然后访问 http://localhost:5000

## 🌐 Web UI 界面

项目提供了现代化的 Web 交互界面：

- **首页**: 用户登录、历史统计、模式选择
- **面试页面**: 实时对话、进度追踪、即时评估
- **历史记录**: 查看过往面试记录和趋势
- **报告页面**: 完整面试报告查看和导出

![Web UI 截图](docs/screenshot.png)

## 📁 项目结构

```
ai-interview-simulator/
├── README.md                 # 项目说明
├── config.py                 # 配置文件（API Key 在这里设置）
├── main.py                   # 程序入口（命令行交互）
├── requirements.txt          # Python 依赖
│
├── core/                     # 核心模块
│   ├── llm_client.py         # Qwen 大模型客户端封装
│   ├── memory.py             # 用户档案 + 会话记忆
│   ├── workflow.py           # 面试流程引擎
│   └── report.py             # 报告生成器
│
├── agents/                   # 面试官 Agent
│   ├── base_agent.py         # 抽象基类
│   ├── hr_agent.py           # HR 面试官
│   ├── hiring_manager_agent.py  # 业务用人经理
│   ├── technical_agent.py    # 技术/分析面试官
│   ├── culture_agent.py      # 文化契合度面试官
│   └── committee_agent.py    # 终面评审委员会
│
├── web/                      # Web UI (新增)
│   ├── app.py                # Flask 后端服务
│   ├── templates/            # HTML 模板
│   │   ├── index.html        # 首页
│   │   ├── interview.html    # 面试页面
│   │   ├── history.html      # 历史记录
│   │   └── report.html       # 报告页面
│   └── static/               # 静态资源
│       ├── css/style.css     # 样式
│       └── js/               # 交互脚本
│
├── data/                     # 数据文件
│   ├── tech_questions.json   # 技术题库（SQL/统计/Python等）
│   ├── behavioral_questions.json  # 行为题库
│   └── role_prompts.json     # 各角色设定
│
└── storage/                  # 持久化存储
    ├── users/                # 用户长期档案
    ├── sessions/             # 面试记录
    └── reports/              # 导出的报告
```

## 🎮 使用示例

```
╔══════════════════════════════════════════════════════════════════╗
║     🎯 AI Multi-Agent Interview Simulator for Data Analyst 🎯    ║
╚══════════════════════════════════════════════════════════════════╝

请输入你的用户ID: alice

==================== 📋 HR 初筛 ====================

🎤 面试官提问:
   请简单介绍一下你自己，以及为什么对数据分析师这个岗位感兴趣？

📝 请输入你的回答:
> 我是 Alice，有 3 年数据分析经验...

──────────────────────────────────────────────────────
📊 本轮评分: 7/10
💬 面试官反馈: 自我介绍结构清晰，但可以更多强调与数据分析相关的具体成就...
✅ 优势标签: 结构清晰, 沟通表达好
⚠️ 待改进标签: 细节不足
──────────────────────────────────────────────────────
```

## 🛠 配置选项

在 `config.py` 中可以修改：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `QWEN_API_KEY` | 通义千问 API Key | 需要填写 |
| `QWEN_MODEL` | 使用的模型 | `qwen-plus` |
| `DEFAULT_POSITION` | 默认面试岗位 | 数据分析师 |

可选模型：
- `qwen-turbo`: 速度快，成本低
- `qwen-plus`: 平衡性能与成本（推荐）
- `qwen-max`: 最强能力

## 📈 后续扩展
- [ ] 语音输入支持
- [ ] 更多岗位支持（Product Analyst, Marketing Analyst 等）
- [ ] 多语言支持

## 📄 License

MIT License
