# settlement-reconciliation-skill

轻量级跨境电商结算对账工具和 Agent Skill，用于把平台 Settlement 报表与银行流水做 **settlement-level reconciliation**。

它适合回答这类问题：平台说本期应该打款多少，银行实际收到了什么，哪些结算批次已匹配，哪些需要人工复核。

## 运行截图

![Codex Desktop 运行截图](images/截屏2026-04-25%2021.57.22.png)

![Claude Code运行截图](images/截屏2026-04-25%2022.09.43.png)


## 功能范围

支持：

- CSV / XLSX 输入文件。
- 平台 settlement 报表与银行流水的一对一批次级匹配。
- 金额容差、日期窗口、币种校验、reference/description 匹配。
- 输出 matched、exceptions、unmatched 和 Markdown 汇总报告。
- 在 Codex CLI、Codex Desktop、Claude Code CLI 中作为 skill 使用。


## 一键安装

从 GitHub clone 后，在仓库根目录安装 Python CLI，并把 skill 安装到 Codex 和 Claude Code 的用户级 skill 目录：

```bash
git clone https://github.com/0xBrick-Li/settlement-reconciliation-skill.git
cd settlement-reconciliation-skill
python3 -m pip install -e ".[xlsx,yaml]" || python -m pip install -e ".[xlsx,yaml]"

mkdir -p ~/.agents/skills/settlement-reconciliation
cp SKILL.md ~/.agents/skills/settlement-reconciliation/SKILL.md

mkdir -p ~/.claude/skills/settlement-reconciliation
cp SKILL.md ~/.claude/skills/settlement-reconciliation/SKILL.md
```

注意：复制 `SKILL.md` 只会安装 Agent 指令，不会安装 Python 命令。仍然需要执行 `pip install -e ".[xlsx,yaml]"`，这样 `settlement-reconcile` 才可用。

验证安装：

```bash
settlement-reconcile --help
```

## 全局安装

如果你希望在任意项目里都能调用这个 skill，推荐做全局安装。全局安装包含两部分：

- 安装 Python CLI：让系统里有 `settlement-reconcile` 命令。
- 安装 Agent Skill：让 Codex / Claude Code 能识别 `$settlement-reconciliation` 或 `/settlement-reconciliation`。

推荐把仓库 clone 到一个长期保留的位置：

```bash
mkdir -p ~/.local/share
cd ~/.local/share
git clone https://github.com/0xBrick-Li/settlement-reconciliation-skill.git
cd settlement-reconciliation-skill
python3 -m pip install -e ".[xlsx,yaml]" || python -m pip install -e ".[xlsx,yaml]"
```

安装到 Codex CLI / Codex Desktop 的全局 skill 目录：

```bash
mkdir -p ~/.agents/skills/settlement-reconciliation
cp SKILL.md ~/.agents/skills/settlement-reconciliation/SKILL.md
```

安装到 Claude Code CLI 的全局 skill 目录：

```bash
mkdir -p ~/.claude/skills/settlement-reconciliation
cp SKILL.md ~/.claude/skills/settlement-reconciliation/SKILL.md
```

验证：

```bash
settlement-reconcile --help
```

之后在任意项目中都可以这样触发：

```text
$settlement-reconciliation
```

或：

```text
/settlement-reconciliation
```

更新全局安装：

```bash
cd ~/.local/share/settlement-reconciliation-skill
git pull
python3 -m pip install -e ".[xlsx,yaml]" || python -m pip install -e ".[xlsx,yaml]"
cp SKILL.md ~/.agents/skills/settlement-reconciliation/SKILL.md
cp SKILL.md ~/.claude/skills/settlement-reconciliation/SKILL.md
```

## 分步安装

只安装 Python CLI：

```bash
git clone https://github.com/0xBrick-Li/settlement-reconciliation-skill.git
cd settlement-reconciliation-skill
python3 -m pip install -e ".[xlsx,yaml]"
```

## 启用 Skill

这个仓库已经包含项目级 skill 文件：

```text
.agents/skills/settlement-reconciliation/SKILL.md
.claude/skills/settlement-reconciliation/SKILL.md
```

### Codex Desktop  && Codex CLI 

在包含 `.agents/skills/settlement-reconciliation/SKILL.md` 的项目中使用：

```text
$settlement-reconciliation
```


### Claude Code CLI

在包含 `.claude/skills/settlement-reconciliation/SKILL.md` 的项目中使用：

```text
/settlement-reconciliation
```

用户级安装路径：

```text
~/.agents/skills/settlement-reconciliation/SKILL.md
~/.claude/skills/settlement-reconciliation/SKILL.md
```


## Config 是什么

`config` 是可选 YAML 配置，用来控制字段映射和匹配参数。

不提供 config 也可以运行，因为代码里内置了常见字段别名。例如 `Net Amount`、`Payout Amount`、`Amount Paid` 都可以映射到 settlement 的 `net_amount`。

当你的平台或银行文件列名和默认别名不一致时，建议复制示例配置后修改：

```bash
cp examples/config.example.yaml my_config.yaml
```

示例配置位置：

```text
examples/config.example.yaml
```

核心配置项：

- `amount_tolerance`：金额容差，例如 `0.01`。
- `date_window_days`：银行入账日期允许偏离 expected payout date 的天数。
- `currency_required`：是否要求币种一致。
- `allow_many_to_one`：是否允许多个 settlement 匹配同一笔银行流水；MVP 默认不允许。
- `settlement_fields`：Settlement 文件列名到统一字段的映射。
- `bank_fields`：Bank Statement 文件列名到统一字段的映射。

真实使用时：

- 如果你的 CSV/XLSX 表头和示例类似，可以不传 config。
- 如果 normalization issue 很多，或字段识别不正确，再传自定义 config。

## 示例文件

仓库内提供了合成样例：

```text
examples/settlement_sample.csv
examples/bank_sample.csv
examples/config.example.yaml
```

样例覆盖：

- 正常匹配。
- 日期超出窗口。
- 金额不一致。
- 币种不一致。
- settlement 找不到银行入账。
- 银行流水找不到 settlement。
- 多个银行候选导致歧义。

运行样例：

```bash
settlement-reconcile \
  --settlement examples/settlement_sample.csv \
  --bank examples/bank_sample.csv \
  --config examples/config.example.yaml \
  --out output/sample_run/
```

## 如何传入文件

使用时，不要把完整 CSV/XLSX 粘贴给 LLM 或加载到上下文。只在提示词中提供文件路径即可。

必填：

- Settlement 文件路径。
- Bank Statement 文件路径。

可选：

- Config 文件路径。
- Output 目录。

如果没有指定 output，skill 会使用：

```text
output/settlement_reconciliation/
```

如果该目录已有报告文件，skill 会改用带时间戳的目录，避免覆盖旧结果。

## 示例提示词

### 其他路径文件：Codex CLI / Codex Desktop

```text
$settlement-reconciliation
将 settlement：<settlement_file_path> 和 bank statement：<bank_statement_file_path> 进行对账。

Config：<optional_config_path_or_omit_if_none>
Output：<optional_output_dir_or_leave_blank_for_default>
```

### 其他路径文件：Claude Code CLI

```text
/settlement-reconciliation
将 settlement：<settlement_file_path>和 bank statement：<bank_statement_file_path> 进行对账。
Config：<optional_config_path_or_omit_if_none>
Output：<optional_output_dir_or_leave_blank_for_default>
```

### 使用仓库示例文件：Codex CLI / Codex Desktop

```text
$settlement-reconciliation
将 settlement：examples/settlement_sample.csv和 bank statement：examples/bank_sample.csv 进行对账。
Config：examples/config.example.yaml
Output：output/sample_run/
```

### 使用仓库示例文件：Claude Code CLI

```text
/settlement-reconciliation
将 settlement：examples/settlement_sample.csv 和 bank statement：examples/bank_sample.csv 进行对账。
Config：examples/config.example.yaml
Output：output/sample_run/
```

## 输出结果

一次成功运行会生成：

```text
reconciliation_summary.csv
matched.csv
exceptions.csv
unmatched_settlements.csv
unmatched_bank_transactions.csv
reconciliation_report.md
```

建议先看：

```bash
cat output/sample_run/reconciliation_report.md
```

常用文件：

- `reconciliation_summary.csv`：总体统计和金额汇总。
- `matched.csv`：正常匹配和 warning 匹配。
- `exceptions.csv`：金额、日期、币种、歧义等异常。
- `unmatched_settlements.csv`：没有找到银行入账的 settlement。
- `unmatched_bank_transactions.csv`：无法解释的银行入账。
- `reconciliation_report.md`：适合人工快速阅读的摘要。


## 安全注意事项

- 不要提交真实银行账号、客户信息、API key、平台 token 或 `.env`。
- 真实业务文件建议放在本地安全目录，不要提交到公共仓库。
- 这个工具不会联网下载平台或银行数据。
- 不做汇率换算；不同币种默认不可匹配。
