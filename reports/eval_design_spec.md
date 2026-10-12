# 评测集设计规范（eval set spec v1）

## 小 topic（已锁定）
日式动画制作中 Layout／原画／動画（中割り）三个环节的职责边界、输入输出、依赖关系与易混术语。

## 知识库边界（IN/OUT）
IN：
- レイアウト、原画（含二原/ラフ原/原トレ）、動画（中割り、均等割り、動画チェック/動画検査、動画番号、動画用紙）的职责、输入、输出
- 相关上游：絵コンテ、演出、作画監督（含四类细分）、クリーンアップ
- 相关下游：仕上げ（色指定/打ち込み/セル検）、撮影、背景/美術（原図、美術ボード）
- 交接与流程：作打ち、カット割り、カット袋、まき直し、引き上げ、アップ、納品、動画注意事項
- 术语辨析：動画チェック vs 動画検査、原画 vs 動画 vs 中割り、ラフ vs アタリ vs 大ラフ、レイアウト vs 絵コンテ vs 原図、色指定 vs 色彩設定、美術 vs 背景
- 视频（中文口径）：流程顺序（脚本→分镜→layout→原画→中割→上色→摄影→剪辑）、各环节产出物

OUT：声优/音乐/宣发/商业模式/动画史/作品评介/企划书细目（第2章漫画气泡文本不入库）

## 题型分布（目标 90 题：dev 30 / final 60）
1. term_def 术语定义（25）：单一词条要点
2. term_contrast 概念辨析（15）：两/三个易混术语区别
3. process_flow 流程依赖（15）：顺序、交接、上下游、输入输出
4. multi_chunk 多块综合（12）：需 2+ 知识块（如"从分镜到摄影经过哪些检查岗位"）
5. mislead 易误解题（8）：常见误区（如"動画=视频""中割り可以随意加帧"）
6. insufficient 证据不足（8）：库里没有的邻近领域问题（如具体某部作品某集的制作分工）→ 必须拒答
7. out_of_scope 知识库外（7）：完全外部（如迪士尼制作流程、3D建模细节）→ 必须拒答

## 每题字段（严格）
question_id / question / question_type / difficulty(1-3) / reference_answer /
required_facts（判分要点数组，2-5 条，每条必须能在 evidence_chunk 中找到原文支撑）/
evidence_chunk_ids（chunk_id 数组）/ source_ids / page_numbers /
answerable(bool) / acceptable_variants（可接受的其他表述）/
evaluation_notes（评分注意事项、易错点）

## 证据锚点纪律
- required_facts 每条注明锚点：{chunk_id: "原文摘录（≤40字）"}
- OCR 误读词头的词条（如 原面→原画）在 evidence 中以规范化后词头+reading 为准，并在 evaluation_notes 标注 OCR 风险
- 视频块证据标注 timestamp；书块标注 page_number
- answerable=false 的题 evidence_chunk_ids 为空，required_facts 为拒答判定要点（"库内无 X 的记载"）

## 隔离纪律
- dev set（30）：调 chunk 大小、检索参数、提示词
- final set（60）：只在最终对照实验跑一次；如重跑需记录并说明
- 过拟合风险：样本量小，报告需明示
