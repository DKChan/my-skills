# DK's Skills

个人 Claude Code Skill 仓库，存放自定义的工作流和领域专用技能。

## 可用 Skills

| Skill | 描述 |
|-------|------|
| `openspec-to-beads` | 将 OpenSpec 规划产物转换为 Beads 可执行任务图。智能检测变更类型、估算工作量、创建合理粒度的 Epic/Task 层级。 |

## 使用方式

将此仓库路径添加到 Claude Code 配置：

```bash
claude config set skills.directories "$(pwd)"
```

或在 `~/.claude/settings.json` 中配置：

```json
{
  "skills": {
    "directories": ["/home/dministrator/code/my-skills"]
  }
}
```

## 目录结构

```
my-skills/
├── README.md
└── {skill-name}/
    └── SKILL.md      # Skill 定义文件（必需）
```

## 开发规范

- 每个 skill 独立目录，核心文件为 `SKILL.md`
- frontmatter 必须包含 `name` 和 `description`
- 推荐添加 `triggers` 列表提高触发准确性
- 文档使用中文（专用名词除外）