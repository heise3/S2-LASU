# S2-LASU 最终冻结包 v1.3

**状态：FROZEN / 统计复现 PASS。** 本版冻结已完成并通过核验的完整统计重算结果、补齐后的复现入口及审计证据。v1.2和此前产出原样保留。本次冻结没有再次拟合模型，没有更改分析定义、阈值或判定，没有写稿。

唯一当前状态文件是 [STATUS.json](STATUS.json)，分析判定见 [DECISIONS.json](DECISIONS.json)。不要用历史证据中的v1.2“仅包装/未重算”字段描述v1.3；本包采用的源运行已经实际重拟合并通过核验。

## 当前权威结果

- [统一主结果表](tables/main/MAIN_RESULTS.csv)：44行。
- [16张主表索引](TABLE_INDEX.md)：T1–T7；[F1–F4图号与说明](FIGURES.md)：4张矢量PDF及4张PNG。
- `tables/details/`：100张通过核验的支持统计表，含抑制、排除、处方者、官方分母和敏感性记录。两份旧包装table_inventory不作为统计结果带入。
- [复现报告](REPRODUCTION_REPORT.md)：主表16/16、支持表100/100、图文件8/8通过，实质性差异0。
- [文献对比T7](tables/main/T7_literature_comparison.csv)：19行，包含Stuart 2003概念先例。本次未重做检索。

## 分析口径与决定

1. LASU主指标为长效SU30天量/全部SU30天量；年龄差斜率用百分点/年。处方者主分析为全年龄。
2. A2为PASS；R2四情形为ROBUST。103个全可见州年、41州的敏感性CI跨0，仍需同时报告。F3横线为抑制界，不是统计CI。
3. 暴露量采用官方年龄参保人年标准化；≥65 SU绝对量增加13.48%同时对应人年率下降31.50%，两者不能互换。T5为公开药品行受益人数并集上下界，不是去重人数的点估计。
4. Beers仅作为LASU描述性背景基准，独立论文路线STOP。修正版百分位依次为全国分母 **78.79**、同类份额log **84.85**、同类份额logit **84.85**、州原始量 **78.79**，四者均Q4，纳入决定保持不变。
5. <65 Part D人群以残障入保者为主；交互只描述年龄组间趋势差异，不解释为Beers政策效应。ATC类别是预先冻结的分母映射，不代表实际适应证等同。

## 明确停用 clidinium 误匹配结果

**旧GI clidinium子串误将aclidinium、umeclidinium呼吸系统产品纳入。含该错误的旧Beers主表、基线、森林图和决定均不得作为当前分析结果使用。** 即使旧文件位于benchmark的`tables/corrected/`，只修正份额但保留(a)/(c)旧基线的比较也继续停用。旧75.76百分位不作为当前值。

[停用清单](DEPRECATED.md)和[机器可读清单](DEPRECATED.csv)给出替代路径。有效药名为`definitions/BEERS_numerator_*_effective.csv`；当前T6和F4均来自全口径更正版。历史错误规则保留在`provenance/beers/*AUDIT_ONLY*`及历史代码中，仅供追溯；不得直接运行历史脚本作为有效分析。所有重算须走以下统一入口，确保必要修正执行。

## 唯一执行入口

Python 3.12，依赖版本见`code/requirements.txt`。默认只读校验：

```sh
python code/reproduce.py verify
```

完整重算需要原项目公开缓存，不重复下载外部数据；所需457份输入、代码与v1.2兼容适配文件均有冻结哈希。v1.2入口仅作为原8步的兼容适配器，v1.3统一入口另外完成遗漏基线、派生表及全量核对；不得单独使用旧入口宣称完整复现。

```sh
python code/reproduce.py preflight --source-project /absolute/path/to/source_project
python code/reproduce.py recompute \
  --source-project /absolute/path/to/source_project \
  --workspace /absolute/path/to/source_project/work/S2_LASU_v1_3_replay_new \
  --audit-dir /absolute/path/to/source_project/work/S2_LASU_v1_3_audit_new \
  --dry-run
# 去掉 --dry-run 后执行；两个目录都必须尚不存在。
```

完整流程14步：原LASU A1–A4/官方分母/F1–F3、R1–R5、Beers初算及修正、文献表；另重建Beers匹配与全国分母/州原始量基线、重新拟合份额并修正GI、补齐6张派生表；最后从空目录组装并核对全部16主表、100支持表、8图文件及4个百分位，独立验证78个模型。输出参照为本v1.3包，不能只检验旧6张代表表。

入口仅提供`verify`、`preflight`、`recompute`；不提供对冻结目录原地assemble/seal。`verify`只验证本包，`preflight`另验证外部源文件和运行依赖。完整重算在两个新的source_project/work子目录进行，拒绝覆盖已有目录。不要把日志重定向到冻结包内。

## 哈希和复现证据

- `MANIFEST.json`：每个交付内容文件的相对路径、字节数、SHA256；不自包含，也不包含SHA256SUMS。
- `SHA256SUMS`：覆盖上述内容文件及MANIFEST.json；自身完整性由外部ZIP SHA256回执覆盖。
- `evidence/import_manifest.json`：逐文件来源、角色、来源/目标哈希；当前全部表图与通过核验的重算源逐字节一致。
- `evidence/freeze_validation.json`：本次冻结的状态、源文件保留、表图一致性与入口集成核验。
- `evidence/reproduction_20261027/`：原完整重算的报告、状态、逐格差异压缩CSV、日志、环境、代码和输入检查记录，原样留存。
- `provenance/`及`reproduction/upstream_code/`：历史来源与脚本快照；状态字段只解释对应历史运行，当前状态以根目录STATUS.json为准。

交付ZIP及其`.sha256`回执在本目录上一级。解压后可在包根目录运行`shasum -a 256 -c SHA256SUMS`或上述verify命令。冻结不等于文件系统锁定；任何字节变化或新增文件都会使完整性检查失败。
