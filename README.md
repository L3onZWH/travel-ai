# 🌍 Travel AI Agent

> 基于 Claude 的智能旅行规划助手，支持多模型、Workspace 隔离、规则驱动、对话持久化。

---

## 📊 开发进度

### Phase 1 — 基础骨溶 `✅ 已完成`

| 任务 | 状态 |
|------|------|
| 项目初始化：uv 环境、目录结构、pyproject.toml、.env 模板 | ✅ |
| `config/settings.py`：API Key、模型名、路径配置 | ✅ |
| `llm/base.py` + `llm/anthropic_llm.py`：Claude API、工具调用循环、流式输出 | ✅ |
| `agent/core.py`：TravelAgent 主类、对话循环 | ✅ |
| `main.py` + CLI：rich 美化输出、prompt_toolkit 输入 | ✅ |

### Phase 2 — Workspace & Memory & Rules `✅ 已完成`

| 任务 | 状态 |
|------|------|
| `agent/workspace.py`：Workspace 创建/切换，目录隔离 | ✅ |
| `memory/manager.py`：Session 持久化，history.json + conversation.md + meta.json | ✅ |
| `agent/session.py`：列出/检索/加载历史 Session | ✅ |
| `agent/rules.py`：解析 rule.md / soul.md，自动注入 system prompt | ✅ |
| CLI 扩展：`/save` `/history` `/load` `/workspace` `/rules` | ✅ |
| `config/rule.md` + `config/soul.md` 配置模板 | ✅ |

### Phase 3 — 工具层 & Web 搜索 `✅ 已完成`

| 任务 | 状态 |
|------|------|
| `tools/base.py`：BaseTool 抓象类、ToolResult 数据类 | ✅ |
| `tools/registry.py`：工具注册/发现，生成 Claude tool_use 格式 | ✅ |
| `llm/anthropic_llm.py`：tool_use 循环（工具调用 → 结果回传）| ✅ |
| `tools/web_search.py`：DuckDuckGo 搜索封装 | ✅ |
| `tools/knowledge_base.py`：知识库读写 | ✅ |

### Phase 3.5 — 测试套件 `✅ 已完成`

| 任务 | 状态 |
|------|------|
| 单元测试：settings / workspace / session / memory / rules / registry / knowledge_base | ✅ |
| 集成测试：Agent+Memory 其合、Workspace 隔离 | ✅ |
| 冒烟测试：真实 API 调用（无 Key 自动跳过）| ✅ |

### Phase 4 — 平台插件 Stub & 方案生成 `🟡 计划中`

| 任务 | 状态 |
|------|------|
| `tools/platforms/base_platform.py`：BasePlatform 接口 | ⏳ |
| `tools/platforms/ctrip_stub.py`：携程模拟机票数据 | ⏳ |
| `tools/platforms/booking_stub.py`：Booking 模拟酒店数据 | ⏳ |
| 性价比方案自动生成 | ⏳ |

### Phase 5 — 安全层 & 审计 `⏳ 计划中`

| 任务 | 状态 |
|------|------|
| 工具白名单（security.md）| ⏳ |
| 参数消毒（路径遍历、注入防护）| ⏳ |
| 审计日志（audit/）| ⏳ |

---

## 环境要求

- Python **3.11+**（推荐通过 conda 管理）
- [uv](https://docs.astral.sh/uv/getting-started/installation/)（用于依赖声明，可选）
- Anthropic API Key

---

## 安装

### 方式一：conda + pip（推荐）

```bash
# 1. 克隆项目
git clone <repo-url>
cd travel-ai

# 2. 创建并激活 conda 环境
conda create -n travel python=3.11
conda activate travel

# 3. 安装依赖
pip install -e .

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key

# 5. 启动
python main.py
```

### 方式二：pip + venv

```bash
# 1. 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate

# 2. 安装依赖
pip install -e .

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key

# 4. 启动
python main.py
```

---

## 配置（.env）

```bash
# 必填
ANTHROPIC_API_KEY=sk-ant-api03-...

# 可选：模型名，默认 claude-opus-4-5
ANTHROPIC_MODEL=claude-opus-4-5

# 可选：代理 / 中转 Base URL
ANTHROPIC_BASE_URL=https://your-proxy.example.com/

# 可选：Tavily 搜索 API Key（不填则用 DuckDuckGo）
TAVILY_API_KEY=
```

---

## 使用

```
🌍  Travel AI Agent  v0.4
智能旅行规划助手

✦ 旅行家
你好！我是你的 AI 旅行顾问「旅行家」🌏

You: 我想去东京，7月份，预算10000元，两个人
✦ 旅行家  ...
```

**命令：**

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/rules` | 查看当前规则（rule.md + soul.md）|
| `/session` | 当前 Session ID |
| `/clear` | 清空对话历史 |
| `/exit` | 退出 |

---

## 配置文件

| 文件 | 说明 | 生效方式 |
|------|------|------|
| `config/rule.md` | 硬性规则，强制注入 system prompt | 下次对话自动生效 |
| `config/soul.md` | 感性偏好：风格/个人信息/软件偏好 | 下次对话自动生效 |
| `config/model.md` | 模型说明（实际值在 .env）| — |

---

## 运行时目录

```
workspace/
├── sessions/<id>/history.json   # 对话历史（自动保存）
├── memory/user_profile.json     # 用户画像
└── knowledge/destinations/      # 知识库缓存
```

---

## 开发

```bash
uv sync --group dev   # 安装开发依赖（需先 conda activate travel）
pip install -e ".[dev]"  # 或用 pip
uv run ruff check .   # 代码检查
uv run mypy .         # 类型检查

# 测试
pytest tests/unit/                    # 单元测试（最快，无需 API Key）
pytest tests/integration/             # 集成测试
pytest -m "not smoke"                 # 全部测试（排除 smoke）
pytest tests/smoke/ -m smoke          # 冒烟测试（需要真实 API Key）
pytest                                # 所有测试
```

### 测试分层

| 层级 | 路径 | 说明 | API Key |
|------|------|------|--------|
| 单元 | `tests/unit/` | 测试各模块独立逻辑，全部 Mock | ✖ 不需要 |
| 集成 | `tests/integration/` | 测试模块协作，LLM Mock | ✖ 不需要 |
| 冒烟 | `tests/smoke/` | 真实 API 调用，无 Key 自动跳过 | ✔ 需要 |

