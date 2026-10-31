# HANDOFF — 数字要素配置与区域协调发展论文

**交接时间**：2026-11-01  
**项目根目录**：`F:\work-environment-for-dsh\digital-factor-rcd`  
**目标期刊**：MDPI *Economies*  
**当前状态**：完整英文稿（28 页，MDPI LaTeX 模板）＋ 数据 ＋ 全套分析/绘图代码 ＋ 图表；本地在 `v2` 分支，工作区基本干净。

> **2026-11-01 第二次更新**：参考 Sustainability 18(3):1283（Gao et al. 2026）与中文稿《数字经济对区域绿色全要素生产率影响的实证分析》，新增了 **Figure 3 气泡图**（DFA×RCD×人均GDP，2013/2021 双面板）和 **Appendix B（Table A2/A3：30 省×9 年 DFA/RCD 指数值）**，并在 4.1 节补了省际排名稳定性的 Spearman 秩相关；同时修正了 4.1 节两处与数据不符的旧数字（见第 5 节末）。两篇参考文章**未**加入参考文献。

> **2026-11-01 第三次更新（重要）**：按用户要求补了空间诊断与空间扩展、子维度分解、内生性/识别检验，并**如实记录了门槛结论的软化**。新增脚本 `src/14_spatial_diagnostics.py`、`15_spatial_threshold.py`、`16_mechanism_extensions.py`、`17_endogeneity_checks.py`、`18_make_latex_spatial_tables.py`；正文新增 3.7、4.7、4.8、4.9 节与 Appendix C；摘要、引言、讨论、局限、结论同步改写。
>
> **必须知道的结论变化**：门槛“位置”稳（SAR 10.583 vs 基线 10.589），但**门槛“陡度”不稳**——SAR 的区制差 bootstrap p=0.143（不显著），SEM 把门槛推到 11.181 且斜率转为递减，交乘项不显著。论文已把门槛降级表述为“长期发展梯度”，不再写成尖锐结构断点。**不要把这两条写回“稳健因果”。**

> **2026-11-01 第四次更新**：按用户要求做了三件事——(1) 新增 sus 风格核密度演化图 `src/19_kde_figure.py`（Figure 5，DFA/RCD 四年度密度）；(2) 参考文献全面英文化：删除 6 条中文期刊文献（zhao2020/zhang2019/guo2020/zhangky2019/gan2011/huang2019），换入 Kanbur & Zhang (2005)、Economies 的 Liu et al. (2023) 与 Chen & Zhang (2025)，加上原有 Qi et al. (2025)，共 3 条 Economies 引用；年份书注释去掉 “(in Chinese)”；(3) 全文压缩：正文 12,428→8,287 词（-33%），删除重复的自我辩护段落，局限集中到 5.6，讨论由 7 小节压到 6 小节。

> **重要：用户明确要求“后面先不要动 GitHub”。新会话不要 `git push`、不要创建/合并 PR、不要改仓库设置，除非用户再次明确授权。**

---

## 1. 一分钟看懂现状

- **主稿 PDF**：`paper/manuscript_MDPI_Economies.pdf`（28 页，当前最新版，含 Figure 1–9、Table 1–11、Appendix A–C）
- **LaTeX 主文件**：`paper/manuscript.tex`
- **章节文件**：`paper/sec1_intro.tex` … `paper/sec6_conclusion.tex`
- **数据**：`data/analysis_panel.csv`（30 省 × 2013—2021，N=270，回归直接用这个）
- **代码**：`src/`（收入 OCR → 指数 → 门槛 → 表格 → 图 → LaTeX 表）
- **图**：`paper/figures/`
- **表**：`paper/tables/`
- **Git**：本地分支 `v2`，commit `b671c4f`；`main` 是 v1.0（tag `v1.0`），**没有把 v2 合并进 main**。
- **未跟踪文件**：`src/08b_maps.py`（新加的地图生成脚本）和 `HANDOFF.md`（本文件）；均未 commit，不要误删。

公开仓库（已建，但**现在不要动**）：

`https://github.com/KarlHeinrich-jpg/Digital-Factor-Allocation-and-Regional-Coordinated-Development`

- `main` = v1.0（初始公开版，Figure 1 还是旧版）
- `v2` = 新版 Figure 1 + `requirements.txt` + `CHANGELOG.md`
- 公开仓库的 `main/v1.0` PDF **不是**最新 Figure 1；最新版只在本地 `v2` 和 `paper/manuscript_MDPI_Economies.pdf`。

---

## 2. 作者信息（已按用户要求写入论文，不要随意改）

- **一作**：Junfeng Wang（王俊峰），School of Marxism, Beijing Technology and Business University, Beijing 100048, China；eventhat@btbu.edu.cn；ORCID `0009-0004-5051-4277`
- **共同一作**：Jiayi Wang，Digital College, Beijing Technology and Business University, Beijing 100048, China；2401050126@st.btbu.edu.cn；ORCID `0009-0005-2206-6857`
- **三作/通讯**：Yile Wang，School of Economics, Beijing Technology and Business University, Beijing 100048, China；2401050128@st.btbu.edu.cn；ORCID `0009-0008-3195-5631`

Author Contributions 目前写成：

> Conceptualization, J.W. (Junfeng Wang) and Y.W.; methodology, J.W. (Junfeng Wang); formal analysis, J.W. (Junfeng Wang); data curation, J.W. (Jiayi Wang); writing—original draft, J.W. (Junfeng Wang); writing—review and editing, J.W. (Jiayi Wang) and Y.W.

---

## 3. 论文结构（当前 28 页）

| 部分 | 内容 |
|---|---|
| Title / Abstract / Keywords | 英文摘要约 230 词；关键词 6 个 |
| 1. Introduction | 背景、三条文献线、三个缺口、四点贡献、结果预览 |
| 2. Literature Review and Hypotheses | 2.1 DFA–RCD；2.2 吸收能力与门槛；2.3 金融发展；2.4 区域异质性与机制；2.5 H1–H5；**Figure 1 在 H5 之后** |
| 3. Data, Variables, and Methods | 3.1 数据；3.2 DFA；3.3 RCD；3.4 熵值法；3.5 基准/门槛模型；3.6 控制变量与描述统计；Table 1、Table 2 |
| 4. Results | 4.1 时空格局（Figure 2 地图、Figure 3 气泡图、Figure 4 趋势）；4.2 基准（Table 3）；4.3 门槛（Table 4、Figure 5/6）；4.4 异质性（Table 5）；4.5 稳健性（Table 6、Figure 7）；4.6 机制（Table 7） |
| 5. Discussion | 主要发现、吸收能力/数字鸿沟、金融发展递减、区域异质性、政策含义、局限 |
| 6. Conclusions | 总结、政策、局限、未来研究 |
| Appendix A | Table A1（DFA/RCD 指标权重） |
| Appendix B | Table A2（DFA 逐年省级值）、Table A3（RCD 逐年省级值） |
| Appendix C | Table A4（交乘调节）、Table A5（分体制中介） |
| References | 30 条被引条目（APA，作者-年份） |

### 图表清单

- **Figure 1**：黑白 TikZ 概念框架
- **Figure 2**：6 张地图（3×2）——左列 DFA、右列 RCD，年份 2013/2017/2021；来源 `figures/fig_maps_6.pdf`（脚本 `src/20_maps_6panel.py`）
- **Figure 3**：4 面板合并图——(a)(b) 2013/2021 气泡图，(c)(d) 四大区域 DFA/RCD 均值趋势；来源 `figures/fig_distribution_trends.pdf`（脚本 `src/21_composite_figure.py`）
- **Figure 4**：3D 核密度曲面（DFA / RCD），照 sus 论文 Figure 6 的透视曲面画法；来源 `figures/fig_kde3d.pdf`（脚本 `src/22_kde3d_figure.py`）
- **Figure 5**：人均 GDP 门槛的 LR 曲线
- **Figure 6**：DFA–RCD 散点/分区制系数
- **Figure 7**：区域异质性与替代设定的系数森林图
- **Figure 8**：LISA 集聚图（四面板）
- **Table 1**：DFA/RCD 指标体系（长表，正文中较密）
- **Table 2**：描述统计
- **Table 3**：基准双向 FE
- **Table 4**：门槛检验与分区制系数
- **Table 5**：区域异质性
- **Table 6**：稳健性
- **Table 7**：机制
- **Table A1**：熵值权重
- **Table A2 / A3**：30 省 × 2013—2021 的 DFA / RCD 指数值，按区域分组，末列 Mean、SD、Change
- **Table 8**：全局 Moran's I（DFA/RCD × rook/逆距离平方，逐年 2013—2021）
- **Figure 8**：LISA 集聚图（DFA/RCD × 2013/2021 四面板，p<0.10，HH/LL/LH/HL/NS 五色）
- **Table 9**：空间扩展门槛（基线 / SLX / SEM / SAR + SAR 直接、间接、总效应）
- **Table 10**：四子维度分开回归、联合回归、各自门槛（含下表的 γ 与 bootstrap p）
- **Table 11**：Oster 界限 + 置换推断
- **Table A4**：交乘项调节；**Table A5**：分体制中介（a、b、a×b、bootstrap CI）

---

## 4. 研究设计与数据（务必先读）

### 4.1 样本

- 中国 30 个省级行政区（不含西藏、港澳台），2013—2021，平衡面板 **N=270**。
- 2013 年起因为国家统计局实施城乡一体化住户收支调查，城乡收入口径可比。
- 台湾、西藏因数据不可得/不可比未进入回归；但**地图必须保留台湾**（浅灰色），且保留南海小图与九段线示意。

### 4.2 核心变量

- **DFA（数字要素配置）**：4 维、15 指标
  - 数字基础设施（5）：互联网接入端口/人口、光缆密度、移动电话普及率、IPv4/人口、域名/人口
  - 数字产业（5）：软件收入/GDP、电商交易额/GDP、有电商活动企业比重、每百家企业网站数、信息化企业/人口
  - 数字金融（3）：北大数字普惠金融覆盖广度、使用深度、数字化程度
  - 数字人力资本（2）：ICT 就业占比、互联网普及率
  - 维度间等权，维度内熵值法。
- **RCD（区域协调发展）**：3 维、10 指标
  - 经济协调（3）：人均 GDP、人均社零、财政自给率
  - 社会协调（4）：居民收入、每万人医院床位、每十万人高等教育在校生、社保支出占比
  - 城乡协调（3）：城镇化率、城乡收入比（负）、城镇登记失业率（负）
  - 维度间等权，维度内熵值法；基线 RCD 是三个**原始子系统得分**的均值。
- 稳健性口径：五维 RCD（加基础设施、生态）、CCD、全局熵值 RCD、等权 DFA、熵值 DFA、PCA DFA。

### 4.3 数据来源

- 《中国统计年鉴》（2014—2022）
- 《中国城市统计年鉴》（2014—2022）
- 《中国环境统计年鉴》
- 各省统计年鉴
- 北京大学数字普惠金融指数（PKU DFIIC）

### 4.4 城乡收入数据（OCR）

- 来源：《中国统计年鉴》2020 版表 6-23/6-29、2022 版表 6-24/6-30。
- 用 RapidOCR 识别，再用恒等式校验：
  `总收入 ≈ 城镇化率 × 城镇收入 + (1−城镇化率) × 农村收入`
- 少量缺失/异常按省内线性插值或恒等式恢复。
- 脚本：`src/01b_ocr_income_rapid.py` → `src/02_build_income_panel.py`。
- 原始 OCR 宽表：`data/income_ocr_raw_wide.csv`；最终收入面板：`data/income_panel.csv`。

### 4.5 控制变量

- 政府干预（财政支出/GDP）
- 人均 FDI 对数
- 人口密度对数
- 私营经济活力（私营企业数/万人）

---

## 5. 关键结果（与论文表格一致，改稿时不要口误）

| 结果 | 数值 |
|---|---|
| 基准双向 FE（全控制） | **0.241**（SE 0.118；p=0.042） |
| 仅 DFA + 双向 FE | 0.277**（p=0.015） |
| 加区域趋势 | 0.204*（p=0.084） |
| 五维 RCD | 0.013（p=0.922） |
| **人均 GDP 门槛** | **γ=10.589**（≈39,700 元） |
| 低区制 / 高区制 | **0.506*** / **0.677*** |
| 门槛 bootstrap p | **0.003** |
| 金融发展门槛 | γ=10.045；0.578*** / 0.267***；p=0.010 |
| 金融发展高区制样本 | 30 个观测：京津沪 27 个 + 青海 3 个 |
| DFA 自身门槛 | γ=0.178；0.549*** / 0.661***；p=0.137 |
| 科技投入门槛 | γ=0.856；0.812*** / 0.627***；p=0.120 |
| 私营经济门槛 | γ=368.402；0.652*** / 0.573***；p=0.107 |
| 西部（双向 FE） | **0.555***（p<0.001） |
| 东部 / 中部 / 东北（双向 FE） | 0.227 / 0.192 / −0.223（均不显著） |
| 剔除直辖市 | 0.288**（p=0.026） |
| 2013—2019 | 0.283**（p=0.022） |
| 1%/99% 缩尾 | 0.302**（p=0.014） |
| 全局熵值 RCD | 0.349**（p=0.024） |
| 等权 DFA | 0.298**（p=0.038） |
| 熵值 DFA | 0.186（p=0.291） |
| 滞后 DFA | 0.139（p=0.344） |
| 额外控制变量 | 0.213（p=0.124） |
| DFA→科技投入 | 6.290**（双向 FE） |
| DFA→金融发展 | 8.885***（双向 FE） |
| DFA→产业升级 | 144.903***（省份 FE） |
| DFA→城乡收入比 | +0.715**（双向 FE，短期扩大）；−1.279***（省份 FE，长期缩小） |

### 空间 / 子维度 / 识别检验（2026-11-01 新增）

| 结果 | 数值 |
|---|---|
| 全局 Moran's I，DFA（rook） | 0.239—0.314，每年 p<0.05 |
| 全局 Moran's I，RCD（rook） | 0.377—0.427，每年 p<0.01 |
| 全局 Moran's I，DFA（逆距离平方） | 0.017—0.068，仅 2013/2021 边际显著 |
| 全局 Moran's I，RCD（逆距离平方） | 0.117—0.175，每年 p<0.05 |
| 省内去均值后的 Moran's I | DFA 均值 0.323、RCD 0.244，9 年中 8 年为正 |
| **DFA 与邻居 DFA 的省内相关** | **0.979 → SLX 不可识别** |
| SEM 门槛 | γ=11.181；λ=0.720；p=0.027；低 0.615 / 高 0.550（**递减**） |
| SAR 门槛 | γ=10.583；ρ=0.580；p=0.143；低 0.169 / 高 0.274 |
| SAR 直接/间接/总效应（低区制） | 0.188 / 0.214 / 0.402 |
| SAR 直接/间接/总效应（高区制） | 0.305 / 0.347 / 0.652 |
| 子维度（单独） | 基建 0.044、产业 0.069、金融 **0.134**、人力 −0.113 |
| 子维度（联合） | 基建 0.057、产业 0.069、金融 **0.151**、人力 −0.173 |
| 子维度门槛（低→高） | 基建 0.587→0.278；产业 −0.250→0.113；金融 0.168→0.234；人力 −0.341→0.102 |
| Oster δ* | 双向 FE 8.58；省份 FE 27.4；加额外控制 1.74 |
| 置换安慰剂 | F_obs=26.74 vs 置换均值 5.85（95 分位 12.00），p=0.002 |
| 交乘项（ln pgdp / fin_dev） | 0.012（p=0.904）/ −0.002（p=0.749），均不显著 |
| 分体制中介 | 三个渠道的 a×b 的 95% bootstrap CI 全部含 0 |

### 必须保留的“边界”表述

1. **主门槛对趋势设定敏感**：按 Hansen (1999) 只含省份 FE 时 p=0.003；加区域特定趋势后 bootstrap p≈0.47；加年份 FE 后不显著。论文 Limitations 已写“长期结构特征，不是短期因果效应”。不要把它写成稳健因果。
2. **金融发展门槛高区制很小**（30 个观测，主要是京津沪），不能推广到所有高金融发展省份。
3. **五维 RCD、CCD、熵值 DFA、滞后 DFA 都不显著**：论文没有隐藏，解释为 scope conditions。
4. **没有严格因果识别**：无 IV；滞后 DFA 不显著；使用 “associated with / suggests / consistent with”，不要改成 “proves/causes”。
5. **DFA 的四个维度等权、维度内熵值**；RCD 三维等权、维度内熵值；不要随意换成全局熵值当基准。

### 4.1 节描述性数字（2026-11-01 已核对并修正）

原来 4.1 节有一批早期指数版本留下的旧数字，已按 `data/analysis_panel.csv` 全部改掉。**以后改动描述性段落时，以这张表为准**：

| 指标 | 2013 | 2021 |
|---|---|---|
| DFA 全国均值 | 0.109 | 0.379 |
| RCD 全国均值 | 0.261 | 0.468 |
| DFA 标准差 / 极差 | 0.129 / 0.599 | 0.177 / 0.775 |
| RCD 标准差 / 极差 | 0.129 / 0.569 | 0.136 / 0.564 |
| DFA 最大值/最小值 | 84.7 倍（北京 / 甘肃） | 4.4 倍（北京 / 甘肃） |
| RCD 最大值/最小值 | 7.9 倍 | 3.2 倍 |
| 东部均值 DFA / RCD | 0.231 / 0.381 | 0.548 / 0.587 |
| 西部均值 DFA / RCD | 0.040 / 0.168 | 0.283 / 0.369 |

- 区域排序：**RCD 每一年都是 East > Northeast > Central > West**；DFA 在 2013—2017 是 Northeast > Central，2018 年起 Central 反超。不要再写成 "East, Central, Northeast, West"。
- 30 个省在 2013→2021 间全部两项指数都上升；按地图的固定分级，DFA 有 29 个省跨级、RCD 有 27 个省跨级。
- 省际排名 Spearman 秩相关：相邻年份 DFA ≥ 0.957（中位 0.980）、RCD ≥ 0.963（中位 0.988）；2013 vs 2021 为 0.918 / 0.899。

---

## 6. Figure 1（新版黑白 TikZ 流程图）

### 文件

- 源文件：`paper/figures/fig1_framework_tikz.tex`
- 编译产物：`paper/figures/fig1_framework_tikz.pdf`
- 论文引入：`paper/sec2_lit.tex` 末尾，`\includegraphics[width=\textwidth]{figures/fig1_framework_tikz.pdf}`

### 设计来源

参考了用户提供的 PDF：

`C:\Users\93529\Desktop\10-论文文件\sus-教育\manuscript.v7\sustainability-4495862-done.pdf`

第 6 页 Figure 1 的概念模型风格：三列标题、虚线构造分组、粗体标题 + 斜体说明、带 H 标签的实线/虚线箭头、底部理论横条。新版 Figure 1 采用了同样的视觉语言：

- 三列：DFA / Threshold conditions / RCD
- 虚线组：DFA 四维、RCD 三维、门槛条件、机制
- 每个框：粗体标题 + 斜体描述
- H1 主路径；H2 经济发展门槛（dashed）；H3 金融发展门槛（dashed）；H5 机制渠道；底部 H4 区域异质性横条
- 黑白、Times New Roman、无填充色

### 编译

必须用 **xelatex**（fontspec + Times New Roman）：

```bash
cd paper/figures
xelatex fig1_framework_tikz.tex
```

不要用 pdflatex 编译这个 standalone 文件。论文主文件仍用 pdflatex 编译，只通过 PDF 引入该图。

### 修改注意

- 不要把它换回 matplotlib 彩色图。
- 不要删除台湾地图相关的部分（Figure 2 另说）。
- 如果图内文字偏小：优先压缩左右留白/自然画布宽度，而不是把 `\textwidth` 继续放大。
- H2/H3/H5 的标签位置在 TikZ 里用绝对坐标；改文字后要重新看是否压线。

---

## 7. 地图（Figure 2）与台湾

### 文件

- 本地地图脚本：`src/china_map_taiwan.py`（基于 yile-paper-style 的 `china_map.py` 修改）
- 台湾多边形：`src/taiwan_province.geojson`（从阿里云 DataV 中国省级 GeoJSON 的台湾省提取）
- 地图生成脚本：`src/08b_maps.py`（**本轮新加，尚未 commit**）
- 输出：`output/figures/fig2a_dfa_map_2p.pdf/png`、`fig2b_rcd_map_2p.pdf/png`
- 论文用图：`paper/figures/fig2a_dfa_map_2p.pdf`、`fig2b_rcd_map_2p.pdf`

### 关键点

- 台湾**必须**出现在中国地图里；当前用**浅灰色**填充（因为台湾不在回归样本中，不能凭空赋 DFA/RCD 值）。
- 图内**没有**额外文字标注；图注写 “Tibet is shown in white and Taiwan in light gray because they are not included in the estimation sample.”
- 南海小图、九段线示意、指北针、比例尺必须保留。
- 小图位置已从原来的 `[0.775, 0.025, 0.195, 0.285]` 改为 `[0.805, 0.005, 0.175, 0.205]`，否则会遮住台湾；不要改回去。
- 台湾多边形必须用 `MultiPolygon` 的省界，不要用原来的 `taiwan_coastline.geojson`（那是 LineString，只能描边不能填充）。

### 重新生成

```bash
cd F:/work-environment-for-dsh/digital-factor-rcd
python src/08b_maps.py
```

脚本会写 `output/figures/` 并复制到 `paper/figures/`。

---

## 8. 代码与执行顺序

```bash
cd F:/work-environment-for-dsh/digital-factor-rcd

# 1. 城乡收入 OCR（已有 data/income_panel.csv 时可跳过）
python src/01b_ocr_income_rapid.py
python src/02_build_income_panel.py

# 2. 构建 DFA / RCD 指数
python src/03_build_indices.py

# 3. 门槛检验与主结果表
python src/04_threshold_test.py        # 主门槛 p 值（省份 FE，无趋势），300 次 bootstrap
python src/05_threshold_main.py       # 区域趋势下的门槛敏感性，500 次 bootstrap
python src/07_main_results.py         # 基准/异质性/稳健性/机制表

# 4. 图与 LaTeX 表
python src/08_figures.py              # Figure 4–7
python src/08b_maps.py                # Figure 2 地图
python src/09_make_latex_tables.py    # Table 2–7、A1
python src/12_bubble_figure.py        # Figure 3 气泡图（同时复制到 paper/figures）
python src/13_appendix_index_tables.py  # Table A2、A3（直接写入 paper/tables）

# 5. 空间 / 子维度 / 识别检验
python src/14_spatial_diagnostics.py   # Table 8、Figure 8，写 output/spatial/W_rook.npy
python src/15_spatial_threshold.py     # Table 9（约 3–4 分钟，含 bootstrap）
python src/16_mechanism_extensions.py  # Table 10、A4、A5（中线约 10 分钟，含中介 bootstrap）
python src/17_endogeneity_checks.py    # Table 11
python src/18_make_latex_spatial_tables.py  # 生成上述 LaTeX 表

# 5. 编译 Figure 1（TikZ，必须 xelatex）
cd paper/figures
xelatex fig1_framework_tikz.tex
cd ..

# 6. 编译论文
pdflatex manuscript.tex
bibtex manuscript
pdflatex manuscript.tex
pdflatex manuscript.tex
```

### 代码对应关系（重要）

- `04_threshold_test.py`：**论文 Table 4 的 bootstrap p 值来源**。按 Hansen (1999) 仅省份 FE；先构造 `DFA × I(q≤γ)` / `DFA × I(q>γ)`，**再组内去均值**。不要先对 DFA 去均值再乘 I，否则会得到错误的“递减”结果。
- `05_threshold_main.py`：区域特定趋势下的门槛估计；用于论文 4.3 末尾的敏感性说明（p≈0.47），不是主表。
- `07_main_results.py`：`table4_threshold.csv` 的 γ/系数用省份 FE、无趋势；p 值读自 `threshold_tests.csv`。改门槛代码时两处要同步。
- `08_figures.py`：Figure 4（趋势）、Figure 5（LR）、Figure 6（散点/分区制）、Figure 7（系数森林图）。注意文件名沿用旧编号，与论文里的 Figure 序号不一致。
- `08b_maps.py`：Figure 2 地图。
- `09_make_latex_tables.py`：从 `output/tables/*.csv` 生成 `paper/tables/*.tex`。
- `12_bubble_figure.py`：Figure 3 气泡图。泡泡面积 ∝ exp(ln_pgdp)，两面板共用同一大小尺度（所以 2013 的泡泡整体偏小，反映收入水平上升）。文件名为 `figures/fig_bubble.pdf`，**故意不用数字编号**，避免和论文 Figure 序号错位。
- `13_appendix_index_tables.py`：Table A2/A3。省名必须用英文（论文用 pdflatex 编译，中文会直接编译失败），映射表在本脚本内。列结构：省名 + 9 年 + Mean + SD + Change，`\scriptsize` + `tabcolsep=3pt`，在 394pt 版心内刚好放得下，不要再加列。
- `10_build_docx.py` / `11_build_docx_simple.py`：早期 Word 草稿构建器，**当前没有 Word 交付物**；可忽略/删除，不要当作主流程。

### 环境

- Python 3.13
- pandas、numpy、scipy、statsmodels、linearmodels、matplotlib、seaborn、scikit-learn、geopandas、shapely、openpyxl、rapidocr_onnxruntime、python-docx
- `requirements.txt` 已在 v2 分支
- TeX Live 2025（pdflatex、bibtex、xelatex）

### 已知环境坑

- 本机 `linearmodels` 7.0 在 `PanelOLS` **无固定效应**时做的是过原点回归（无截距）；不要用它跑 pooled OLS，必要时用 statsmodels LSDV。论文主表都带 FE，不受影响。
- `linearmodels` 的 `rsquared_within` 在部分设定下可能为负；需要组内 R² 时自己算。
- `china_map_taiwan.py` 依赖 `C:/Users/93529/.agents/skills/yile-paper-style/scripts/paper_style.py`；脚本里已把该路径加入 `sys.path`。换机器需改路径。
- OCR 依赖 RapidOCR；少量识别错误已用恒等式修正，不要重新随机改收入值。
- `.tmp/` 有 272MB 下载文件（年鉴扫描、pandoc、GeoJSON），已被 `.gitignore` 排除，不要提交。

---

## 9. Git / GitHub 状态（新会话务必看）

```text
main  e4c51e6  Initial public release (v1.0, tag v1.0)
v2    b671c4f  Redesign Figure 1 as a reference-style black-and-white conceptual model
```

- 当前本地分支：`v2`，工作区有未提交改动：`paper/manuscript.tex`、`paper/sec4_results.tex`、`paper/manuscript_MDPI_Economies.pdf`、`README_交付说明.md` 被修改；`src/12_bubble_figure.py`、`src/13_appendix_index_tables.py`、`paper/figures/fig_bubble.png/pdf`、`paper/tables/tableA2_dfa_values.tex`、`tableA3_rcd_values.tex`、`src/08b_maps.py`、`HANDOFF.md` 为未跟踪文件。**没有 commit、没有 push。**
- `main` = v1.0：公开仓库的初始版本，Figure 1 还是**旧版**；没有 `requirements.txt`/`CHANGELOG.md`。
- `v2` = 新 Figure 1 + requirements + changelog；**尚未合并到 main**。
- **用户要求：后面先不要动 GitHub**。因此：
  - 不要 `git push`
  - 不要创建/合并 PR
  - 不要改 repo 设置/Release
  - 不要 `git push --force`
- 如果用户以后要求更新公开仓库：先把 `src/08b_maps.py` commit 到 `v2`，再 PR `v2 → main`，合并后打 `v2.0` tag/release。不要在未授权时做。
- 仓库 URL：`https://github.com/KarlHeinrich-jpg/Digital-Factor-Allocation-and-Regional-Coordinated-Development`
- 注意：用户曾在聊天里贴过一个 GitHub PAT，已暴露；建议撤销/轮换。**不要把任何 token 写进仓库或脚本。**

### 文件状态

- `paper/manuscript_MDPI_Economies.pdf`：tracked，当前最新 28 页。
- `paper/manuscript.pdf`：本地编译产物，被 `.gitignore` 忽略；内容与上面相同。
- `paper/manuscript.aux/.log/.out/.blg/.bbl`：本地编译产物，被忽略。
- `paper/figures/*.aux/.log`：TikZ 编译产物，被忽略。
- `src/08b_maps.py`、`HANDOFF.md`：untracked；新会话可先 `git add` 到 v2（但不要 push，除非用户同意）。

---

## 10. 新会话建议的第一步（10 分钟）

1. `cd F:\work-environment-for-dsh\digital-factor-rcd`
2. `git status`，确认在 `v2`，只有 `?? src/08b_maps.py` 和 `?? HANDOFF.md`。
3. 读本文件、`README_交付说明.md`、`paper/manuscript.tex`。
4. 打开 `paper/manuscript_MDPI_Economies.pdf`，看第 1 页作者、第 6 页 Figure 1、第 11 页地图。
5. 问用户这次要改什么（文字/结果/图表/投稿材料），**不要先动 GitHub**。
6. 如果改结果：先读对应 `output/tables/*.csv` 和 `src/04/05/07`，确认口径；改完重新生成表/图/PDF。
7. 如果改 Figure 1：只改 `paper/figures/fig1_framework_tikz.tex`，xelatex 编译，不要换 matplotlib。
8. 如果改地图：只改 `src/china_map_taiwan.py`/`08b_maps.py`，保留台湾浅灰、南海小图、指北针、比例尺。
9. 最后把改动文件、PDF 页码、剩余风险写回本 HANDOFF 或新 HANDOFF。

---

## 11. 后续可做（按优先级）

1. **合并 v2 → main（等用户授权）**：把新 Figure 1、requirements、地图脚本纳入公开版；打 v2.0 tag/release。
2. **Cover letter / 投稿信**：MDPI Economies，强调多维 DFA/RCD、Hansen 门槛、吸收能力、区域异质性。
3. **审稿人最可能追问的点**：
   - 门槛对区域趋势/年份 FE 敏感 → 补年份 FE、区域趋势、替代门槛、bootstrap CI；论文已有部分。
   - 因果识别 → 历史电信基础设施/地形 IV、政策试点 DID、系统 GMM；当前明确承认是条件关联。
   - 金融发展高区制样本小 → 解释为“京津沪+青海 3 个观测”，不要过度推广。
   - RCD5/CCD/滞后 DFA 不显著 → 作为 scope condition，不要隐藏。
4. **图表打磨**：
   - Table 1 较密（25 行压一页）；可拆成 DFA/RCD 两张表或把定义移附录。
   - Figure 1 在 `\textwidth` 下图内字号约 8 pt；如嫌小，压缩自然画布宽度/左右留白。
   - 地图边界如期刊要求官方审图号，替换 `china_map_taiwan.py` 中的边界文件；不要删南海小图。
5. **参考文献**：30 条被引；中文文献已翻译并标 `(in Chinese)`；投稿前核对卷期页码/DOI。`references.bib` 另有 2 条未引用（`acemoglu2011`、`rodrik2016`），可删可补引。
6. **数据/代码发布**：公开仓库已有 panel/代码；如期刊要求，可加 Zenodo DOI，把 `v2.0` release 作为引用版本。

---

## 12. 绝对不要做的事

- 不要在没有用户明确要求时 `git push` / 开 PR / 改 GitHub 仓库。
- 不要把台湾从地图里去掉，也不要把台湾涂成某个 DFA/RCD 等级（没有数据）。
- 不要删除南海小图、九段线示意、指北针、比例尺。
- 不要把 Figure 1 换回旧的 matplotlib 彩色图，或用 pdflatex 编译 TikZ standalone。
- 不要把主门槛写成“稳健因果效应”；不要隐藏 RCD5/CCD/熵值 DFA/滞后 DFA 不显著。
- 不要改作者顺序/单位/邮箱/ORCID，除非用户明确给出新信息。
- 不要把 `.tmp/`、`paper/manuscript.aux/log`、PAT/token 提交到仓库。
- 不要凭空给台湾/西藏赋数据值。
- 不要把 Table A2/A3 的省名改回中文：主文件用 pdflatex 编译，中文会直接失败（要中文就得整套换 xelatex + ctex，不要为了两张附录表这么做）。
- 不要把 Table A2/A3 再加列（现为 13 列，394pt 版心刚好放得下）；加列会溢出。
- 不要把“门槛在空间设定下稳健”写成结论：位置稳，**陡度不稳**（SAR p=0.143、SEM 方向相反）。正文已降级为“长期发展梯度”。
- 不要把 SLX 的 0.133/0.275 当作“控制了空间溢出后的真实效应”来解释：DFA 与 W·DFA 省内相关 0.979，两者不可分离。
- 不要声称做了 IV：本数据没有历史电话普及率、地形、骨干网距离等工具变量，正文已明确说明未做。

---

## 13. 关键文件路径速查

| 用途 | 路径 |
|---|---|
| 主稿 PDF | `F:\work-environment-for-dsh\digital-factor-rcd\paper\manuscript_MDPI_Economies.pdf` |
| LaTeX 主文件 | `paper\manuscript.tex` |
| 章节 | `paper\sec1_intro.tex` … `paper\sec6_conclusion.tex` |
| 参考文献 | `paper\references.bib` |
| MDPI 模板 | `paper\Definitions\` |
| Figure 1 源 | `paper\figures\fig1_framework_tikz.tex` |
| Figure 2 地图 | `paper\figures\fig2a_dfa_map_2p.pdf`、`fig2b_rcd_map_2p.pdf` |
| 最终面板 | `data\analysis_panel.csv` |
| 收入面板 | `data\income_panel.csv` |
| 回归表 CSV | `output\tables\table2_descriptives.csv` … `table7_mechanisms.csv` |
| 指数代码 | `src\03_build_indices.py` |
| 门槛代码 | `src\04_threshold_test.py`、`05_threshold_main.py` |
| 主结果表代码 | `src\07_main_results.py` |
| 图代码 | `src\08_figures.py`（Figure 4–7）、`08b_maps.py`（Figure 2）、`12_bubble_figure.py`（Figure 3） |
| LaTeX 表代码 | `src\09_make_latex_tables.py`（Table 2–7、A1）、`13_appendix_index_tables.py`（Table A2/A3） |
| 地图引擎 | `src\china_map_taiwan.py`、`src\taiwan_province.geojson` |
| 气泡图 | `paper\figures\fig_bubble.pdf`、`paper\figures\fig_bubble.png` |
| 附录指数表 | `paper\tables\tableA2_dfa_values.tex`、`tableA3_rcd_values.tex` |
| 参考流程图 PDF | `C:\Users\93529\Desktop\10-论文文件\sus-教育\manuscript.v7\sustainability-4495862-done.pdf`（第 6 页） |
| 参考文章 1 | `D:\xwechat_files\...\2026-10\sustainability-18-01283-with-cover(3).pdf`（Gao et al. 2026，Figure 3 省级逐年矩阵、KDE 动态演化；**未引用**） |
| 参考文章 2 | `D:\xwechat_files\...\2026-09\数字经济对区域绿色全要素生产率影响的实证分析...(1)(4).docx`（Table 3 省级逐年指数矩阵、气泡图；**未引用**） |
| 中文交付说明 | `README_交付说明.md` |
| 仓库 README | `README.md` |

---

**交接结论**：论文、数据、代码、图表都齐了；当前最新版在本地 `v2` + `paper/manuscript_MDPI_Economies.pdf`，公开仓库 `main` 仍是 v1.0。新会话先读本文件、不要动 GitHub、按用户新指令在 `v2` 上继续即可。
