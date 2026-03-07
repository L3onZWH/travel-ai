# Travel AI Agent — 开发计划

> 版本：v0.4 完整架构版  
> 语言：纯 Python 3.11+  
> LLM：多模型支持（Claude / OpenAI / DeepSeek / Grok / Kimi）  
> 界面：CLI（命令行）  
> 上下文存储：Markdown 文件  
> 架构重点：Workspace 隔离 · 消息队列 Lane · 上下文守卫 · 分层记忆 · 委托式多 Agent · 安全白名单 · 思考等级  

---

## 一、产品目标

构建一个智能旅游助手 Agent，能够：

- 持续对话，给出旅游建议（目的地、行程、性价比方案）
- 通过 Web 搜索获取实时旅游资讯，积累行程知识库
- 规则驱动（`rules.md` / `agents.md` / `soul.md`），支持自定义行为约束和性格偏好
- 插件化平台接入（MVP 仅 stub，未来支持真实下单）
- 上下文持久化（MD 文件），每次对话可恢复；历史上下文自动压缩与每日记忆归档
- Workspace 隔离，每个 Agent 独立运行边界
- 消息队列 Lane 机制，支持多种并发交互策略
- 多模型支持与自动降级，工具安全白名单防提示词攻击
- 架构为未来多模态（图片/语音）及 MCP 能力扩展预留接口

---

## 一点五、核心设计理念

### 1. Workspace — 工作区隔离

- 每个 **Workspace** 代表一个独立的工作边界，不同工作区的对话、记忆、配置互不干扰
- 每个 **Session** 是一次对话实例，持久化为 Markdown 文件，支持随时恢复
- Workspace 目录结构：`workspace/<workspace_id>/sessions/<session_id>/`

### 2. 委托式 Agent 模式

```
用户消息
  │
  ▼
主 Agent（编排层）
  ├─► 分析任务，拆解子任务
  ├─► 委托子 Agent 执行（异步/后台）
  ├─► 立即回复用户进度 + 询问下一步
  └─► 子 Agent 完成后，汇总结果反馈给用户
```

主 Agent 不阻塞等待，委托后即可继续与用户交互，子 Agent 结果以事件方式回传。

### 3. Lane — 消息调度车道

消息队列像车道一样隔离，避免竞争状态，支持四种交互模式：

| 模式 | 说明 |
|------|------|
| `steer` | 插队——排到队列最前面，当前执行完立即执行 |
| `collect` | 收集——在时间窗口内收集多条消息，统一批量执行 |
| `followup` | 顺序——逐一按序执行消息队列中的任务 |
| `interrupt` | 中断——打断当前执行，清空队列，立即执行新指令 |

### 4. 分层记忆体系

```
记忆层级
├── Session 级记忆   → 上下文截断时生成长/短摘要，写入 memory.md
├── Day 级记忆       → 每日对话日记，类似工作日志
└── 任务级记忆       → 触发工作流时更新，记录「如何做某事」
```

Rule / Soul / Memory 三者关系：
- **Rule（规则）**：优先级最高，程序强制执行，注入 system prompt，不依赖 LLM 判断
- **Soul（灵魂）**：感性偏好，记录用户习惯（输出格式、语气、个人信息、喜好软件等）
- **Memory（记忆）**：理性经验，记录工作知识（如何下单、哪里查票、网络错误处理等）
- 反复遇到或用户强调的内容，优先级不断提升（短期 → 长期）

### 5. 思考等级

| 等级 | 说明 | 适用模型示例 |
|------|------|------|
| `off` | 不启用思考 | 任意模型 |
| `fast` | 轻量思考，快速响应 | claude-haiku、gpt-4o-mini |
| `high` | 深度思考，复杂任务 | claude-opus-4、gpt-4.5 |

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      CLI 入口                           │
│                   main.py / cli.py                     │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│                   Lane 消息队列                        │
│   steer │ collect │ followup │ interrupt              │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│              主 Agent（编排 / 委托层）                  │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │ LLM 路由 │  │ 上下文守卫  │  │  Rules 引擎      │  │
│  │多模型降级│  │ 80% 截断   │  │ rule/soul注入    │  │
│  └──────────┘  └────────────┘  └─────────────────┘  │
└──────────────┬───────────────────────┬──────────────┘
               │                       │
┌──────────────▼──────┐   ┌────────────▼─────────────┐
│   子 Agent 委托层    │   │      记忆管理层             │
│  delegator.py       │   │  Session/Day/Task Memory  │
│  后台执行 + 回调     │   │  summary / archive        │
└─────────────────────┘   └──────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│                    Tool 插件层                        │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐ │
│  │WebSearch │ │ Platform  │ │Knowledge │ │  MCP   │ │
│  │ Tavily   │ │携程/Airbnb│ │ Base     │ │ Client │ │
│  └──────────┘ └───────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 三、目录结构

```
travel-ai/
├── main.py                        # CLI 启动入口
├── pyproject.toml                 # 依赖管理 (uv)
├── PLAN.md                        # 本文件
├── README.md
│
├── config/                        # 配置文件目录（用户可编辑）
│   ├── agent.md                   # Agent 交互配置（名称/角色/委托规则）
│   ├── rule.md                    # 硬性行为规则（程序强制执行）
│   ├── soul.md                    # 感性偏好（语气/格式/用户习惯/个人信息）
│   ├── model.md                   # 模型配置（首选/备选/降级规则/API Key/上下文长度）
│   ├── security.md                # 安全白名单策略
│   └── settings.py                # 环境变量与路径配置
│
├── agent/
│   ├── __init__.py
│   ├── core.py                    # 主 Agent，对话编排与委托入口
│   ├── delegator.py               # 子 Agent 委派管理器（委托+异步回调）
│   ├── context_guard.py           # 上下文守卫（Token 计数、80% 截断触发）
│   ├── lane.py                    # 消息队列 Lane（steer/collect/followup/interrupt）
│   ├── rules.py                   # rule.md / soul.md 解析与 system prompt 注入
│   ├── session.py                 # Session 管理（创建/加载/列出）
│   ├── workspace.py               # Workspace 管理（隔离边界）
│   └── thinking.py                # 思考等级切换（off/fast/high）
│
├── llm/
│   ├── __init__.py
│   ├── base.py                    # BaseLLM 抽象接口
│   ├── router.py                  # 模型路由器（首选/降级/上下文长度感知）
│   ├── anthropic_llm.py           # Claude API 封装
│   ├── openai_llm.py              # OpenAI API 封装
│   ├── deepseek_llm.py            # DeepSeek API 封装
│   ├── grok_llm.py                # Grok API 封装
│   └── kimi_llm.py                # Kimi API 封装
│
├── memory/
│   ├── __init__.py
│   ├── manager.py                 # 记忆管理主类（session/day/task 三层）
│   ├── compressor.py              # 上下文压缩器（超 80% 触发，保留最近 50 条）
│   ├── archiver.py                # Day 级记忆归档（每日日记生成）
│   ├── task_memory.py             # 任务级记忆（工作流经验积累）
│   └── token_counter.py           # Token 用量计算（多模型适配）
│
├── tools/
│   ├── __init__.py
│   ├── base.py                    # BaseTool 抽象接口
│   ├── registry.py                # 工具注册表
│   ├── security.py                # 工具安全策略（白名单、参数消毒）
│   ├── web_search.py              # Web 搜索工具
│   ├── knowledge_base.py          # 知识库读写工具
│   ├── skills/                    # 自定义技能扩展
│   │   ├── __init__.py
│   │   └── base_skill.py
│   ├── mcp/                       # MCP 客户端预留接口
│   │   ├── __init__.py
│   │   └── mcp_client.py
│   └── platforms/
│       ├── __init__.py
│       ├── base_platform.py       # 平台插件工厂基类（Channel 接口）
│       ├── booking_stub.py
│       ├── ctrip_stub.py
│       └── airbnb_stub.py
│
├── channel/                       # 第三方接入渠道（插件化工厂）
│   ├── __init__.py
│   ├── base_channel.py            # BaseChannel 抽象（统一消息收发）
│   └── cli_channel.py             # CLI 渠道实现（当前 MVP）
│
├── audit/                         # 审计日志（自动生成）
│   ├── logger.py                  # 结构化审计日志写入
│   └── 2025-07/                   # 按月分文件夹
│       └── 2025-07-01.jsonl
│
└── workspace/                     # 运行时自动生成
    ├── <workspace_id>/            # 工作区隔离目录
    │   ├── sessions/              # 每次对话的 MD 文件
    │   │   └── 2025-07-01_tokyo-trip/
    │   │       ├── conversation.md  # 对话历史（MD 格式）
    │   │       ├── memory.md        # Session 级记忆摘要（长版本）
    │   │       ├── summary.md       # 历史摘要链（短版本，注入上下文）
    │   │       └── meta.json        # Session 元数据
    │   └── memory/
    │       ├── soul.md            # Soul 感性记忆（用户习惯持久化）
    │       ├── long_term.md       # 长期理性记忆（工作经验）
    │       ├── daily/             # Day 级记忆（每日日记）
    │       │   └── 2025-07-01.md
    │       └── tasks/             # 任务级记忆
    │           └── flight_booking.md
    └── knowledge/                 # 搜索结果积累的知识库
        └── destinations/
            └── tokyo.md
```

---

## 四、核心模块详细设计

### 4.1 配置文件体系

#### `config/rule.md` — 硬性规则（最高优先级）

规则由程序强制执行，不依赖 LLM 判断，同时注入 system prompt：

```markdown
## 强制规则
- 每次回答必须包含费用估算
- 禁止推荐未经验证的第三方付款链接
- 推荐行程时按「交通→住宿→景点→餐饮」顺序组织

## 平台规则
- 机票：优先携程、去哪儿
- 住宿：优先 Airbnb
- 禁止推荐无资质的黑车拼车服务
```

#### `config/soul.md` — 感性偏好（用户习惯）

```markdown
## 输出风格
- 喜欢 Markdown / JSON 格式输出
- 不喜欢啰嗦的回复，言简意赅
- 回复中适当使用 emoji

## 个人信息
- 家庭地址：北京市朝阳区
- 公司地址：北京市海淀区中关村
- 生日：1990-01-01

## 软件偏好
- 订票：携程 App
- 地图：高德地图
- 音乐：网易云音乐
```

#### `config/model.md` — 模型配置

```markdown
## 主模型
- provider: anthropic
- model: claude-opus-4
- context_length: 200000
- api_key: ${ANTHROPIC_API_KEY}

## 备用模型（降级顺序）
1. provider: openai, model: gpt-4o, context_length: 128000
2. provider: deepseek, model: deepseek-chat, context_length: 64000
3. provider: kimi, model: moonshot-v1-8k, context_length: 8000

## 降级规则
- 触发条件：API 错误连续 2 次 / 响应超时 30s
- 降级策略：按备用模型列表顺序尝试
- 恢复策略：主模型恢复后自动切回

## 思考等级默认值
- default: fast
```

#### `config/security.md` — 安全白名单

```markdown
## 允许的工具
- web_search
- knowledge_base_read
- knowledge_base_write
- ctrip_query
- booking_query

## 禁止的操作
- 执行任意系统命令
- 访问 workspace 以外的文件路径
- 向未知第三方 URL 发送用户个人信息
```

### 4.2 Lane — 消息队列调度

```python
class LaneMode(Enum):
    STEER     = "steer"     # 插队，当前执行完立即执行
    COLLECT   = "collect"   # 时间窗口内收集，统一执行
    FOLLOWUP  = "followup"  # 顺序逐一执行
    INTERRUPT = "interrupt" # 中断当前，清空队列，立即执行

class MessageLane:
    def enqueue(self, message: Message, mode: LaneMode) -> None: ...
    def get_next(self) -> Message | None: ...
    def interrupt(self, message: Message) -> None: ...
    def collect_window(self, timeout_ms: int) -> list[Message]: ...
```

### 4.3 委托式 Agent 设计

```python
class Delegator:
    """
    主 Agent 委托子 Agent 执行具体任务。
    委托后主 Agent 立即返回，不阻塞用户交互。
    子 Agent 完成后通过回调通知主 Agent。
    """
    def delegate(
        self,
        task: str,
        agent_config: AgentConfig,
        callback: Callable[[AgentResult], None],
    ) -> str:  # 返回 task_id
        ...
    
    def on_complete(self, task_id: str, result: AgentResult) -> None: ...
    def get_status(self, task_id: str) -> TaskStatus: ...
```

**交互流程：**
1. 用户发送复杂请求（如「帮我规划东京行程并查询最近的机票」）
2. 主 Agent 拆解任务：① 行程规划 ② 机票查询
3. 主 Agent 委托子 Agent 执行任务 ①②
4. **立即**回复用户：「正在为您规划行程并查询机票，请稍候，同时告诉我您偏好什么航司？」
5. 用户继续交互，子 Agent 后台运行
6. 子 Agent 完成后，主 Agent 汇总结果，推送给用户

### 4.4 上下文管理与记忆压缩

```python
class ContextGuard:
    COMPRESS_THRESHOLD = 0.80   # 超过 80% 上下文长度时触发
    PRESERVE_RECENT   = 50      # 保留最近 50 条消息不压缩
    
    def check_and_compress(self, session: Session) -> None:
        usage = self.count_tokens(session.messages) / session.model_context_length
        if usage >= self.COMPRESS_THRESHOLD:
            self._persist_memory(session)     # 先持久化记忆
            self._compress_history(session)   # 再压缩历史
    
    def _compress_history(self, session: Session) -> None:
        """将最近 50 条以外的消息整理成摘要，更久远历史替换为 summary block"""
        recent   = session.messages[-self.PRESERVE_RECENT:]
        older    = session.messages[:-self.PRESERVE_RECENT]
        summary  = self.llm.summarize(older)  # 用 LLM 生成摘要
        session.messages = [SummaryBlock(summary)] + recent
    
    def _persist_memory(self, session: Session) -> None:
        """压缩前触发 Memory 持久化：生成长短两版摘要写入 memory.md"""
        long_summary  = self.llm.summarize(session.messages, style="detailed")
        short_summary = self.llm.summarize(session.messages, style="brief")
        session.memory_md.append(long_summary)   # 长版 → memory.md
        session.summary_md.append(short_summary) # 短版 → summary.md（注入上下文）
```

### 4.5 分层记忆管理

```python
class MemoryManager:
    """
    三层记忆：Session 级 / Day 级 / Task 级
    """
    # Session 级：上下文截断时自动触发
    def save_session_memory(self, session_id, long_summary, short_summary): ...
    
    # Day 级：每天对话结束后归档（类似日记）
    def archive_daily(self, date: str, sessions: list[Session]): ...
    
    # Task 级：触发新工作流时更新，记录「如何完成某任务」
    def update_task_memory(self, task_type: str, experience: str): ...
    
    # Soul 更新：用户偏好/习惯发生变化时写入
    def update_soul(self, preference_key: str, value: str): ...
    
    # 反复强化的内容提升优先级
    def reinforce(self, memory_key: str) -> None: ...
```

**记忆优先级机制：**
- 每条记忆维护一个 `reinforcement_count`（强化次数）
- 用户反复提及或显式要求记住的内容，`reinforcement_count += 1`
- 超过阈值的记忆晋升为「核心记忆」，始终注入 system prompt
- 长期未访问的记忆降权，避免 prompt 膨胀

### 4.6 LLM 路由层

```python
class LLMRouter:
    """
    多模型路由：首选模型 → 按降级规则切换 → 自动恢复
    """
    def chat(self, messages, system, thinking: ThinkingLevel) -> str:
        for llm in self._get_candidates(thinking):
            try:
                return llm.chat(messages, system)
            except (APIError, TimeoutError):
                self._record_failure(llm)
                continue
        raise AllModelsFailedError()
    
    def _get_candidates(self, thinking: ThinkingLevel) -> list[BaseLLM]:
        """根据思考等级筛选合适的模型（fast 用轻量模型，high 用大模型）"""
        ...

class ThinkingLevel(Enum):
    OFF  = "off"   # 不启用思考
    FAST = "fast"  # 轻量快速（haiku、gpt-4o-mini）
    HIGH = "high"  # 深度思考（opus-4、gpt-4.5）
```

### 4.7 Memory 层 — MD 文件存储

每个 session 对应一个目录，`conversation.md` 格式：

```markdown
# Session: Tokyo Trip Planning
- 创建时间: 2025-07-01 10:00
- 目的地: 东京
- Workspace: default

## 历史摘要（自动生成）
> [2025-07-01 10:00–10:30] 用户询问东京5日游预算规划，确认预算8000元，偏好公共交通和青旅。

## 对话记录

### [User] 2025-07-01 10:31
我想去东京玩5天，预算8000元

### [Assistant] 2025-07-01 10:31
为您规划东京5日游，预算8000元方案如下...
```

### 4.8 Tool 插件层

```python
class BaseTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema
    
    def execute(self, **kwargs) -> ToolResult: ...
```

**MVP 内置工具：**

| 工具               | 类                   | 说明                |
| ---------------- | ------------------- | ----------------- |
| web_search       | `WebSearchTool`     | 搜索实时旅游资讯          |
| save_knowledge   | `KnowledgeBaseTool` | 保存搜索结果到本地 MD      |
| search_knowledge | `KnowledgeBaseTool` | 检索已有知识库           |
| booking_query    | `BookingStub`       | 查询酒店（stub，返回模拟数据） |
| ctrip_query      | `CtripStub`         | 查询机票（stub，返回模拟数据） |

### 4.9 Channel — 渠道插件工厂

```python
class BaseChannel(ABC):
    """
    统一消息收发接口，屏蔽底层渠道差异。
    MVP 仅实现 CLI，未来扩展微信/飞书/Web 等。
    """
    def receive(self) -> Message: ...
    def send(self, message: Message) -> None: ...
    def send_progress(self, text: str) -> None: ...  # 进度通知

class CliChannel(BaseChannel): ...
# 未来扩展：WechatChannel / FeishuChannel / WebChannel
```


### 4.5 CLI 界面

```
$ python main.py

🌍 Travel AI Agent v0.1
─────────────────────────
[s] 新建对话  [l] 加载历史  [q] 退出
> s

对话主题（回车跳过）: 东京5日游规划

[Travel AI]: 你好！我是你的旅游助手。请问你想去哪里旅行？预算大概是多少？

[You]: 我想去东京，7月份，预算10000元，两个人

[Travel AI]: 正在搜索东京7月旅游信息... 🔍
好的，我来为你规划一个性价比高的东京双人5日游方案...

[You]: /save     # 保存当前对话
[You]: /search   # 触发网络搜索
[You]: /rules    # 查看当前规则
[You]: /history  # 列出历史会话
[You]: /exit     # 退出
```

---

## 五、技术选型

| 类别      | 选型                                        | 理由        |
| ------- | ----------------------------------------- | --------- |
| 语言      | Python 3.11+                              | 需求指定      |
| 包管理     | uv + pyproject.toml                       | 现代、快速     |
| LLM SDK | `anthropic` / `openai` 官方库               | 多模型支持     |
| Web 搜索  | `duckduckgo-search` (免费) + Tavily API（可选） | 无需 key 可用 |
| CLI 框架  | `rich` + `prompt_toolkit`                 | 美观交互      |
| 配置管理    | `python-dotenv` + `pydantic-settings`     | 简洁安全      |
| MD 解析   | 内置 str 操作（MVP）                            | 避免过度依赖    |
| 消息队列    | `asyncio.Queue`（单进程内）                     | 轻量、无外部依赖  |
| 并发模型    | `asyncio` 协程                              | 委托式非阻塞交互  |
| 测试      | `pytest` + `pytest-asyncio`               | 标准        |
| 代码质量    | `ruff` + `mypy`                           | 统一规范      |


**依赖清单（pyproject.toml）：**

```toml
[project]
name = "travel-ai"
version = "0.4.0"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "openai>=1.30.0",
    "duckduckgo-search>=6.0.0",
    "rich>=13.0.0",
    "prompt-toolkit>=3.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.6.0",
    "mypy>=1.10.0",
]
```

---

## 六、多模态扩展预留（非 MVP）

在 `BaseLLM` 和 `BaseTool` 中预留多模态接口：

```python
@dataclass
class Message:
    role: str
    content: str | list[ContentBlock]  # 支持 text/image/audio block
    
@dataclass
class ImageBlock:
    type: Literal["image"]
    source: str  # url or base64
    
# CLI 未来可接入:
# - 用户粘贴图片（景点/地图截图）
# - 输出生成图文行程 PDF
```

---

## 七、平台插件扩展设计（非 MVP）

```python
class BasePlatform(ABC):
    platform_name: str
    
    def search_flights(self, origin, dest, date, passengers) -> list[FlightResult]: ...
    def search_hotels(self, city, checkin, checkout, guests) -> list[HotelResult]: ...
    def create_order(self, item_id, user_info) -> OrderResult: ...
    def get_auth_url(self) -> str: ...  # OAuth 登录
```

MVP Stub 返回模拟数据，真实接入时只需实现对应平台类。

---

## 七点五、安全策略

采用 **白名单模式**——只记录明确允许的操作，未在白名单中的行为一律拒绝。

```
安全层级：
1. 工具白名单（security.md）   → 只有显式允许的工具才能调用
2. 参数消毒（tools/security.py）→ 路径遍历、注入攻击防护
3. System Prompt 注入防护       → 用户输入与系统指令严格分离
4. 审计日志（audit/）           → 所有工具调用记录可追溯
```

`security.md` 示例：
```markdown
## 允许的工具
- web_search
- knowledge_base_read
- knowledge_base_write
- ctrip_query
- booking_query

## 路径访问限制
- 只允许读写 workspace/ 目录
- 禁止访问系统目录（/etc, /root 等）

## 网络访问限制
- 只允许访问白名单域名（携程、Booking、Tavily 等）
```

---

## 八、开发日程安排

### Phase 1 — 基础骨架（第 1 周，Day 1–3）

**目标：能跑起来的最小对话循环**


| Day   | 任务                                                               | 产出      |
| ----- | ---------------------------------------------------------------- | ------- |
| Day 1 | 项目初始化：uv 环境、目录结构、pyproject.toml、.env 模板、.gitignore               | 可运行空项目  |
| Day 1 | `config/settings.py`：API Key、模型名、路径配置（pydantic-settings）         | 配置模块    |
| Day 2 | `llm/base.py` + `llm/anthropic_llm.py`：封装 Claude API，支持多轮消息、流式输出 | LLM 模块  |
| Day 2 | `agent/core.py`：TravelAgent 主类，基础对话循环（内存中）                       | 可对话     |
| Day 3 | `main.py` + CLI 框架：rich 美化输出，prompt_toolkit 输入，基础命令（/exit）       | MVP CLI |
| Day 3 | 联调测试：完整跑通一次旅游对话                                                  | 冒烟测试通过  |


**验收标准：** `python main.py` 启动后可持续与 Claude 对话，讨论旅游话题。

---

### Phase 2 — Workspace & Memory & Rules（第 1 周，Day 4–5）

**目标：对话可持久化，Workspace 隔离，规则配置生效**

| Day   | 任务                                                              | 产出         |
| ----- | --------------------------------------------------------------- | ---------- |
| Day 4 | `agent/workspace.py`：Workspace 创建/切换，目录隔离                      | Workspace  |
| Day 4 | `memory/manager.py`：Session 级记忆，conversation.md / memory.md 格式 | Memory 模块  |
| Day 4 | `agent/session.py`：列出历史 session，按名称/日期检索                       | Session 管理 |
| Day 4 | CLI 命令扩展：`/save`、`/history`、`/load <id>`、`/workspace <name>`   | 持久化命令      |
| Day 5 | `config/rule.md` + `config/soul.md` 模板创建                        | 配置模板       |
| Day 5 | `agent/rules.py`：解析 rule.md / soul.md，生成 system prompt 片段      | 规则引擎       |
| Day 5 | 集成测试：加载旧 session 继续对话，规则生效验证                                   | 集成测试       |

**验收标准：** 退出重进后可恢复历史对话；不同 Workspace 对话不串台；修改 rule.md 后 Agent 行为改变。

---

### Phase 3 — 工具层 & Web 搜索（第 2 周，Day 6–8）

**目标：Agent 能主动搜索，积累知识库**


| Day   | 任务                                                          | 产出          |
| ----- | ----------------------------------------------------------- | ----------- |
| Day 6 | `tools/base.py`：BaseTool 抽象类，ToolResult 数据类                 | 工具基类        |
| Day 6 | `tools/registry.py`：工具注册/发现机制，生成 Claude tool_use 格式         | 工具注册表       |
| Day 6 | `llm/anthropic_llm.py` 升级：支持 tool_use 循环（工具调用 → 结果回传）       | LLM Tool 支持 |
| Day 7 | `tools/web_search.py`：DuckDuckGo 搜索封装，返回结构化结果               | 搜索工具        |
| Day 7 | `tools/knowledge_base.py`：保存搜索摘要到 `context/knowledge/`，支持检索 | 知识库工具       |
| Day 8 | `agent/core.py` 集成工具调用：Agent 自主决定何时搜索                       | 工具集成        |
| Day 8 | CLI 显示工具调用过程（`🔍 正在搜索...`），rich 格式化搜索结果                     | UX 优化       |


**验收标准：** 问「东京7月天气」时 Agent 自动搜索并给出准确答案；知识被保存到本地 MD。

---

### Phase 4 — 平台插件 Stub & 方案生成（第 2 周，Day 9–10）

**目标：性价比方案输出，平台接入框架就绪**


| Day    | 任务                                                    | 产出           |
| ------ | ----------------------------------------------------- | ------------ |
| Day 9  | `tools/platforms/base_platform.py`：BasePlatform 接口定义  | 平台基类         |
| Day 9  | `tools/platforms/ctrip_stub.py`：返回模拟机票数据（含价格/时间/航司）   | 携程 Stub      |
| Day 9  | `tools/platforms/booking_stub.py`：返回模拟酒店数据（含价格/评分/位置） | Booking Stub |
| Day 9  | `tools/platforms/airbnb_stub.py`：返回模拟民宿数据             | Airbnb Stub  |
| Day 10 | System Prompt 优化：注入「性价比导向」、「费用明细」、「比较方案」指令            | 提示工程         |
| Day 10 | 输出格式化：生成结构化行程表（Markdown 表格，含费用汇总）                     | 方案输出         |
| Day 10 | CLI 命令 `/plan` ：触发完整行程规划流程                            | 规划命令         |


**验收标准：** 输入目的地+预算+天数，输出含交通/住宿/景点/餐饮的完整费用明细方案。

---

### Phase 5 — Lane & 委托 & 多模型（第 3 周，Day 11–12）

**目标：消息调度车道就绪，委托式多 Agent 可用，多模型降级生效**

| Day    | 任务                                                                              | 产出       |
| ------ | ------------------------------------------------------------------------------- | -------- |
| Day 11 | `agent/lane.py`：Lane 消息队列实现（steer/collect/followup/interrupt）                  | Lane 模块  |
| Day 11 | `agent/delegator.py`：主 Agent 委托子 Agent，asyncio 后台执行 + 回调                      | 委托模块     |
| Day 11 | CLI 集成 Lane：`interrupt` 命令（`/stop` 中断当前任务）                                    | UX 命令    |
| Day 12 | `llm/openai_llm.py` + `llm/deepseek_llm.py` + `llm/grok_llm.py` + `llm/kimi_llm.py` | 多模型封装    |
| Day 12 | `llm/router.py`：模型路由器，读取 model.md，支持自动降级与恢复                                   | 模型路由     |
| Day 12 | `agent/thinking.py`：思考等级（off/fast/high）切换，影响模型选择                              | 思考等级     |

**验收标准：** `/stop` 可中断当前 Agent 任务；委托子任务后主 Agent 立即响应用户；切换模型降级策略生效。

---

### Phase 6 — 上下文压缩 & 分层记忆（第 3 周，Day 13–14）

**目标：上下文自动压缩，三层记忆体系完整**

| Day    | 任务                                                                | 产出      |
| ------ | ----------------------------------------------------------------- | ------- |
| Day 13 | `memory/compressor.py`：80% 触发压缩，保留最近 50 条，旧消息生成摘要                | 上下文压缩   |
| Day 13 | 压缩前触发记忆持久化：长摘要写 memory.md，短摘要写 summary.md                        | 记忆持久化   |
| Day 14 | `memory/archiver.py`：Day 级记忆，每日对话结束后生成日记                          | 每日归档    |
| Day 14 | `memory/task_memory.py`：任务级记忆，工作流触发时更新（如「如何在携程下单」）               | 任务记忆    |
| Day 14 | Soul 更新机制：检测用户偏好变化自动写入 soul.md；记忆强化计数，核心记忆始终注入 system prompt | 记忆强化    |

**验收标准：** 长对话自动触发压缩；多天对话后 daily/ 有归档；任务记忆在下次同类任务时被正确注入。

---

### Phase 7 — 安全 & 打磨 & 文档（第 4 周，Day 15–17）

**目标：安全策略就绪，稳定可用，文档完善**

| Day    | 任务                                                  | 产出        |
| ------ | --------------------------------------------------- | --------- |
| Day 15 | `tools/security.py`：白名单校验、参数消毒、路径访问控制               | 安全模块      |
| Day 15 | `config/security.md` 模板：允许工具 / 域名白名单                | 安全配置      |
| Day 15 | 错误处理：网络超时、API 限流、文件权限异常统一处理                         | 健壮性       |
| Day 16 | 单元测试：LLM mock、工具测试、memory 读写测试、lane 调度测试            | pytest 覆盖 |
| Day 16 | 集成测试：完整对话流程 E2E 测试，含委托/压缩/多模型切换                     | E2E 测试    |
| Day 17 | README.md 更新：安装/配置/使用文档，config/ 各 md 文件注释详解         | 使用文档      |
| Day 17 | CHANGELOG.md，架构决策记录（ADR）                           | 项目文档      |

**验收标准：** 新用户按 README 5分钟内跑起来；所有核心路径有测试覆盖；安全白名单拦截非法工具调用。

---

### Phase 8 — 打磨 & 文档（第 4 周，Day 15–17，合并至 Phase 7）

> 已合并到 Phase 7，见上。

---

## 九、关键里程碑

| 里程碑                     | 日期     | 验收标准                           |
| ----------------------- | ------ | ------------------------------ |
| M1: Hello Agent         | Day 3  | CLI 启动，与 Claude 旅游对话           |
| M2: Workspace Ready     | Day 5  | 对话持久化，Workspace 隔离，规则驱动行为      |
| M3: Search Ready        | Day 8  | 自动 Web 搜索，知识积累                 |
| M4: MVP Complete        | Day 10 | 输出完整性价比行程方案                    |
| M5: Lane & Delegate     | Day 12 | 消息调度 Lane 就绪，委托式子 Agent 可用，多模型切换 |
| M6: Memory Full         | Day 14 | 三层记忆体系完整，上下文自动压缩，记忆强化生效       |
| M7: Production Ready    | Day 17 | 安全白名单就绪，测试通过，文档完善              |


---

## 十、风险与应对


| 风险               | 概率  | 应对                       |
| ---------------- | --- | ------------------------ |
| DuckDuckGo 搜索被限流 | 中   | 降级到 Tavily API（需 key）或缓存 |
| Claude API 费用超预期 | 低   | 配置 max_tokens，搜索结果预处理压缩  |
| MD 文件并发写入冲突      | 低   | MVP 单进程，加文件锁预留           |
| tool_use 循环卡死    | 低   | 设置最大迭代次数（默认 5 次）         |


---

## 十一、未来路线图（Post-MVP）

```
v0.5 — 真实平台接入（Channel 插件化）
  └── 携程/去哪儿机票 API
  └── Booking.com Affiliate API
  └── OAuth 登录流程
  └── Channel 工厂：WechatChannel / FeishuChannel

v0.6 — 多模态支持
  └── 用户上传景点图片识别
  └── 地图截图解析行程
  └── 输出图文 PDF 行程单

v0.7 — Web 前端
  └── FastAPI 后端
  └── React/Next.js 前端
  └── 流式对话 SSE
  └── WebChannel 接入

v0.8 — 多用户 & 协作
  └── 用户账户系统 + 独立 Workspace
  └── 多人共享行程规划
  └── 向量数据库替代 MD 知识库（Memory 向量化检索）

v0.9 — MCP 生态
  └── tools/mcp/ 接入标准 MCP 工具
  └── 第三方 MCP Server 热插拔
```

---

*文档最后更新：2025-07-02*  
*负责人：Travel AI Team*

---

## 十二、当前实现状态（代码审查快照）

> 基于代码库实际文件审查更新，反映当前真实进度。

### 已完成模块 ✅


| 模块       | 文件                        | 状态   | 备注                                       |
| -------- | ------------------------- | ---- | ---------------------------------------- |
| 全局配置     | `config/settings.py`      | ✅ 完成 | pydantic-settings，默认模型 `claude-opus-4-5` |
| LLM 层    | `llm/anthropic_llm.py`    | ✅ 完成 | chat / stream / raw_chat，最多 8 轮工具循环      |
| 工具基类     | `tools/base.py`           | ✅ 完成 | BaseTool 抽象类 + ToolResult 数据类            |
| 工具注册     | `tools/registry.py`       | ✅ 完成 | register / execute / to_claude_schemas   |
| Web 搜索   | `tools/web_search.py`     | ✅ 完成 | Tavily API 封装                            |
| 知识库      | `tools/knowledge_base.py` | ✅ 完成 | 读取本地 `context/knowledge/` 文件             |
| 记忆管理     | `memory/manager.py`       | ✅ 完成 | 会话历史 + 跨会话用户画像持久化（JSON）                  |
| Agent 主控 | `agent/core.py`           | ✅ 完成 | 对话编排，system prompt 注入                    |
| 规则引擎     | `agent/rules.py`          | ✅ 完成 | 从 `rules.md` 加载规则                        |


### 与原计划的差异 ⚠️


| 差异点       | 计划                        | 实际                                            |
| --------- | ------------------------- | --------------------------------------------- |
| Memory 路径 | `agent/memory.py`         | `memory/manager.py`（独立模块）                     |
| 持久化格式     | Markdown 文件               | JSON 文件（`history.json` / `user_profile.json`） |
| 最大工具轮次    | 5 次                       | 8 次（`MAX_TOOL_ROUNDS = 8`）                    |
| 默认模型      | `claude-3-5-sonnet`       | `claude-opus-4-5`                             |
| 平台插件      | `tools/platforms/` (Stub) | 尚未实现                                          |


### 待开发项 📋

- 平台插件 Stub（携程 / Booking / Airbnb）
- CLI 入口 `main.py`（当前缺少或待完善）
- `/plan`、`/history`、`/load` 等 CLI 命令
- 更多目的地知识库文件（`context/knowledge/destinations/`）
- 单元测试 & 集成测试（pytest）
- 错误处理统一化（网络超时、API 限流）
- README.md 完善

