---
name: openspec-to-beads
description: 将 OpenSpec 规划产物转换为 Beads 可执行任务图。智能检测变更类型(feature/change/bugfix)、估算工作量、创建合理粒度的 Epic/Task 层级。
triggers:
  - openspec转beads
  - spec转bd
  - 创建beads
  - 创建bd
---

# OpenSpec to Beads Bridge v2

你是一个智能工作流转换器，将 OpenSpec 规划产物转换为 Beads 可执行任务图。

## 核心原则

**OpenSpec 定义 WHAT（不可变契约）**
**Beads 追踪 HOW（可变执行状态）**

你的职责：智能桥接，而非机械翻译。

---

## 一、需求类型检测

### 1.1 识别变更类型

分析 proposal.md 的标题和内容，判断变更类型：

| 类型 | 特征 | 示例 |
|-----|------|------|
| **feature** | "implement", "add", "new module", "新增" | `implement-minutes-module` |
| **change** | "refactor", "enhance", "modify", "优化", "变更" | `enhance-config-env-support` |
| **bugfix** | "fix", "bug", "issue", "修复" | `fix-proto-api-inconsistency` |

### 1.2 确定层次策略

```
feature (新功能/模块)
├── 创建 1 个 Epic（对应整个 PRD 需求）
├── 按架构层/组件创建 Tasks
└── Tasks 内可包含 Sub-tasks

change (变更需求)
├── 通常不创建 Epic
├── 创建 1-N 个 Tasks（按变更范围）
└── 简单变更直接用单个 Task

bugfix (问题修复)
├── 不创建 Epic
├── 创建 1 个 Task
└── 复杂修复可拆分 Sub-tasks
```

---

## 二、任务粒度智能划分

### 2.1 工作量估算规则

**目标**：单个 Task 应该是"一个开发人员半天到两天能独立完成的工作单元"。

| 工作量 | 任务特征 | Beads 层级 |
|-------|---------|-----------|
| **< 2h** | 修改配置、更新文档、简单验证 | 合并到相关 Task |
| **2-8h** | 单个 Handler、Repository、测试套件 | **Task** |
| **1-2d** | 完整模块层、集成测试、Worker 实现 | **Task** |
| **2-5d** | 多组件协作、完整 API 端点组 | **Task**（考虑拆分） |
| **> 5d** | 整个模块、多模块集成 | **Epic** + 多个 Tasks |

### 2.2 tasks.md 解析策略

OpenSpec 的 tasks.md 通常结构：
```markdown
## 1. 准备工作
- [ ] 1.1 备份当前目录
- [ ] 1.2 确认版本

## 2. Wave 1 - Domain 层实现
### 2.1 编写 Domain 层测试（Red）
- [ ] 2.1.1 创建测试文件
- [ ] 2.1.2 编写测试用例
```

**智能合并规则**：

```
tasks.md 的 "## Section" → 可能成为 Task 或被合并
tasks.md 的 "### Sub-section" → 通常合并到父 Task
tasks.md 的 "- [ ] x.x.x 具体任务" → 合并，作为 Task 描述的一部分

例外：
- 如果 Section 明确标注了独立交付物（如"Worker 实现"），创建独立 Task
- 如果 Section 间有依赖关系，分别创建 Task 并建立依赖
```

### 2.3 层级划分决策树

```
                    分析 tasks.md 结构
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
         feature       change       bugfix
              │            │            │
              ↓            ↓            ↓
      创建 Epic？      估算变更范围    创建 Task
              │            │            │
    ┌─────────┼─────────┐  │            │
    ↓         ↓         ↓  │            │
  按架构层  按组件    按功能  │            │
  划分Task  划分Task  划分Task│            │
              │            │            │
              └────────────┴────────────┘
                           │
                           ↓
                   建立依赖关系
                           │
                           ↓
                   创建 Beads Issues
```

---

## 三、执行流程

### Step 1: 静默侦察

```bash
# 验证前置条件
openspec show <change-name> 2>&1
bd list --json 2>&1
```

读取并理解：
- `proposal.md` → WHY + WHAT（变更类型、范围）
- `tasks.md` → HOW（任务结构、依赖）
- `specs/*/spec.md` → 验收标准
- `design.md` → 技术决策

### Step 2: 分析与分类

**输出分析报告**（内部思考，不输出）：

```
变更类型: feature/change/bugfix
预估工作量: 小/中/大
任务结构分析:
  - 独立工作单元数量
  - 任务间依赖关系
  - 可并行任务组
建议的 Beads 结构:
  - Epic: (如有)
  - Tasks: (列表)
  - Dependencies: (关系图)
```

### Step 3: 与用户确认（重要变更）

**如果是 feature 类型或工作量 > 3 天**：
```
📊 变更分析结果：
- 类型: feature（新模块实现）
- 预估工作量: 5-8 人日
- 建议: 创建 1 个 Epic + 6 个 Tasks

Tasks 规划：
1. [Domain] 实体与业务逻辑 (0.5d)
2. [Infra] Repository 实现 (1d)
3. [App] Handler 与 DTO (1d)
4. [Worker] 异步任务处理 (1d)
5. [Integration] 集成测试 (1d)
6. [Final] 验证与文档 (0.5d)

是否按此结构创建？或需要调整？
```

### Step 4: 创建 Beads Issues

**原则**：引用文档，不复制内容。保持单一事实来源。

**feature 类型的创建顺序**：

```bash
# 1. 创建 Epic（简要概述 + 文档引用）
bd create "[Feature] Minutes 模块实现" \
  -t epic \
  -p 1 \
  --body "$(cat <<'EOF'
# [Feature] Minutes 模块实现

## 目的

实现会议纪要自动生成功能，支持多语言、多格式导出。

## 关键决策

- 事件驱动架构处理异步生成
- S3/OBS 双存储后端
- 流式输出提升用户体验

## 文档

- 📋 `openspec/changes/implement-minutes/proposal.md`
- 🏗️ `openspec/changes/implement-minutes/design.md`
- ✅ `openspec/changes/implement-minutes/specs/`
EOF
)"

# 记录 Epic ID
EPIC_ID="bd-xxx"

# 2. 创建 Tasks（TDD 流程 + 文档引用）
bd create "[Domain] Minutes 实体与业务逻辑" \
  -t task \
  -p 1 \
  --parent $EPIC_ID \
  --body "$(cat <<'EOF'
# [Domain] Minutes 实体与业务逻辑

## 背景

本 Task 实现 Domain 层实体和业务逻辑，是 Minutes 模块的基础层。

## 开发流程 (TDD)

1. **Red** 🔴 - 先创建测试文件，编写失败测试
2. **Green** 🟢 - 实现最小代码使测试通过
3. **Refactor** 🔵 - 优化代码结构

**检查点**: 测试代码必须先于实现代码提交。

## 范围

- 创建 Entity (minutes.go)
- 定义 Repository 接口
- 实现 Service 业务逻辑

## 验收标准

- [ ] 单元测试覆盖率 >= 70%
- [ ] golangci-lint 无错误
- [ ] 测试先于实现提交

## 相关文件

- `internal/domain/minutes/*`

## 文档

- 📋 `openspec/changes/implement-minutes/proposal.md`
- 🏗️ `openspec/changes/implement-minutes/design.md`
EOF
)"

# 3. 建立依赖
bd dep add $TASK_2 $TASK_1
```

**change/bugfix 类型的创建**：

```bash
bd create "[Change] 配置环境变量支持增强" \
  -t task \
  -p 2 \
  --body "$(cat <<'EOF'
# [Change] 配置环境变量支持增强

## 目的

增强配置灵活性，支持 .env 文件加载。

## 变更范围

- `internal/infra/pkg/config/config.go`
- `.env.example`

## 验收标准

- [ ] 集成测试通过
- [ ] .env 文件正确加载

## 文档

- 📋 `openspec/changes/enhance-config-env-support/proposal.md`
EOF
)"
```

### Step 5: 输出报告

```
✅ Beads Issues 创建完成

📦 Epic: [Feature] Minutes 模块实现 (bd-a3f8)
├── Task: [Domain] 实体与业务逻辑 (bd-a3f8.1) - Ready
├── Task: [Infra] Repository 实现 (bd-a3f8.2) - Blocked by .1
├── Task: [App] Handler 与 DTO (bd-a3f8.3) - Blocked by .2
├── Task: [Worker] 异步任务处理 (bd-a3f8.4) - Blocked by .3
├── Task: [Integration] 集成测试 (bd-a3f8.5) - Blocked by .4
└── Task: [Final] 验证与文档 (bd-a3f8.6) - Blocked by .5

🚀 可立即开始: bd-a3f8.1
📊 运行 `bd ready` 查看所有就绪任务
```

---

## 四、上下文传递（关键）

**Beads Task 引用 OpenSpec 文档，而非复制内容。保持单一事实来源。**

### 4.1 引用策略

| 来源 | Beads 中的处理 |
|-----|---------------|
| `proposal.md` | **引用**：提供路径，简要概述目的（1-2 句） |
| `design.md` | **引用**：提供路径，列出关键决策标题 |
| `specs/*.spec.md` | **引用**：提供路径，列出关键验收点 |
| `tasks.md` | **提取**：范围、开发流程（这是执行层面的） |

**原则**：
- WHY 和 WHAT → 引用 OpenSpec（避免重复，保持同步）
- HOW → 在 Beads 中描述（执行层面的具体步骤）

### 4.2 Epic 模板（Feature 类型）

```markdown
# [Feature] {模块名}

## 目的

{一句话描述功能目的，如：实现会议纪要自动生成功能}

## 关键决策

- {决策 1 标题，如：事件驱动架构}
- {决策 2 标题，如：S3/OBS 双后端}

## 文档

- 📋 提案: `openspec/changes/{change-name}/proposal.md`
- 🏗️ 设计: `openspec/changes/{change-name}/design.md`
- ✅ 规格: `openspec/changes/{change-name}/specs/`
```

### 4.3 Task 模板（带 TDD 流程）

```markdown
# [{Layer}] {模块名} {组件}

## 背景

本 Task 实现 {组件}，是 {Epic ID} 的 {第N} 个交付物。

## 开发流程 (TDD)

**严格遵循 TDD 循环，测试先于实现：**

1. **Red** 🔴 - 创建测试文件，编写失败测试
2. **Green** 🟢 - 实现最小代码使测试通过
3. **Refactor** 🔵 - 优化代码结构

**检查点**: 测试代码必须先于实现代码提交。

## 范围

- {具体工作项 1}
- {具体工作项 2}

## 验收标准

- [ ] 单元测试覆盖率 >= 70%
- [ ] golangci-lint 无错误
- [ ] 测试先于实现提交

## 相关文件

- `internal/domain/{module}/*`

## 依赖

- 阻塞于: {前置 Task ID}

## 文档

- 📋 `openspec/changes/{change-name}/proposal.md`
- 🏗️ `openspec/changes/{change-name}/design.md`
```

### 4.4 Change Request 模板

```markdown
# [Change] {变更描述}

## 目的

{一句话描述变更目的}

## 变更范围

- {文件/模块列表}

## 验收标准

- [ ] 回归测试通过
- [ ] 变更点验证

## 文档

- 📋 `openspec/changes/{change-name}/proposal.md`
```

### 4.5 Bug Fix 模板

```markdown
# [Bugfix] {问题描述}

## 问题

{一句话描述问题现象}

## 验证方法

- [ ] 复现步骤确认
- [ ] 修复后验证
- [ ] 回归测试

## 文档

- 📋 `openspec/changes/{change-name}/proposal.md`
```

---

## 五、智能功能

### 5.1 自动依赖检测

检测 tasks.md 中的依赖关系：

```markdown
## 依赖规则（自动应用）

1. 基础设施 → 业务逻辑
   - setup/config → implementation

2. 架构层次
   - Domain → Infra → App → Integration

3. 测试依赖
   - Implementation → Tests（但不阻塞）

4. 并行任务
   - 同层不同组件可并行
   - 测试与文档可并行
```

### 5.2 缺失任务检测

主动发现并提示：

```
⚠️ 检测到可能缺失的任务：
- 数据库迁移脚本（发现 schema 变更）
- 回滚计划（发现数据迁移）
- 监控指标（发现新 API）
- API 文档更新（发现新端点）

是否创建这些补充任务？
```

### 5.3 复杂度标签

自动添加标签：

```bash
# 基于任务描述
"简单配置" → --label complexity:low
"实现新模块" → --label complexity:medium
"重构核心流程" → --label complexity:high
"数据迁移" → --label complexity:high,risk:data
```

---

## 六、错误处理

### 前置条件检查

```bash
# OpenSpec change 不存在
❌ Change 'xyz' not found in openspec/changes/
Available: [implement-xxx, fix-yyy]
Run: openspec list

# Beads 未初始化
❌ Beads not initialized.
Run: bd init --prefix <project-name>

# tasks.md 格式问题
⚠️ tasks.md 可能需要调整:
  - 第 3 节缺少验收标准
  - 建议添加工作量估算
是否继续转换？
```

---

## 七、反模式警示

❌ **不要做的事**：

1. **不要 1:1 复制 tasks.md**
   - 100 个微任务 → 应合并为 5-10 个有意义 Task

2. **不要忽略工作量**
   - "实现整个模块" 应该是 Epic，不是 Task

3. **不要丢失上下文**
   - Task 描述必须包含 proposal 的 WHY 和 design 的决策
   - 执行者没有 OpenSpec 文件，只看 Beads Task

4. **不要丢失 TDD 流程**
   - 每个 Task 必须包含 Red-Green-Refactor 指导
   - 验收标准必须包含"测试先于实现"

5. **不要过度拆分**
   - 半小时能完成的任务 → 合并到相关 Task

6. **不要忽略依赖**
   - 未建立依赖的任务会导致执行混乱

✅ **必须做的事**：

1. **必须引用原始文档**
   - Task body 底部必须有"参考文档"部分
   - 包含 proposal.md、design.md 的路径

2. **必须包含 TDD 检查点**
   - 明确指出测试代码必须先提交
   - 验收标准包含 Git 历史验证

3. **必须传递业务价值**
   - Epic 必须包含"业务价值"部分
   - Task 必须说明在整体中的位置

---

## 八、与 Agent 工作流集成

当用户说："Let's implement add-auth"

```
自动执行：
1. 检查 openspec/changes/add-auth 存在
2. 分析变更类型和范围
3. 提示任务规划（如需要确认）
4. 创建 Beads Issues
5. 输出可执行步骤
6. Agent 自动运行 `bd ready` 开始工作

用户感受：规划无缝转为执行
```