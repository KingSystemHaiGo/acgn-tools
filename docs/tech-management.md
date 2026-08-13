# 技术管理制度（Tech Management v0.1）

> 创建：2026-08-13 19:51 ｜ 发起：CEO 小花花（duke 指示：开发项目必须做技术选型/架构/路线图，联网学习先进经验，适配全 agent 工作室）
> 借鉴：Twelve-Factor App（Heroku 实践）、Fowler Patterns of Distributed Systems、工程化开发流程
> 核心认知：**开发项目 = 技术选型 → 架构设计 → 路线图 → 开发 → 验证 → 发布**，技术管理先于写代码

## 0. 为什么补这份制度（duke 批评）

之前只做了项目管理（任务拆解/协作制度/验收），**没做技术管理**：技术选型没有、架构没有、路线图没有——直接跳到写代码，不是开发团队的工作流程。本制度把技术管理变成强制阶段。

## 1. 开发阶段流程（每个项目必经）

```
阶段 0 技术选型（Tech Stack Decision）→ 阶段 1 架构设计（Architecture）→ 阶段 2 路线图（Roadmap）
→ 阶段 3 开发（R2 规格 → R3 实现）→ 阶段 4 验证（R4 断言 → R5 验证）→ 阶段 5 发布（R6 审查 → 入库）
```

**门禁**：未完成选型/架构/路线图，不进入写代码阶段（12-Factor 启示：契约先行）。

## 2. 阶段 0：技术选型（Tech Stack Decision）

### 2.1 选型原则（12-Factor 适配全 agent）
| 12-Factor 原则 | 全 agent 工作室适配 |
|---|---|
| I. Codebase 单一代码库 | GitHub acgn-tools（仓库即事实源）✅ 已有 |
| II. 依赖显式声明 | pyproject.toml + requirements.txt（依赖锁版本） |
| III. 配置存环境 | 环境变量/配置文件分离（不硬编码） |
| IV. 后端服务可替换 | SQLite 起步（零部署），可换 PostgreSQL |
| V. 构建/发布/运行分离 | 构建（CI）→ 发布（tag）→ 运行（可回滚） |
| VI. 无状态进程 | agent 可随时重启（状态存仓库/DB 不存内存） |
| VII. 端口绑定 | CLI 工具为主，未来 Web 服务端口绑定 |
| VIII. 并发模型 | 进程模型扩展（多 agent 并行跑任务） |
| IX. 可丢弃性 | 快速启动+优雅关闭（agent 断线不丢状态） |
| X. 开发/生产一致 | 本地=仓库=部署（agent 环境差异已用角色矩阵解决） |
| XI. 日志事件流 | 结构化日志（JSON lines）可审计 |
| XII. 管理任务一次性 | 迁移/导入用一次性脚本（spark-cli） |

### 2.2 当前项目选型（T002 冲突检测）
- **语言**：Python 3.11+（可验证性工具链成熟；长征/小吉量熟悉）
- **依赖管理**：uv + pyproject.toml（本机已有 uv）
- **测试框架**：pytest（R4 断言直接可执行，fixture 驱动）
- **数据格式**：JSON + canonicalizer v1（JCS RFC 8785，与对拍体系一致）
- **存储**：SQLite（知识条目表 + 年轮表，零部署起步）
- **CLI**：Typer/Click（与 spark-cli 互补：spark-cli 管项目，产品 CLI 管知识）
- **CI**：GitHub Actions（提交自动跑 pytest + digest 校验）——后续加

## 3. 阶段 1：架构设计（Architecture）

### 3.1 分层（模块化，单一职责）
```
apps/conflict-detector/
├── models.py        # KnowledgeEntry 数据模型（十字段/六字段）
├── rules.py         # 三维判定规则（lineage→digest→validity）
├── detector.py      # 主裁决函数（编排规则，输出 verdict+evidence）
├── arbitration.py   # 四选一仲裁出口（KEEP_A/KEEP_B/SPLIT/REDEFINE）
├── evidence.py      # 证据链三元组 [字段名, 修订号, 双方值]
├── cli.py           # 产品 CLI（导入/检测/查询）
└── tests/
    ├── fixtures/    # CONFLICT-001~010（T4 矩阵）
    └── test_*.py    # R4 断言（澄川/星星）
```

### 3.2 数据流
```
用户导入 → KnowledgeEntry（六字段）→ detector.detect(entries)
  → 三维判定（rules.py）→ Verdict（SUPERSEDED/CONFLICTED/REJECTED）
  → conflicted → arbitration（四选一）→ rulings_log（年轮）→ knowledge_map
```

### 3.3 接口契约（R2 规格已在仓库，作为架构基础）
- `detector.detect(entry_a, entry_b) -> Verdict`（主裁决函数）
- `arbitration.resolve(conflict, choice) -> Ruling`（仲裁出口）
- 输入输出均 JSON 可序列化（与 canonicalizer 兼容）

## 4. 阶段 2：技术路线图（Roadmap）

### 4.1 当前项目（冲突检测 MVP）
| 版本 | 内容 | 时间 |
|---|---|---|
| v0.1 | 算法骨架（R2 规格 ✅ → R3 实现）| 8/17 前 |
| v0.2 | 跑通 10 条 fixture + pytest 断言 | 8/17 checkpoint |
| v0.3 | knowledge_map + rulings_log 存储（SQLite）| 8/17 后 |
| v1.0 | 产品闭环（导入→检测→仲裁→年轮）| 8/24 |

### 4.2 里程碑门禁
- v0.1 门禁：R3 代码实现跑通 R2 验收用例三组（正控/负控/边界）
- v0.2 门禁：T4 矩阵 10 条 fixture 全过 + digest 字节级收据
- v1.0 门禁：8/17 后三人技术栈碰头确认架构 → 项目章程 → 最小原型

## 5. 技术评审（R6 强化）

- **架构评审**：代码实现前，CTO 长征 + 技术核心小吉量评审架构设计（模块/接口/数据流）
- **代码审查**：实现后 R6 审查（契约合规/digest 纪律/测试覆盖）
- **选型变更**：技术选型变更须 ADR（决策记录，human/decisions/）——12-Factor 启示：显式记录

## 6. 全 agent 适配要点

- **无环境成员参与技术管理**：R1 设计（规格）/R2 规则（算法逻辑）不需要跑代码——技术管理文档（选型/架构/路线图）人人可评审提意见
- **环境差异**：有环境的做 R3 实现/R5 验证；无环境的评审架构/写规格
- **异步评审**：架构/选型文档入仓库 → 异步大会/评审通道收集意见 → CEO 汇总决策
- **留痕**：每个技术决策入仓库（ADR），agent 重启/失忆可恢复（与记忆系统一致）

## 7. 状态

- v0.1 草案（2026-08-13 19:51）——duke 指示落地，随项目实践迭代
- 首批应用：T002 冲突检测（选型/架构/路线图已在本文档 §2-4 给出，待长征 CTO 评审确认）
