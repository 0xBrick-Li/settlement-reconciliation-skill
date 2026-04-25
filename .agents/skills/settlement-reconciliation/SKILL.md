---
name: settlement-reconciliation
description: Reconcile marketplace settlement reports with bank statements at settlement level, producing matched, exception, unmatched, and summary reports from CSV/XLSX files.
---

# Settlement Reconciliation

Use this skill when the user provides or asks to process:

- A platform settlement report and a bank statement.
- CSV or XLSX file paths that should be reconciled at payout / settlement level.
- Marketplace payout reconciliation, settlement reconciliation, or bank deposit matching.
- Exception reports for missing deposits, amount mismatches, date mismatches, ambiguous candidates, or unexplained bank deposits.

This skill is intended for local agent use in:

- Codex CLI
- Codex Desktop
- Claude Code CLI

## Hard File Handling Rules

- Do not `cat` or otherwise read the full settlement or bank file into the LLM context.
- Do not ask the user to paste full CSV/XLSX contents.
- Do not make the LLM parse large files row by row.
- The user must provide file paths at runtime; do not assume or hard-code business file names.
- Do not invent, assume, or reuse example settlement or bank paths. If the user did not provide settlement and bank paths, ask for them.
- The output directory is optional. If the user did not provide one, use `output/settlement_reconciliation/`.
- If `output/settlement_reconciliation/` already contains reconciliation report files, use `output/settlement_reconciliation_<YYYYMMDD_HHMMSS>/`.
- You may check whether paths exist.
- You may read only headers or a few sample rows when needed to infer field mapping.
- The Python CLI must read and process the full input files.
- After running the CLI, read only generated reports such as `reconciliation_report.md`, `reconciliation_summary.csv`, and, when needed, `exceptions.csv`.

## Boundaries

Do:

- Normalize settlement and bank rows into a common schema.
- Match by currency, net payout amount, expected payout date window, and references.
- Produce CSV reports and a Markdown summary.
- Preserve source file and row numbers for auditability.
- Summarize exceptions in Chinese when the user is Chinese-speaking.

Do not:

- Perform order-level reconciliation.
- Build ERP, general ledger, accounting journal, or database workflows.
- Fetch platform or bank data from external systems.
- Convert currencies or infer FX rates.
- Auto-resolve ambiguous many-to-one or one-to-many matches.

## Agent Workflow

1. Confirm the user supplied settlement and bank statement paths. If either path is missing, ask for it.
2. Confirm whether the user supplied a config path. If not, use the built-in default field aliases.
3. Use the user-supplied output directory, or default to `output/settlement_reconciliation/`.
4. If the default output directory already contains report files, use `output/settlement_reconciliation_<YYYYMMDD_HHMMSS>/`.
5. Check whether `settlement-reconcile` is available with `command -v settlement-reconcile`.
6. If the CLI is unavailable, install this project using the dependency install fallback below.
7. Run `settlement-reconcile` with the user-supplied `--settlement`, `--bank`, optional `--config`, and resolved `--out`.
8. Read `reconciliation_report.md` and, if needed, `exceptions.csv` from the output directory.
9. Reply with a concise Chinese summary of match rate, totals, high-priority exceptions, and the actual output directory.

## Dependency Install Fallback

When this skill starts for the first time, or when `settlement-reconcile` is unavailable, install from the skill project root.

Check first:

```bash
command -v settlement-reconcile
```

Then try these commands in order until one succeeds:

```bash
python3 -m pip install -e ".[xlsx,yaml]"
python -m pip install -e ".[xlsx,yaml]"
pip3 install -e ".[xlsx,yaml]"
pip install -e ".[xlsx,yaml]"
```

Verify after installation:

```bash
settlement-reconcile --help
```

## Explicit Invocation

Codex CLI and Codex Desktop:

```text
$settlement-reconciliation
```

Claude Code CLI:

```text
/settlement-reconciliation
```

If the user is unsure whether this skill is available, ask the agent:

```text
请列出当前可用 skills，并确认 settlement-reconciliation 是否可用。
```

## How Users Should Provide Files

For Codex CLI, Codex Desktop, or Claude Code CLI:

- Put the settlement and bank files somewhere accessible from the current workspace.
- Provide the actual paths in the prompt.
- Use relative paths when possible.
- Use absolute paths when the files are outside the workspace.
- Do not paste full CSV/XLSX contents into the prompt.

## Recommended Command Shape

Use the settlement and bank paths provided by the user:

```bash
settlement-reconcile \
  --settlement <settlement_path> \
  --bank <bank_statement_path> \
  --config <optional_config_path> \
  --out <resolved_output_dir>
```

If no config was provided:

```bash
settlement-reconcile \
  --settlement <settlement_path> \
  --bank <bank_statement_path> \
  --out <resolved_output_dir>
```

Useful overrides:

```bash
settlement-reconcile \
  --settlement <settlement_path> \
  --bank <bank_statement_path> \
  --out <resolved_output_dir> \
  --amount-tolerance 0.01 \
  --date-window-days 5
```

Output directory resolution:

- If the user provides an output directory, use it.
- If the user does not provide an output directory, use `output/settlement_reconciliation/`.
- If that default directory already contains report files, use `output/settlement_reconciliation_<YYYYMMDD_HHMMSS>/`.
- Always tell the user the actual output directory in the final response.

## Prompt Templates

Codex CLI / Codex Desktop:

```text
$settlement-reconciliation

请用 Python CLI 对下面两个文件做 settlement-level reconciliation。
不要读取完整 CSV/XLSX 到上下文，只通过 settlement-reconcile 脚本读取文件。

Settlement:
<settlement_file_path>

Bank Statement:
<bank_statement_file_path>

Config:
<optional_config_path_or_omit_if_none>

Output:
<optional_output_dir_or_leave_blank_for_default>

完成后读取 reconciliation_report.md 和 exceptions.csv，并用中文总结异常，同时告诉我实际输出目录。
```

Claude Code CLI:

```text
/settlement-reconciliation

请对以下两个文件做 settlement-level 对账。
不要 cat 完整文件，不要把完整 CSV/XLSX 放进上下文，只运行 settlement-reconcile。

- Settlement: <settlement_file_path>
- Bank Statement: <bank_statement_file_path>
- Config: <optional_config_path_or_omit_if_none>
- Output: <optional_output_dir_or_leave_blank_for_default>

最后用中文总结匹配率、金额差异和需要人工复核的异常，并告诉我实际输出目录。
```

Natural language trigger:

```text
我有一个平台 settlement 报表和一个银行流水，需要做 settlement-level reconciliation。
Settlement 文件路径是：<settlement_file_path>
Bank 文件路径是：<bank_statement_file_path>
输出目录可以不指定；如果我没指定，请使用默认输出目录。
不要把完整文件加载进上下文，请通过 Python CLI 读取文件并输出 matched、exceptions、unmatched 和 markdown summary。
```

## Output Files

- `reconciliation_summary.csv`: totals, counts, and amount differences.
- `matched.csv`: clean matches and warning matches.
- `exceptions.csv`: mismatches, ambiguous records, and missing items.
- `unmatched_settlements.csv`: settlements without a bank deposit.
- `unmatched_bank_transactions.csv`: bank transactions without a settlement.
- `reconciliation_report.md`: concise human-readable summary.

## Input Mapping

Prefer using a config file when source headers differ from the defaults. Fields map canonical schema names to possible source column names.

```yaml
amount_tolerance: 0.01
date_window_days: 5
currency_required: true
allow_many_to_one: false
settlement_fields:
  settlement_id: [Settlement ID, Payout ID]
  currency: [Currency]
  expected_payout_date: [Expected Payout Date, Payout Date]
  net_amount: [Net Amount, Payout Amount]
bank_fields:
  transaction_id: [Transaction ID]
  transaction_date: [Transaction Date]
  currency: [Currency]
  amount: [Amount]
  reference: [Reference]
```
