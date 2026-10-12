# 失败案例分析（5 个真实案例 + 修复前后实测）

数据来源：dev/final 两轮真实实验（data/eval/results/）、质量检查（data/quality/）、部署日志。
所有「改进前后」数字均为真实复测，非估算。

---

## 案例 1：OCR 词头形近误读 → 检索身份丢失（数据层→检索层连锁）

- 问题：查询「原画の仕事」时 BM25 无法命中 原画 词条——其词头被 OCR 读成「原面」（p126）。作画監督→作画監替、二原→二豚、作画→作雨、仕上検査→仕上検 同类。
- 标准答案：原画（げんが）定义（p126 正文完整）。
- 实际：检索命中其它含「原画」字符的块，身份块（词条本体）排序靠后/丢失。
- 证据差异：正文里的「原画」多为正确字形（正文大字号），词头误读集中在小字号黑体词条头。
- 错误类别：OCR 词头误读 + 分块身份依赖词头。
- 根因：Vision 对粗体小字号词条头的形近字误读（画面→酒面、背景→背界 同源）。
- 改进：按注音（reading）反查规范化映射（scripts/36），词头修复 6 处，verification_status=headword_fixed_by_reading 打标。
- 改进前后（实测）：修复后 dev 集 22 题证据块可按规范名词头命中；TD-002（原画职责）检索 top1=g0206（原画块）。
- 遗留：210 对五十音序违例中仍含 OCR 变体（背界/酒面），人工抽检清单待逐条核（data/quality/manual_review_list.md）。

## 案例 2：whisper 同音术语变体 → 视频块检索系统性失败（ASR→检索层）

- 问题：查询「layout 设计稿」无法召回视频证据——whisper 把 layout 转成「Lightout/Lineout」（v0004/v0006），「一原」转成「一元」，「中割」转成「中歌/中哥」。
- 标准答案：PV-002（layout 环节产出）。
- 实际检索：BM25 字符 bigram 无交集 → miss。
- 证据差异：视频块存在且内容正确，仅词形同音漂移。
- 错误类别：ASR 同音异字（中文专有名词 OOV）。
- 根因：whisper-small 中文模型对中英混杂术语的同音归一。
- 改进：评测题锚定改引转写原文变体并在 notes 标注（Lightout=layout）；检索层未做变体归一（列为 next step）。
- 改进前后（实测）：PV-002 证据锚定从 v0003/v0004（无法支撑）改为 v0004/v0005（引文逐字命中），质检 unsupported 从 3→0。

## 案例 3：BM25 长度归一化惩罚词典长释义（检索排序错误）

- 问题：查询「作画監督」时，含词头 2 次的短块（c008 样例）排在 300 字定义块（c001 样例）之前。
- 标准答案：作画監督定义块。
- 实际：定义块 rank 2+。
- 错误类别：检索排序错误（长度归一化 vs 词典体裁）。
- 根因：BM25Okapi 文档长度归一化天然偏向短文；词典语料中词条身份=词头。
- 改进：词头加权（HEADWORD_BOOST=3.0，命中 section_title 或正文词头前缀的块分数×3，bm25.py）。
- 改进前后（实测）：单元测试 test_exact_term_ranks_first 从 FAILED→PASSED（22/22 绿）；dev 集 MRR 0.644→（同权重融合后）0.736。

## 案例 4：faiss/loky C 库冲突段错误（基础设施，静默失败）

- 问题：同一进程先建 BM25 再建 VectorRetriever 后，嵌入阶段 Segfault 11，进程无输出死亡（首次表现为后台任务「完成」但无结果文件）。
- 错误类别：依赖冲突 + 静默失败。
- 根因：py3.14 下 faiss-cpu 与 sentence-transformers 的 loky 多进程在特定初始化顺序下 C 层冲突。
- 定位过程：探针隔离（scripts/52）单组件逐级加载全通 → 锁定「组合+顺序」触发。
- 改进：向量索引独立进程构建并持久化（scripts/53），评测加载 data/indexes/vector（scripts/54/64）；OMP_NUM_THREADS=1。
- 改进前后（实测）：segfault 复现路径废弃；final 集三组检索对照一次跑通（scripts/64 输出完整指标）。
- 关联教训：与 OCR Swift fflush 静默失败同型——**脚本打印 success 但产物缺失**，必须以产物文件存在性为准。

## 案例 5：quick tunnel 代理超时（部署）

- 问题：cloudflared quick tunnel 首次请求 api.trycloudflare.com 超时失败。
- 错误类别：环境（代理）。
- 根因：shell 继承 Vortex 代理 env，代理不转发该域名。
- 改进：env -u 显式剥离代理变量后重启。
- 改进前后（实测）：失败（context deadline exceeded）→ 获得公网 URL 并通过 scripts/72 全部断言（health/ask/frontend/无 key 泄漏）。

## 附加观察（非案例）：查询「レイアウトとは」top1=レイアウト撮（g0534）而非本体 g0533——词头加权对共享前缀词条无区分度，需 exact-head boost 进阶版（已列 next step，未实施不虚报）。

## 案例 6（补充，真实压测）：英文 cross-encoder 重排在日文语料上有害（检索重排）

- 问题：E 实验组对 hybrid(α=0.3) top-20 用 cross-encoder/ms-marco-MiniLM-L-6-v2 重排，最终 top-5 指标全面劣化。
- 标准答案：final 集 54 题证据块。
- 实际：recall@5 0.8596→0.6667，MRR 0.7793→0.4222，延迟 8.7ms→638.5ms（×73）。
- 证据差异：CE 把 BM25 词头精确命中的证据块压后，召回无意义候选。
- 错误类别：模型选型错误（语言域不匹配）。
- 根因：ms-marco CE 为英文 IR 训练，对日文 query-doc 对打分无判别力；先尝试的 multilingual CE（cross-encoder/multilingual-MiniLM-L12-v2）模型仓库 401 不可得。
- 改进：降级路径按设计触发（NotImplementedError→上层退回 hybrid）；正确方向是日文 CE（如 cl-nagoya/reranker-base）——未实施，不虚报。
- 结论：重排不是免费增益，语言域匹配是前置条件。
