# 文献检索与筛选 (Literature Screening)

> 生物医学文献系统检索与多维度自动筛选工具包  
> A systematic biomedical literature search & multi-dimensional LLM scoring pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## 📖 简介

**文献检索与筛选**是一个五步文献筛选流程，专为生物医学研究设计，可用于：

- 🔬 新课题的系统文献检索
- 🎯 LLM 微调语料的自动化筛选
- 📊 系统综述 / Meta 分析的文献筛选
- 🧬 药物靶点发现、生物标志物研究的文献过滤

核心思路：**用大语言模型（LLM）对每篇文献摘要进行多维度自动打分，替代人工逐篇阅读的低效方式。**

---

## 🔄 五步工作流程

```
Step 1: 关键词设计 → Step 2: PubMed检索 → Step 3: 去重过滤
                                              ↓
Step 4: 多维度LLM打分 ← Step 5: 质量阈值筛选 → 高质量文献集
```

| 步骤 | 说明 | 脚本 |
|------|------|------|
| **1. 关键词设计** | 根据研究主题构建 PubMed 查询语句（MeSH + 自由词） | 参考 `references/keyword_design.md` |
| **2. PubMed 检索** | 批量获取标题、摘要、出版类型、年份 | `scripts/pubmed_search.py` |
| **3. 去重与过滤** | 剔除重复、非研究性论文（评论/新闻/信件等） | `scripts/dedup_filter.py` |
| **4. 多维度打分** | LLM 对每篇摘要进行 0/1 多维度评判 | `scripts/multi_dim_score.py` ⭐ 核心 |
| **5. 质量筛选** | 按总分阈值筛选，输出分布可视化 | `scripts/select_papers.py` |

---

## 🚀 快速开始

### 环境要求

```bash
pip install biopython openai
```

### 完整示例（HCC 药物靶点文献筛选）

```bash
# Step 1-2: PubMed 检索
python scripts/pubmed_search.py \
  --query '("Carcinoma, Hepatocellular"[Mesh] OR HCC[tiab]) AND (drug target*[tiab] OR therapeutic target*[tiab])' \
  --email your@email.com \
  --output results.csv

# Step 3: 去重与过滤
python scripts/dedup_filter.py \
  --input results.csv \
  --output dedup.csv

# Step 4: LLM 多维度打分（⭐ 核心步骤）
python scripts/multi_dim_score.py \
  --input dedup.csv \
  --output scored.csv \
  --dimensions drug_target \
  --api-key $DEEPSEEK_API_KEY

# Step 5: 按阈值筛选（例如 TOTAL >= 3）
python scripts/select_papers.py \
  --input scored.csv \
  --threshold 3 \
  --output selected.csv
```

---

## 🎯 核心特性

### 1. 可定制的评分维度

**预设模板：**

| 预设名 | 适用场景 | 维度 |
|--------|---------|------|
| `drug_target` | 药物靶点发现 | GENE, TARGET, DRUG, VALID, CLIN, MECH, BIOM, REVIEW |
| `biomarker` | 生物标志物研究 | BIOMARKER, COHORT, SENSITIVITY, PROGNOSIS, VALIDATION, MULTICENTER, METHOD, UTILITY |

**自定义维度：**

```bash
python scripts/multi_dim_score.py \
  --dimensions "IMMUNE,CHECKPOINT,T_CELL,CYTOKINE,CLIN,TRIAL" \
  ...
```

详细维度设计指南见 [`references/scoring_dimensions.md`](references/scoring_dimensions.md)。

### 2. 断点续传

打分过程中每 50 篇自动保存 checkpoint，中断后可续传：

```bash
python scripts/multi_dim_score.py --resume ...  # 从上次中断处继续
```

### 3. 分布可视化

`select_papers.py` 自动绘制分数分布直方图，帮助确定合理阈值：

```
Score distribution:
  Score    Count    Cumulative   % Kept
  ------   ------   ----------   ------
  8        42       42           0.5%
  7        189      231          2.8%
  6        421      652          7.8%
  5        892      1544         18.5%
  4        1247     2791         33.4%   ← 常见选择
  3        1589     4380         52.5%   ← 推荐阈值
  2        1892     6272         75.2%
  1        1203     7475         89.6%
  0        867      8342         100.0%
```

### 4. PubMed 检索最佳实践

- ✅ 自动使用 WebEnv 历史查询（支持 >10,000 结果）
- ✅ 200 篇/批的批量获取，内置延迟避免被封
- ✅ 完整元数据提取（标题、摘要、出版类型、年份）

---

## 📁 文件结构

```
literature-screening/
├── SKILL.md                          # 技能定义文件（WorkBuddy 使用）
├── README.md                         # 本文件
├── scripts/
│   ├── pubmed_search.py              # PubMed 检索脚本
│   ├── dedup_filter.py               # 去重与过滤脚本
│   ├── multi_dim_score.py            # 多维度 LLM 打分脚本 ⭐
│   └── select_papers.py              # 质量筛选脚本
└── references/
    ├── scoring_dimensions.md         # 评分维度设计指南
    └── keyword_design.md             # PubMed 关键词构建规范
```

---

## 💰 成本估算

使用 DeepSeek V4 Pro API 进行打分（以 8 维度、5000 篇文献为例）：

| 项目 | 数值 |
|------|------|
| 每篇 Token 消耗 | ~500 tokens（提示 + 输出） |
| 总 Token | ~2,500,000 |
| 费用 | **约 ¥1.50**（0.6 元/百万 tokens） |
| 耗时 | ~20 分钟（0.2 秒/篇 + 限流间隔） |

---

## 🔧 进阶用法

### 更换 LLM 后端

支持任何 OpenAI 兼容 API：

```bash
# 使用通义千问
python scripts/multi_dim_score.py \
  --base-url https://dashscope.aliyuncs.com/compatible-mode/v1 \
  --model qwen-plus \
  --api-key $DASHSCOPE_KEY \
  ...

# 使用本地 Ollama
python scripts/multi_dim_score.py \
  --base-url http://localhost:11434/v1 \
  --model qwen2.5:7b \
  --api-key ollama \
  ...
```

### 大规模文献处理

对于 >10,000 篇文献：

1. 先用 `--limit 100` 试验维度设计的合理性
2. 检查分数分布是否有区分度
3. 调整维度定义后再全量运行
4. 使用 `--resume` 防止长时间运行中断

---

## 📊 实际案例

### HCC 药物靶点发现

| 阶段 | 数量 | 说明 |
|------|------|------|
| PubMed 检索 | 9,092 篇 | 2015-2026, HCC + drug target |
| 去重过滤后 | 8,991 篇 | 去除评论/新闻/信件 |
| 8维打分后 (TOTAL >= 3) | 3,507 篇 | 用于 LLM 微调语料 |
| 8维打分后 (TOTAL >= 5) | 1,005 篇 | 高质量金标准 |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

### 待改进方向

- [ ] 支持 Scopus / Web of Science 检索
- [ ] 支持本地 LLM（Ollama/LM Studio）一键配置
- [ ] 支持 PDF 全文打分（目前仅支持摘要）
- [ ] 增加 PRISMA 流程图自动生成
- [ ] 增加更多研究领域的预设维度模板

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [Biopython](https://biopython.org/) - PubMed Entrez API
- [DeepSeek](https://deepseek.com/) - LLM 打分后端
- [WorkBuddy](https://www.codebuddy.cn/) - AI 开发辅助

---

*Built for researchers who value both rigor and efficiency.*
