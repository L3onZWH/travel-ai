# 模型配置 (model.md)

> 此文件为文档说明模型配置意图。
> 实际 API Key 和模型名请在 .env 中配置。

## 主模型

- Provider: Anthropic (Claude)
- 默认模型: claude-opus-4-5
- 环境变量: `ANTHROPIC_MODEL`

## 思考等级

| 等级 | 说明 | 适用场景 |
|------|------|------|
| `off` | 不启用思考 | 简单查询 |
| `fast` | 轻量模型 | 日常对话 |
| `high` | 深度思考 | 复杂规划任务 |

## 备用模型（未来支持）

1. OpenAI gpt-4o
2. DeepSeek deepseek-chat
3. Kimi moonshot-v1-8k
4. Grok grok-beta

## 降级规则

- API 错误连续 2 次 → 尝试备用模型
- 响应超时 30s → 重试一次再降级
