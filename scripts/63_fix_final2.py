# -*- coding: utf-8 -*-
"""Fix final set evidence anchors: point to the chunks that ACTUALLY contain
each quote (chunk_id swap or append). Then rebuild + verify."""
src = open("scripts/56_final_set.py", encoding="utf-8").read()

fixes = [
    # FD-004 動画机 chunk exists (g0362) — evidence term fine but quote uses
    # different surface; replace quote with actual g0362 text
    ('"トレス台・透写台・ライトテーブル等の呼び方がある"',
     '"（トレス台）〔透写台）（ライトテーブル〕等いろいろな呼び方をする"'),
    # FD-007 演出 -> evidence chunk g0106 (アニメーションでは演出家)
    ('"作品を構成し、キャラクターの満技をつけ（満技=演技）",\n  "作品全体をまとめて方向性を指揮し、責任を持つ"],\n  ["演出"])',
     '"作品を構成し、キャラクターの満技をつけ（満技=演技）",\n  "作品全体をまとめて方向性を指揮し、責任を持つ"],\n  ["アニメーションでは演出家"], notes="演出词条头正文被双栏错位，其正文块词头为「アニメーションでは演出家」。")'),
    # FD-008: quote uses 方向性 but OCR is 方肉性
    ('"シリーズ監督が作品の方向性を各話担当演出に伝える"',
     '"シリーズ監督が作品の方肉性を各話担当演出に伝えるための打ち合わせ（方肉=方向）"'),
    # FD-016 打ち込み quote lives in 色指定 chunk (g0085); add it as evidence
    ('"害き込んでいく作業そのものは（打ち込み）ともいう"],\n  ["打ち込み"])',
     '"カットごとに色指定を、原由または動治に害き込んでいく作楽"],\n  ["色指定", "打ち込み"], notes="打ち込み定义句同时出现在色指定与打ち込み两词条。")'),
    # FD-017/FC-012/FP-006: 美術ボード actually chunk g0434 section_title=美術ポード
    ('["美術ボード"] if "美術ボード" in by_term else ["美術設定"])\n\n# --- term_contrast 12 ---',
     '["美術ポード"] if "美術ポード" in by_term else ["美術設定"])\n\n# --- term_contrast 12 ---'),
    ('["美術設定", "美術ボード"] if "美術ボード" in by_term else ["美術設定"])',
     '["美術設定", "美術ポード"] if "美術ポード" in by_term else ["美術設定"], notes="美術ボード词条OCR词头为美術ポード。")'),
    ('"背景部門ではこの美術ポードに合わせて背景画を描く"],\n  ["原図", "美術ボード"] if "美術ボード" in by_term else ["原図"])',
     '"背景部門ではこの美術ポードに合わせて背景画を描く"],\n  ["原図", "美術ポード"] if "美術ポード" in by_term else ["原図"])'),
    # FC-005 作打ち body is in chapter-3 chunk c0011; quote actual c0011 text via
    # a chapter-aware evidence: keep 演出打ち + note; replace quote with glossary one
    ('"作打ちが終わらないと現場はなにも動かないが、作打ちに入れば「とりあえず動き出す」"],\n  ["演出打ち"], notes="作打ち正文在第3章 chunks。")',
     '"シリーズ監督が作品の方肉性を各話担当演出に伝えるための打ち合わせ（演出打ち；作打ち正文见第3章块）"],\n  ["演出打ち"], notes="作打ち定义句在第3章 c0011，本题为辨析题主锚演出打ち词条。")'),
    # FC-011: カットナンバー definition lives in g0140 カット chunk
    ('"絵コンテ作成時に、最初の場師をカット①として、連番でつけられた番号（場師=場面）",',
     '"絵コンテ作成時に、最初の場師をカット①として、連番でつけられた番号、（語C-）69ページ参照（場師=場面）",'),
    ('["カット表", "動画番号"], notes="カットナンバー词条头注音OCR异常（なんば一）未独立成块；其定义句在カット表块正文（絵コンテ作成時に…連番でつけられた番号）。")',
     '["カット表", "カット", "動画番号"], notes="カットナンバー定义句在カット块正文。")'),
    # FM-001: quote surface differs; use actual
    ('"作画工程紙素材を収納するための、B4サイズ各社専用封間（カット袋）",',
     '"B4サイズ各社専用封間のこと（カット袋、封間=封筒）",'),
]
n = 0
for old, new in fixes:
    if old in src:
        src = src.replace(old, new); n += 1
    else:
        print("NOT FOUND:", old[:56].replace("\n", "\\n"))
open("scripts/56_final_set.py", "w", encoding="utf-8").write(src)
print("applied", n, "of", len(fixes))
