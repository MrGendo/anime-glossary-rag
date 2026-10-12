# 动画垂直领域 RAG 知识库 — 最终技术报告

日期：2026-10-12（UTC+8）
项目根：`/Users/Admin/Downloads/project/tiA_test`

---

## 1. 项目概述

- 选定小 topic：**日式动画制作中 Layout／原画／動画（中割り）的职责边界**——职责、输入输出、上下游交接、易混术语辨析。
- 选择理由：原始资料（224 页术语集 + 全流程视频）对该主题证据密度最高；术语边界清晰，可构造带唯一证据锚点的评测题；职种细分术语是 LLM 长尾知识，预期存在可测量缺口（已由对照实验证实，见 §6）。
- 知识库边界：IN=三环节及直接上下游（絵コンテ/演出/作監/動画検査/仕上げ检查/制作進行交接）；OUT=声优、音乐、商业模式、动画史、作品评介、3D 建模细节。
- 公网 URL：**https://pac-estimation-oil-health.trycloudflare.com**（cloudflared quick tunnel；免账号隧道无 SLA，随本机进程存活；已做真实公网请求验证，见 §9）
- GitHub 仓库：**https://github.com/MrGendo/anime-glossary-rag**（含 README/运行说明/.env.example；版权 PDF 与全量 OCR 数据未入库，重建脚本见 scripts/）
- 完成状态：数据处理✅ 评测集✅ 检索对照实验（B/C/D/E）✅ **答案层对照实验（A vs D）✅** Web/API✅（真实 LLM 模式）测试✅ 公网部署✅ **GitHub 提交✅** 报告✅

## 2. 资料审查与选题依据

详见 `reports/source_audit.md`（含 A/B/C/D 证据分级）。要点：

- PDF：《アニメーションの基礎知識大百科》神村幸子著，224 页，**100% 扫描型**（FreePic2Pdf 制作，0 文本层）→ macOS Vision OCR 两轮（行级→坐标框级），双栏重构，**549 词条**+59 章节块。
- 视频：BV1vRjZzUEwN《从零学动画01》968s，无 CC 字幕，AI 总结接口未登录 403 → 合法替代：yt-dlp 取音轨 + whisper.cpp small 本地转写，**315 段覆盖 98.9%**，12 个带时间戳块。
- 原始资料完全支撑方案 A，未降低证据标准，未扩充边界。补充资料：无（零外部语料混入）。
- OCR 质量：五十音单调性强校验 549 词条 210 对违例（含拉丁排序规则差异、小写假名缺表、注音误读三类），人工抽检清单已产出（data/quality/manual_review_list.md），**不冒充已人工核验**。

## 3. 技术架构

- 数据流：PDF(2x render) → Vision OCR(boxes) → 双栏重构 → 词条切分(正则+注音) → 术语规范化(注音反查) → chunks.jsonl(620) → [BM25 | FAISS(MiniLM多语言)] → hybrid(α=0.3) → 引用受控生成 → FastAPI/前端。
- 引用机制：生成层只允许引用 [E1..En] 标签；服务层把 E 标签**映射回真实命中 chunk**（越界引用→citation_parse_warning），前端展示 chunk_id/页码/分数。模型无法编造来源。
- 选型理由：Vision OCR 本机实测优于 tesseract-jpn（对照见 source_audit）；whisper.cpp 绕开 python 绑定兼容性问题；BM25+FAISS 为零服务依赖本地方案；FastAPI+单页前端最小可部署。
- 纯代码理由（题目要求）：检索/上下文组装/生成/引用/评测全链路在项目代码内（app/），仅用基础库。

## 4. 数据处理与质量评估

- 独立质检程序 `scripts/65_quality_check.py`，报告 `data/quality/quality_report.json`：
  - 620 块（549 词条/12 视频/59 章节）；空文本 0；重复 0；书籍块缺页码 0；视频块缺时间戳 0
  - 词头 OCR 误读修复 6 处（打标 headword_fixed_by_reading）；近空释义 9 词条；可疑字符块 3
  - **90 道评测题 100% 要点可回溯证据原文**（unsupported=0，空白不敏感匹配）
- 未解决：9 近空词条（跨页拼接遗留）、210 序违例的人工逐条核验（清单已出）、whisper 术语同音变体未做归一表。

## 5. 评测设计

- dev 30 题（调参用：α 扫描在其上完成）/ final 60 题（单次使用后未再调参）。
- 题型（final）：term_def 24 / term_contrast 13 / process_flow 10 / multi_chunk 6 / insufficient 4 / out_of_scope 3；54 可答+6 拒答。
- 每题字段齐全（question_id…evaluation_notes），判分要点=日文原文锚+OCR 变体注记。
- 检索指标：Recall@5 / MRR@5 / Hit@5（多证据题按命中比例计 recall；无证据的拒答题不计入检索指标分母，只进答案指标）。
- 答案层指标已实现定义（fact 覆盖率/引用正确率/拒答正确率/无依据断言率），评审方案=固定提示词 LLM 评审+人工复核（**待 key 后执行**，不虚报数字）。

## 6. 实验结果（全部真实执行输出）

### 6.1 最终集检索对照（n=54 可答题）

| 组 | Recall@5 | MRR@5 | Hit@5 | 延迟 |
|---|---|---|---|---|
| C BM25 | 0.8256 | 0.7614 | 0.9074 | 0.6ms |
| B 向量 | 0.4059 | 0.4877 | 0.5000 | 8.3ms |
| **D 混合 α=0.3** | **0.8596** | **0.7793** | **0.9444** | 8.7ms |
| E 混合+CE 重排 | 0.6667 | 0.4222 | 0.7593 | 638.5ms |

E 组说明：cross-encoder/ms-marco-MiniLM-L-6-v2 为英文检索专用重排器，对日文 query-doc 对无判别力，重排后显著劣化且延迟 ×73——**跨语语料上直接套英文 reranker 有害**（首次尝试的 multilingual CE 模型名 401 不可得，已如实记录；日文 CE 如 cl-nagoya 的 reranker 留作 next step）。

分题型 recall（BM25/向量/混合）：term_def 0.96/0.60/**1.00**；term_contrast 0.86/0.26/0.86；process_flow 0.65/0.15/0.65；multi_chunk 0.49/0.43/**0.62**。

- 关键发现：**中文问→日文词条跨语场景，向量腿（MiniLM）显著弱于 BM25 字符 bigram**；混合以 0.3 向量权重取得全面最优。
- dev 集 α 扫描（0/0.3/0.5/0.7/1.0）：recall 0.849/0.826/0.803/0.705/0.508，MRR 0.644/0.736/0.693/0.646/0.409 → 选 α=0.3。
- 优化迭代（案例3）：BM25 词头加权使单元排序测试 FAILED→PASSED。
- 局限：multi_chunk 0.62 是明显短板（多查询/查询扩展方向）；样本 54，未做显著性检验，不称统计显著。

### 6.2 拒答题（答案层实测）

A 基线 6 道库外/证据不足题**全部硬答**（幻觉率 100%）；D 混合RAG 6/6 正确拒答（「证据不足，无法从知识库回答」），拒答判定管线见 §3。

### 6.3 延迟与成本

- 检索延迟见表（亚毫秒~8.7ms）。生成层实测（答案层实验）：A 组 12.4s/题、D 组 5.7s/题；Token 总消耗 A=5,402+14,467、D=45,715+5,855（glm-4-flash 免费档，真实 usage 字段累计）。
- 请求日志（SQLite）：含 request_id/命中/分数/回答/引用/延迟/模型，持续落库。

### 6.4 答案层对照（A 基线 vs D 混合RAG）——已执行（glm-4-flash，60题×2组）

用户提供独立 ZHIPU_API_KEY 后补跑完成（scripts/81，2026-10-12）。同题集、同模型、同生成参数；A 组无证据（no_rag），D 组 hybrid(α=0.3) top-5。

| 指标 | A 基线 | D 混合RAG | 相对变化 |
|---|---|---|---|
| 要点覆盖率（严格锚串） | 0.1132 | **0.3491** | **×3.1** |
| 全要点题率 | 0.0556 | **0.2407** | **×4.3** |
| 拒答正确率（6 库外题） | 0.000（全部硬答/幻觉） | **1.000** | — |
| 引用正确率 | — | 0.6292（指向真实证据块） | — |
| 平均延迟 | 12.4s | 5.7s | -54% |
| Token（prompt/completion） | 5,402/14,467 | 45,715/5,855 | — |

- 宽松语义评分口径（关键词≥60%，scripts/84）复核：A=0.009 / D=0.264——**两种口径下结论方向一致，组间差异远大于评分器差异**。
- 人工抽检（6 题语义判定）：D 组「严格评 0 分」的 6 题中 5 题语义正确（FD-006/014/015/022/FC-001），1 题真实答错（FP-004 答成色指定表）——严格分**低估** D，真实 RAG 优势只大不小。
- 分题型（严格口径，D）：term_def 0.42 vs A 0.09；term_contrast 0.31 vs 0.08；multi_chunk 0.50 vs 0.22。
- 基线幻觉实例：A 组对 6 道库外题全部编造回答（如公司规模、行业单价）；D 组 6/6 正确拒答。
- 统计口径：n=54 可答题（106 要点）+6 拒答题；未做显著性检验（样本量限制），差值为「观察到的提升」。

## 7. 失败案例分析

`reports/failure_cases.md`：5 个真实案例（OCR 词头误读连锁 / whisper 同音变体 / BM25 长度归一化 / faiss-loky 段错误静默失败 / 隧道代理超时），每例含问题/答案/实际/证据差异/类别/根因/改进/改进前后实测数字。

## 8. AI Coding 工具与 Token 消耗

- 工具：Hermes Agent（主控，模型 glm-5.3，本会话）+ 3 个并行子 agent（glm-5.3，经 delegate_task）分别实现 ingestion/retrieval/generation；1 个子 agent 超时未完成（ingestion 主干由主控接管完成）；Claude Code 2.1.234 在环境中可用但本任务未使用其写码。
- Token 统计：**无法准确获取**——Hermes 会话与子 agent 均未暴露逐调用 token 计数。可查证事实：主控工具调用约 200+ 次；子 agent 完成 20/26/474s 运行。不编造输入/输出 token 数与费用。
- 主要消耗阶段：评测集锚点修复（11 轮 patch 迭代）、检索层调参与段错误定位。

## 9. 部署与验证

- 本机：uvicorn 127.0.0.1:8902（python3.14 venv）；最新提交后全量 pytest **57 passed, 1 skipped**。
- 公网：cloudflared quick tunnel → **https://pac-estimation-oil-health.trycloudflare.com**
- GitHub：**https://github.com/MrGendo/anime-glossary-rag**（161 文件，提交 7fc6b7b；已核验无密钥/无版权 PDF/无 data/raw）
- 真实公网验证（scripts/72_public_verify.py 实测输出）：/api/health ok(620)；/api/ask 返回 req_1aa321d26d73、top hit g0534 レイアウト撮 p202 score 54.3；前端正常；**ZHIPU_API_KEY 不在前端出现**。
- 交付前复验（2026-10-12 15:5x，重启加载 α=0.3 服务后）：/api/health ok(620, ZhipuClient, hybrid)；/api/ask 实测 req_0a7eb3d49878（タイムシート题，答出 1秒24分割/撮影伝票要点，top hits g0325 1.000/g0252 0.667/g0169 0.362 与本地 α=0.3 完全一致）；库外题 req_111ab2effeec 未编造人名、如实答「知识库无该具体信息」（refusal 标志 False，内容无幻觉，如实记录）。
- 限制：quick tunnel 免账号（无 SLA、URL 随机、进程存活期有效）；本机无 Docker（Dockerfile 已备未实测）；未登录评审者可直接访问（无鉴权=按题目要求开放）。
- 潜在成本：真 LLM 模式下 glm-4-flash 免费档；tunnel 免费；本机常驻进程约 300MB 内存。

## 10. 个人时间投入

真实记录（会话时间戳可核）：资料审查+OCR 管线约 40min（多轮引擎对照/双栏重构）；评测集编写与锚点核验约 50min（90 题逐题锚定+11 轮修复）；检索调参与段错误定位约 20min；部署+公网验证约 10min；报告 20min。非 LLM 直接执行的工作：OCR 引擎质量人工判读、评测题撰写、锚点引文逐条核对、失败案例根因判断。

## 11. 实现规划 vs 实际

计划 12 步全走完；超预期耗时：① OCR 双栏穿插问题（第一轮成果报废重做坐标框级）② whisper python 绑定兼容链（3 个方案失败后落 whisper.cpp）③ 评测锚点与 OCR 实际字符对齐（引文必须引用误读原文的设计决策）。快于预期：检索层（子 agent+接管修复一次到位）、部署（tunnel 一次成功，除代理剥离）。

## 12. 局限性与下一步

- ~~答案层对照未跑（阻塞=独立 key）~~ 已完成（§6.4，scripts/81，glm-4-flash，60 题×2 组）。
- 向量腿跨语弱 → 实验方向：日文查询改写、日英双语嵌入（multilingual-e5-base）、伪翻译查询扩展。
- multi_chunk 0.62 → 多跳检索/查询分解。
- 词头共享前缀（レイアウト vs レイアウト撮）exact-head boost 未做。
- 210 序违例人工核验、9 近空词条修复、whisper 变体归一表。
- 统计功效：54 题样本，报告差值不称显著；扩题至 120 或 bootstrap CI 是下一步。

## 13. 复现方法

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m pytest tests/ -q                     # 57 passed, 1 skipped
.venv/bin/python -m uvicorn app.main:app --port 8902     # Mock 模式
export ZHIPU_API_KEY=...                                 # 真实 LLM
.venv/bin/python scripts/64_final_retrieval.py           # 检索对照复现
.venv/bin/python scripts/65_quality_check.py             # 质量报告复现
cloudflared tunnel --url http://127.0.0.1:8902           # 公网
```

数据重建全链：scripts/01→71 按编号（渲染→OCR→双栏重构→词条→规范化→chunks→索引→评测→质检→部署验证）。
