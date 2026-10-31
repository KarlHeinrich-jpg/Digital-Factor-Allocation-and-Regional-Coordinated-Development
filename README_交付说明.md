# 数字要素配置与区域协调发展：论文交付说明

**论文题目（英文）**：Nonlinear Effects of Digital Factor Allocation on Regional Coordinated Development: Evidence from a Provincial Panel Threshold Model in China

**目标期刊**：MDPI *Economies*

**当前状态**：完整英文稿（MDPI LaTeX 模板，24 页，含 6 幅图、7 张正文表、1 张附录表、30 条参考文献）＋ 数据与复现代码。

---

## 一、交付文件

| 文件 | 内容 |
|---|---|
| `paper/manuscript_MDPI_Economies.pdf` | **主稿 PDF**，MDPI Economies 模板排版，可直接用于投稿前审阅 |
| `paper/manuscript.tex` + `paper/sec1_intro.tex` … `sec6_conclusion.tex` | LaTeX 源文件（MDPI 官方 `mdpi.cls`，`economies` 选项） |
| `paper/references.bib` | BibTeX 参考文献（30 条被引条目） |
| `paper/Definitions/` | MDPI LaTeX 模板文件（`mdpi.cls`、`mdpi.bst` 等） |
| `paper/figures/` | 论文图（PNG 300 dpi + PDF 矢量；Figure 1 为 TikZ 黑白流程图） |
| `paper/tables/` | LaTeX 表格源文件 |
| `data/analysis_panel.csv` | 最终分析面板（30 省 × 2013—2021，N=270，含 DFA、RCD、控制变量等） |
| `data/income_panel.csv` | 城乡居民收入面板（含城乡收入比、质量标记） |
| `data/provincial_panel_raw.csv` | 原始省级面板（来自你此前的“经济韧性与数字碳排耦合”项目数据） |
| `output/tables/*.csv` | 全部回归结果表（可直接核对数字） |
| `output/figures/*` | 全部图件源文件 |
| `src/*.py` | 从数据清洗到图表、表格的完整脚本 |

---

## 二、研究设计

- **样本**：中国 30 个省级行政区（不含西藏、港澳台），2013—2021 年，平衡面板 N=270。2013 年起因为国家统计局实施城乡一体化住户收支调查，城乡收入口径可比。
- **核心解释变量 DFA（数字要素配置）**：4 个维度、15 个指标——数字基础设施（5）、数字产业（5）、数字金融（3）、数字人力资本（2）。维度间等权，维度内熵值法赋权。
- **被解释变量 RCD（区域协调发展）**：3 个核心维度、10 个指标——经济协调（3）、社会协调（4）、城乡协调（3）。维度间等权，维度内熵值法赋权。稳健性中使用五维 RCD（加入基础设施、生态环境）、耦合协调度（CCD）、全局熵值加权 RCD。
- **方法**：双向固定效应基准模型 + Hansen (1999) 面板门槛模型；门槛搜索为门槛变量内 80% 分位区间，bootstrap 300 次（聚类 wild bootstrap），并报告似然比置信区间。
- **控制变量**：政府干预、人均 FDI 对数、人口密度对数、私营经济活力。
- **机制变量**：产业升级、金融发展、科技投入、城乡收入比。

### 数据来源

- 《中国统计年鉴》（2014—2022）
- 《中国城市统计年鉴》（2014—2022）
- 《中国环境统计年鉴》
- 各省统计年鉴
- 北京大学数字普惠金融指数（PKU DFIIC）
- 城乡收入数据：从《中国统计年鉴》2020 版表 6-23/6-29、2022 版表 6-24/6-30 提取（RapidOCR 识别），并用“总收入 ≈ 城镇化率 × 城镇收入 + (1−城镇化率) × 农村收入”恒等式交叉校验；少量缺失按省内线性插值补齐。

---

## 三、主要结果（与论文表格一致）

### 1. 基准回归（表 3，被解释变量 RCD）

| 模型 | DFA 系数 | 标准误 | p 值 |
|---|---:|---:|---:|
| (1) 仅 DFA + 双向 FE | 0.277** | 0.112 | 0.015 |
| (2) + 控制变量 | **0.241** | 0.118 | **0.042** |
| (3) + 区域趋势 | 0.204* | 0.118 | 0.084 |
| (4) 五维 RCD | 0.013 | 0.133 | 0.922 |

经济含义：DFA 每提高 1 个单位，RCD 约提高 0.241 个指数点；DFA 一个标准差（0.179）对应 RCD 提高约 0.043 个点（0.29 个标准差）。

### 2. 门槛模型（表 4，省份 FE，Hansen 1999）

| 门槛变量 | 门槛值 γ | 低区制 β | 高区制 β | Bootstrap p |
|---|---:|---:|---:|---:|
| **ln(人均 GDP)** | **10.589** | **0.506*** | **0.677*** | **0.003** |
| 金融发展 | 10.045 | 0.578*** | 0.267*** | 0.010 |
| DFA 自身 | 0.178 | 0.549*** | 0.661*** | 0.137 |
| 科技投入 | 0.856 | 0.812*** | 0.627*** | 0.120 |
| 私营经济 | 368.402 | 0.652*** | 0.573*** | 0.107 |

- 人均 GDP 门槛 10.589 约合 **39,700 元/人**；跨过门槛后 DFA 的边际关联从 0.506 升至 0.677（约 +34%），支持“吸收能力”假说。
- 金融发展门槛的高区制只有 **30 个观测**：北京、上海、天津各 9 年（27 个）＋青海 3 年。该结果需谨慎解读，论文中已说明。
- DFA 自身、科技投入、私营经济门槛的 bootstrap p 值均 >0.10，不能拒绝线性原假设。

### 3. 区域异质性（表 5，双向 FE）

| 地区 | DFA 系数 | 标准误 | p |
|---|---:|---:|---:|
| 东部 | 0.227 | 0.234 | 0.337 |
| 中部 | 0.192 | 0.341 | 0.576 |
| **西部** | **0.555*** | 0.125 | **0.000** |
| 东北 | -0.223 | 0.285 | 0.450 |

西部效应最强且稳健；省份 FE 下四个地区系数均为正（东部 0.296***、中部 0.485***、西部 0.535***、东北 0.096***）。

### 4. 稳健性（表 6，DFA 系数）

| 设定 | 系数 | p |
|---|---:|---:|
| 基准 | 0.241** | 0.042 |
| 全局熵值加权 RCD | 0.349** | 0.024 |
| 等权 DFA | 0.298** | 0.038 |
| 剔除直辖市 | 0.288** | 0.026 |
| 2013—2019 | 0.283** | 0.022 |
| 1%/99% 缩尾 | 0.302** | 0.014 |
| 五维 RCD | 0.013 | 0.922 |
| CCD | 0.118 | 0.683 |
| 熵值加权 DFA | 0.186 | 0.291 |
| 滞后一期 DFA | 0.139 | 0.344 |
| 加额外控制变量 | 0.213 | 0.124 |

### 5. 机制（表 7）

- DFA → 科技投入：6.290**（双向 FE）
- DFA → 金融发展：8.885***（双向 FE）
- DFA → 产业升级：144.903***（省份 FE）
- DFA → 城乡收入比：+0.715**（双向 FE，短期扩大差距）；−1.279***（省份 FE，长期缩小差距）
- 中介变量在 RCD 方程中不显著，论文将机制证据表述为“渠道证据/提示性证据”，未做正式中介效应断言。

---

## 四、必须知道的研究局限（论文已写入 Limitations，但这里再强调）

1. **主门槛结果对区域趋势/年份固定效应敏感**：基准门槛模型按 Hansen (1999) 只含省份固定效应；加入区域特定线性趋势后，人均 GDP 门槛的 bootstrap p 值约为 0.47；加入年份固定效应后门槛不再显著。论文将其解释为“长期结构特征”，并明确不能当作短期因果效应。若审稿人追问，这是最需要准备回应的地方。
2. **不能作严格因果识别**：没有外生工具变量；滞后 DFA 不显著；可能存在反向因果和遗漏变量。论文使用“associated with / suggests / consistent with”等克制表述，并在局限中说明。
3. **金融发展门槛的高区制样本很小**（30 个观测，主要是京津沪），不能推广到所有高金融发展省份。
4. **五维 RCD、CCD、熵值加权 DFA、滞后 DFA 均不显著**：论文没有隐藏这些结果，而是解释为“核心三维度（经济—社会—城乡）是 DFA 的主要作用面，基础设施/生态维度响应较慢；熵值 DFA 被 IPv4/域名等少数指标主导”。这是论文的“scope condition”，不是完美的稳健性。
5. **指数构建依赖指标选择与赋权**：已用等权 DFA、全局熵值 RCD、五维 RCD、CCD 等替代口径检验；结果并非全部显著，需在审稿回复中如实说明。
6. **城乡收入数据**：来自年鉴扫描表的 OCR + 恒等式校验；个别单元格存在测量误差，2013 年统计口径变化也需注意。
7. **作者信息已按要求填写**：一作王俊峰（北京工商大学马克思主义学院，eventhat@btbu.edu.cn，ORCID 0009-0004-5051-4277）；共同一作 Jiayi Wang（Digital College, BTBU，2401050126@st.btbu.edu.cn，ORCID 0009-0005-2206-6857）；三作/通讯 Yile Wang（School of Economics, BTBU，2401050128@st.btbu.edu.cn，ORCID 0009-0008-3195-5631）。投稿前请再核对邮箱、ORCID 与作者顺序。
8. **参考文献**：30 条被引条目均已进入 PDF；中文文献做了英文翻译并标注 “(in Chinese)”。投稿前请用 MDPI/EndNote 再核对卷期页码和 DOI；`references.bib` 中另有 2 条未被引用的条目（`acemoglu2011`、`rodrik2016`），可删除或补引。
9. **地图与台湾**：图 2 已把台湾作为中国地图的一部分画出（浅灰色填充，图内无额外文字说明）；台湾和西藏因数据不可得未进入回归样本，图注已说明。地图由 `src/china_map_taiwan.py` 生成，台湾多边形来自 `src/taiwan_province.geojson`。正式投稿如期刊要求官方边界，请替换为有审图号的官方边界文件，但不要删除南海小图。
10. **Table 1 较密**：25 个指标压在一页，排版偏紧；如审稿人要求，可拆成 DFA、RCD 两张表或把定义移到附录。

---

## 五、复现方式

环境：Python 3.13，pandas、numpy、statsmodels、linearmodels、matplotlib、python-docx、rapidocr_onnxruntime；LaTeX：TeX Live 2025（pdflatex + bibtex）。

```bash
cd F:/work-environment-for-dsh/digital-factor-rcd

# 1. 城乡收入 OCR（如已有 data/income_panel.csv 可跳过）
python src/01b_ocr_income_rapid.py
python src/02_build_income_panel.py

# 2. 构建 DFA / RCD 指数
python src/03_build_indices.py

# 3. 门槛检验与主结果表
python src/04_threshold_test.py
python src/05_threshold_main.py
python src/07_main_results.py

# 4. 图与 LaTeX 表
python src/08_figures.py
python src/09_make_latex_tables.py

# 5. 编译黑白流程图（TikZ）
cd paper/figures
xelatex fig1_framework_tikz.tex
cd ..

# 6. 编译论文
pdflatex manuscript.tex
bibtex manuscript
pdflatex manuscript.tex
pdflatex manuscript.tex
```

说明：
- `04_threshold_test.py` 的 bootstrap 为 300 次，约几分钟；`05_threshold_main.py` 为 500 次，时间更长。
- 地图由 `C:\Users\93529\.agents\skills\yile-paper-style\scripts\china_map.py` 生成；如路径变化，修改 `output/figures/map_data.csv` 的生成和地图脚本调用。

---

## 六、投稿前待办清单（MDPI Economies）

- [ ] 核对作者顺序、单位、通讯邮箱、ORCID 与 Author Contributions（已按你提供的信息填写）；按需补充 Acknowledgments。
- [ ] 写 Cover Letter（建议强调：多维 DFA/RCD 指数、Hansen 门槛、经济吸收能力与金融发展门槛、区域异质性）。
- [ ] 在 MDPI 系统中选择 Article；上传 PDF 供审阅，接受后上传 LaTeX 源包（含 `Definitions/`、`figures/`、`tables/`、`references.bib`）。
- [ ] 核对参考文献格式（MDPI Economies 为 APA 作者-年份；当前模板已按 APA 排版）。
- [ ] 检查图 2 地图边界与版权；如需要，替换为官方审图号边界。
- [ ] 准备数据可用性说明（当前写“可向作者索取”；如愿意公开，可上传 `data/analysis_panel.csv` 到 Figshare/Zenodo 并写 DOI）。
- [ ] 如审稿人质疑门槛的稳健性，优先补：年份 FE、区域趋势、替代门槛变量、bootstrap 置信区间、剔除直辖市、滞后项；这些论文中已有部分，可直接引用。
- [ ] 如审稿人质疑因果识别，可补：历史电信基础设施/地形工具变量、政策试点 DID、系统 GMM；当前稿件明确承认是条件关联而非因果。

---

## 七、一句话总结

这篇稿子的核心卖点是：**用多维 DFA 与多维 RCD 指数，在 30 省 2013—2021 面板上发现数字要素配置对区域协调发展的正向关联，并用 Hansen 门槛模型证明这种关联在跨过经济发展门槛后更强；同时如实报告了金融发展高区制的递减、五维 RCD 的不显著和门槛对趋势设定的敏感性。** 它是一篇“有结果、也有边界”的实证论文，适合投 MDPI Economies；但门槛的稳健性和因果识别是审稿中最可能被追问的两点，投稿前请务必准备好回应。
