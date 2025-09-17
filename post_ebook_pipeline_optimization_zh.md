# YC AI Startup School 电子书：字幕抓取与文本优化技术纪实

本文记录了本仓库为“YC AI Startup School”电子书项目所做的一系列工程化改造：从字幕抓取的稳定性强化，到转录文本的清洗、元数据补齐，再到章节的结构化润色，最后实现一键构建全书。

## 背景与目标

- 将 YC AI Startup School 系列视频整理为电子书：一讲一章，并可导出合并稿。
- 解决“字幕抓取易失败、文本可读性差、章节缺少元信息”等痛点。
- 提供可复现的离线工作流，最小化依赖，必要时利用浏览器登录态提取字幕。

## 方案总览

本次改造围绕三条主线展开：

1) 字幕抓取稳健化（多路径兜底）
2) 文本清洗与元数据结构化
3) 章节润色与成书

对应新增/优化脚本：

- `scripts/download_subs.py`：强化 yt-dlp 驱动的字幕下载与 VTT 解析。
- `scripts/fetch_yc_ai_startup_school.py`：兼容新版 `youtube-transcript-api` 的对象化返回，改进容错。
- `scripts/enrich_and_clean.py`：对 `talks.json` 进行清洗并补齐日期、规范来源链接。
- `scripts/polish_chapters.py`：去口语、大小写矫正、自动插入小标题，提升章节可读性与结构化程度。

## 字幕抓取：多路径策略

为对抗平台风控与环境差异，我们实现了“三线并行、优先可用”的抓取策略：

- A. `youtube-transcript-api`：直接拉取官方/自动字幕；失败则尝试英文翻译轨道（新增对象返回兼容）。
- B. `yt-dlp` + 浏览器登录态：通过 `--cookies-from-browser chrome` 或 `--cookies cookies.txt` 下载 `*.vtt` 字幕。
- C. Playwright UI 抓取（备选）：打开“显示字幕”面板抓取文本，适合被 API 限制时的人机可视兜底。

其中 B 方案经过参数优化以适配最新风控：

- 自动探测 `yt-dlp` 路径（PATH、Homebrew、用户目录、`.venv`）。
- 使用 `--extractor-args "youtube:player_client=web,web_creator,ios|njsig"` 提升成功率。
- 容忍无视频流场景，仅取字幕文件。

## 文本清洗与元数据补齐

考虑到原始 VTT 常包含噪声（WEBVTT 头、Kind/Language、UI 注释、roll-up 重复、字符级打点 `<c>` 等），我们做了如下处理：

- 解析 VTT 时：
  - 跳过 `WEBVTT/Kind/Language/Style/Region` 行与时间轴行；
  - 去除 `<...>`、`[Music]/[Applause]/[Laughter]/[Inaudible]` 等注记；
  - 识别 roll-up 字幕：保留扩展行、消除重复短行；
  - 按长度合并为自然段（约 800 字），避免“每句一段”的碎片化；
  - 跨 cue 去重，段内去重。

- `scripts/enrich_and_clean.py`：
  - 用 `yt-dlp -J` 拉取视频 `upload_date`，标准化为 `YYYY-MM-DD` 写回 `talks.json`；
  - 规范 `source_url`；
  - 统一空白与标点空格，消除基本噪声。

## 章节润色与结构化

`scripts/polish_chapters.py` 提供进一步的语言层优化：

- 去口语（保守策略）：`um/uh/you know/I mean/kind of/sort of/okay/yeah/right` 等；对 “like,” 在疑似语气用法下清理。
- 大小写矫正：句首大写、代词 `I` 纠正、常见缩写（I'm/I've/…）与术语（AI、YC）规范。
- 自动小标题：按篇幅将正文切分为 2–5 个区块，插入 “Introduction/Key Ideas/Technical Insights/Applications/Conclusion” 等通用标题，保证结构一致性。

说明：脚本遵循“最小侵入、避免语义误删”的原则。如需更“激进”清洗（更强的口语/赘词删除、断句重排、摘要化），可在此基础上加一层高阶润色策略。

## 可复现步骤

1) 发现与导出视频清单（可选）

```bash
python3 scripts/fetch_yc_ai_startup_school.py --series yc-ai-startup-school --export-videos
```

2) 使用浏览器登录态下载字幕（推荐）

```bash
# 首次建议先试跑少量
python3 scripts/download_subs.py --series yc-ai-startup-school --browser chrome --limit 3

# 全量
python3 scripts/download_subs.py --series yc-ai-startup-school --browser chrome
```

3) 清洗并补齐元数据

```bash
python3 scripts/enrich_and_clean.py --series yc-ai-startup-school --use-yt-dlp --browser chrome
```

4) 生成章节与成书

```bash
python3 scripts/ingest_json.py --series yc-ai-startup-school --overwrite
python3 scripts/build_book.py --series yc-ai-startup-school
```

5) 章节润色（去口语/大小写/小标题）

```bash
# 全量润色
python3 scripts/polish_chapters.py --series yc-ai-startup-school

# 或仅处理某一章
python3 scripts/polish_chapters.py --series yc-ai-startup-school --file 14-andrej-karpathy-software-is-changing-again.md

# 重新构建汇编稿
python3 scripts/build_book.py --series yc-ai-startup-school
```

## 结果

- 14/14 个视频字幕成功写入 `data/yc-ai-startup-school/talks.json`，并生成 14 个章节（外加 `000-introduction.md`）。
- 所有章节已补齐日期与来源链接；正文完成清洗与结构化润色。
- 一键构建合并稿 `build/yc-ai-startup-school/book.md`，后续可用 Pandoc 导出 EPUB/PDF。

## 后续工作（可选）

- 更高阶的语言精修：减少口头冗词的同时保持语气；合并短句、重排断句；自动抽取小节标题（基于主题/关键词）。
- 中/英双语版：在字幕存在多语言轨道时合卷或分卷输出。
- 出版级导出：接入 Pandoc 主题、目录、封面、参考文献样式；PDF 使用 `tectonic` 或 `xelatex`。

---

以上改造确保了从“发现内容→抓取字幕→清洗补齐→章节润色→合并出书”的全链路稳定且可复现。需要进一步个性化风格或目标格式输出，欢迎在此基础上继续拓展。
