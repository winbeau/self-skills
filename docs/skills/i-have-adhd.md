# i-have-adhd — 面向 ADHD 读者的输出风格

> **来源声明**
> - 本 Skill 从 [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) vendored 而来，版权归 **Ayoub Ghriss (© 2026)**，**MIT 许可**。
> - 许可证原文保留在 [`skills/i-have-adhd/LICENSE`](../../skills/i-have-adhd/LICENSE)，改动清单见 [`ATTRIBUTION.md`](../../skills/i-have-adhd/ATTRIBUTION.md)。
> - 上游自述：规则思路 loosely based on *The Adult ADHD Tool Kit*（J. Russell Ramsay、Anthony L. Rostain），改写为「LLM 该怎么回答」，而非「人该怎么安排一天」。

## 它做什么

一个**输出风格 Skill**：不改变模型做什么，只改变模型怎么把结果说出来。一旦启用，规则在**整个 session 内持续生效**，不会几轮之后自动失效，也不随话题切换而失效——直到你说 `stop adhd mode` 或 `normal mode`。

10 条规则：

1. 首行就是可执行动作（命令 / 路径 / 片段优先，铺垫靠后）
2. 多步任务必须编号，每步一个有界动作
3. 结尾给**一个**两分钟内能做完的具体动作
4. 抑制岔路：先做完手上这件，第二件单独问
5. 每轮复述状态（"5 步中的第 3 步已完成"）
6. 时间估计用具体单位（"约 15 分钟"，不是"要点工夫"）
7. 已完成的工作要显式可见，不埋在总结里
8. 报错平铺直叙：原因 + 修法，禁止 "Uh oh" / "看起来出了点问题"
9. 列表最多 5 项，超了就拆成"现在做 / 以后做"
10. 无开场白、无复盘、无客套收尾

另有 6 条**破例条件**（要求"讲解一遍"、危险操作前确认、连续三轮 debug 死循环、真有歧义、规则会吃掉答案本身、规则与 harness 冲突），以及一个发送前自检清单。完整规则以 [`skills/i-have-adhd/SKILL.md`](../../skills/i-have-adhd/SKILL.md) 为准。

## 怎么用

本仓库通过 `./deploy.sh` 建立软链，安装后：

```
/i-have-adhd            # Claude Code
$i-have-adhd            # Codex
```

也可以直接说「开 adhd 模式」「用 ADHD 风格回答」。关闭：

```
stop adhd mode
```

## 与上游的两点差异

**1. 只保留 `name` + `description` 两个 frontmatter 键。**

本仓库的可移植性约定（`CLAUDE.md`）和 `scripts/validate_skills.py` 都要求 `SKILL.md` frontmatter 只含这两个键，因此上游的 `disable-model-invocation: true`、`license: MIT`、`metadata.hermes` 被移除。

其中 `disable-model-invocation` 原本是**硬开关**，用来阻止模型自作主张地加载这个 Skill。移除后改为在 `description` 里显式写明"仅用户主动调用，不要自行触发"——这是**较弱的约束**，模型理论上仍可能自行触发。如果你更看重那个硬保证，在本地给 `SKILL.md` 加回：

```yaml
disable-model-invocation: true
```

代价是 `python3 scripts/validate_skills.py` 会报 `frontmatter must contain only name and description`。

**2. 不安装上游的 always-on hook。**

上游作为 Claude Code plugin 分发时带了一个 `SessionStart` hook：检测到 `~/.claude/.i-have-adhd-always` 存在就自动开启该风格。本仓库用软链装 Skill，不走 plugin 机制，因此**没有装这个 hook**，`touch ~/.claude/.i-have-adhd-always` 在这里不起作用。

想要开机即生效，两条路：

- 走上游的 plugin 安装（与本仓库的软链副本二选一，别同时装，会重名）：
  ```bash
  claude plugin marketplace add ayghri/i-have-adhd
  claude plugin install i-have-adhd@i-have-adhd
  touch ~/.claude/.i-have-adhd-always
  ```
- 或者把等价指令写进 `~/.claude/CLAUDE.md`（本仓库的 `global/CLAUDE.md`），让它对所有 session 生效。

## 未 vendored 的上游内容

`plugin.json`、`.claude-plugin/`、`.codex-plugin/`、`.agents/`、`.cursor/`、`hooks/`、`evals/`（一套 rubric + cases.jsonl 的评测集）、GitHub workflows、`agents/gemini.toml`。需要这些请回上游仓库取。
