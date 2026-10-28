# v1.2 完整统计复现审计

最终状态：**PASS**。先读 [REPRODUCTION_REPORT.md](REPRODUCTION_REPORT.md)。不改动任何旧产出，不写稿。

## 文件

- `REPRODUCTION_STATUS.json`：本次实际重拟合状态。
- `table_comparison.csv`：16主表 + 100支持统计表。
- `figure_comparison.csv`：F1–F4的PDF/PNG内容比较。
- `BEERS_percentile_comparison.csv`：修正版四口径百分位。
- `main_table_differences.csv`：7条主表末位差异。
- `difference_summary.csv`：按文件分类的差异汇总。
- `difference_list.csv.gz`：完整320,718条非实质差异；`material_differences.csv`为空表。
- `old_file_preservation.csv`：旧文件哈希保护。
- `run_contract.json`、`runtime_environment.json`、执行日志：运行证据。
- 工作区 `/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/S2_LASU_v1_2_reproduction_20261027`：全部独立数据副本、代码和重算输出。
- 重组表图 `/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/S2_LASU_v1_2_reproduction_20261027/rebuilt_v1_2`：本次重新组装的主表、支持表和图。

## 再次完整运行

使用已记录的Python环境；原项目提供冻结代码和数据。以下两个目录必须尚不存在：

```sh
"/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/formal_v1_env/bin/python" \
  "/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/S2_LASU_v1_2_reproduction_audit_20261027/code/run_reproduction.py" \
  --source-project "/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2" \
  --workspace "/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/S2_LASU_v1_2_reproduction_repeat" \
  --audit-dir "/Users/feishuduobang/Documents/Codex/2026-10-26/s2-lasu-medicare-part-d-k0-2/work/S2_LASU_v1_2_reproduction_repeat_audit"
```

执行顺序：冻结reproduce.py recompute → 原BEERS全国分母/州原始量模型 → 份额模型 → clidinium修正 → 文献表 → 6张派生CSV → 78个独立核验 → 空目录组装主表 → 全部表图及旧文件比较 → 审计报告/压缩包。

本次首次运行使用冻结入口及补充步骤分次执行（日志完整）；新入口把已经执行过的相同步骤串联。入口需要本地缓存输入，不联网，不重做文献检索，不修改原分析脚本。
