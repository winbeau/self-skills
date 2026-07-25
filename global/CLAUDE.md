# ~/.claude/CLAUDE.md — 全局提示词

本文件对所有 session 生效（项目级 CLAUDE.md 优先级更高，会覆盖冲突条目）。

## Workflow 触发时机（选择性编排，非全量）

> **不是所有任务都跑 workflow。** 只有**开放性探索 / 多源调研 / 思考整合综合 / 需要多视角交叉验证**的任务，才默认用 Workflow 多 agent 编排；直接、机械、单步、事实查一次即定的任务，直接做，不要起 workflow。

- **该用 workflow**：开放式调研、方案设计与多方案对比、跨多个子系统的理解梳理、需要对抗式核实的关键判断、大范围审计 / 迁移 / 综述。这类任务的共同点是「解空间宽、需要发散再收敛」。
- **不该用 workflow**：改一行代码、查一个已知文件或值、格式转换、单步执行、对话式回答、明确单文件的机械改动。直接上手更快更省。
- 拿不准时：先自己 scout 一下（列文件、定位范围），发现确实是「发散—整合」型再起 workflow；否则直接做。
- **起了 workflow 也照旧守下面的路由与 token 规则**（默认继承父模型 / pipeline 优先 / schema 最小 / finder 限量 / budget 守门）——选择性编排是为了「该重则重、该轻则轻」，不是放开烧 token。

## Workflow 模型路由与 Token 控制

> **cc-switch 兼容原则**：`haiku` / `sonnet` / `opus` 是 Claude Code 的逻辑路由槽位，不代表固定厂商、固定模型版本或固定价格。实际模型由当前 cc-switch Provider 映射决定，切换 Provider 后可能变化。
>
> **默认继承父 session 模型，不显式写 `model`。** 只有用户明确指定模型档位，或某个独立子任务确实需要不同的速度/质量档位时，才给 `agent()` 写 `model: "haiku" | "sonnet" | "opus"`。不要在 Workflow 脚本中写具体版本 ID，也不要假定 `fable` 可用；先确认当前 Provider 已配置相应路由。

### 路由选择建议

| 场景 | 路由策略 |
|---|---|
| 默认任务、代码实现、关键判断 | 省略 `model`，继承当前会话 |
| 大批量机械检索 / 提取 / 分类 | 仅在确认该槽位可用时使用 `haiku` |
| 明确希望使用平衡档 | 仅在确认该槽位可用时使用 `sonnet` |
| 明确需要最高质量档 | 使用 `opus`，或直接继承已选择的高质量主会话 |

切换 cc-switch Provider 后，不能继续沿用上一 Provider 的成本比例、能力排序或可用性判断。若某个显式槽位报 unavailable，立即改回继承父模型，不要重复调用同一失败槽位。

### Token 节省规则

1. **`pipeline()` 优先**：无阻塞，wall-clock = 最慢单链；`parallel()` 是 barrier，只在真正需要全量结果时用。
2. **两段式流水线**：需要分档且槽位已验证可用时，可用较轻路由做 finder/extractor 初筛，再把候选送到继承模型或更高质量路由；不要为了省 token 强制调用一个不可用槽位。
3. **`schema` 最小化**：需要结构化下游输入时，为 `agent()` 指定最小 schema，字段只留下游需要的，避免 free-text 膨胀。
4. **数量上限**：finder agent ≤ 8（通常 4–6）；verifier ≤ 3 票（majority-vote 足够）。
5. **`budget` 守门**：长循环必须有 `budget.total && budget.remaining() > N` 守卫。
6. **截断必须 `log()`**：top-N 抽样或限量 finder，必须 log 说明，不能让结果看起来像全覆盖。
7. **避免重复调研**：同 session 内已有调研结果（task output / 落盘文件）先读，不要重跑 workflow。

### 写脚本检查清单

- [ ] `model` 是否可以省略并继承父 session？只有确有分档需求且路由已验证可用时才显式填写。
- [ ] 是否避免写死具体模型版本、供应商模型名或固定价格比例？
- [ ] 有无不必要的 `parallel()`（能改 `pipeline()` 的改掉）？
- [ ] schema 字段数最小化？
- [ ] finder/verifier 数量有上限，或循环有 `budget` 守门？
- [ ] 脚本写好后先展示给用户确认，再 launch `Workflow()`？

## 静态文章 / 文档 HTML 路由

当用户要把通用文章、报告、提案、RFC、教程或其他文稿生成**单个自包含的静态 HTML 文件**时，使用 `article-to-html`，默认样式为 `xju-notion`；用户显式指定样式时以用户选择为准。不要把这条路由用于多页网站或应用、React / UI 原型、幻灯片、PDF / LaTeX，或 OpenReview 导出（后者使用 `openreview-to-html`）。
