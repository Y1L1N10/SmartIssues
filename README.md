# SmartIssues

AI 驱动的 GitHub Issues 智能分析工具。

## 核心功能

- **智能分析**: Claude AI 自动分类、评估优先级、生成摘要
- **报告生成**: Markdown 格式的详细报告和 Todo 列表
- **多 API 支持**: 支持 Anthropic 和 OpenRouter
- **批量处理**: 支持多仓库批量分析
- **本地缓存**: 避免重复 API 调用

## 快速开始

### 安装

```bash
git clone https://github.com/Y1L1N10/SmartIssues.git
cd SmartIssues
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
```

编辑 `.env`:

```bash
# GitHub Token (必填)
GITHUB_TOKEN=ghp_xxx

# API 提供商: anthropic 或 openrouter
API_PROVIDER=openrouter

# OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-xxx

# 或 Anthropic API Key
# ANTHROPIC_API_KEY=sk-ant-xxx

# 模型 (可选)
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### 使用

```bash
# 检查配置
python cli.py check

# 分析 Issues (控制台输出)
python cli.py analyze owner/repo -n 10

# 生成报告
python cli.py analyze owner/repo -f report -o report.md

# 生成 Todo 列表
python cli.py analyze owner/repo -f todo -o todo.md
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `analyze <repo>` | 分析仓库 Issues |
| `check` | 检查 API 连接 |
| `info <repo>` | 查看仓库信息 |
| `cache` | 管理本地缓存 |

### analyze 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-n, --max-issues` | 最大 Issue 数量 | 30 |
| `-f, --format` | 输出格式 (console/report/todo) | console |
| `-o, --output` | 输出文件路径 | - |
| `--state` | 状态过滤 (open/closed/all) | open |
| `-l, --labels` | 标签过滤 | - |
| `--no-cache` | 禁用缓存 | false |

## 输出示例

### 分析结果

每个 Issue 包含:
- **分类**: bug/feature/enhancement/documentation 等
- **优先级**: critical/high/medium/low
- **工作量**: trivial/small/medium/large/extra-large
- **摘要**: 2-3 句话总结
- **行动项**: 具体待办事项
- **阻塞项**: 潜在障碍

### AI 推荐

批量分析后自动生成:
- 项目健康度评估
- 优先处理建议
- Quick Wins (高价值低成本任务)

## 项目结构

```
SmartIssues/
├── src/
│   ├── config.py          # 配置管理
│   ├── github_client.py   # GitHub API
│   ├── processor.py       # AI 分析
│   ├── formatter.py       # 输出格式化
│   ├── cache.py           # 缓存管理
│   └── utils.py           # 工具函数
├── templates/             # Jinja2 模板
├── tests/                 # 单元测试
├── cli.py                 # CLI 入口
└── .env.example           # 配置模板
```

## 开发

```bash
# 运行测试
pytest tests/ -v

# 代码检查
ruff check .
```

## License

MIT
