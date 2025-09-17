YC AI Startup School 电子书构建项目总结报告

一、项目目标
- 将 YC 的 AI Startup School 全系列演讲内容编成一本电子书：每位讲者一章，统一英文输出与格式。
- 在不下载视频本体的前提下，利用公开字幕或页面转录信息，生成结构清晰、可导出 EPUB/PDF 的稿本。

二、范围与来源
- 数据来源：YouTube（Y Combinator 官方频道的 AI Startup School 播放列表）、YC 官方站点/博客（若有文字稿）、第三方字幕（若必要）。
- 本次实现以 YouTube 官方播放列表为主，自动发现并导出视频列表，后续对每个视频尝试抓取对应的英文字幕或转录文本。

三、仓库结构与核心文件
- content/：每讲一章的 Markdown 章节（自动生成）。
- build/：构建产物（book.md、videos.json、可选 EPUB/PDF）。
- scripts/：构建与抓取工具脚本。
  - ingest_json.py：从 talks.json 生成章节文件。
  - build_book.py：合并 content/*.md 为 build/book.md（并生成内置标题页）。
  - fetch_yc_ai_startup_school.py：自动发现播放列表、导出视频清单，并尝试机器接口字幕抓取。
  - download_subs.py：基于 yt-dlp + 浏览器/文件 cookies，仅下载字幕（.vtt），并转为正文。
  - fetch_transcripts_playwright.py：基于 Playwright 的 UI/播放器数据双通道字幕抓取（不下载视频）。
  - make_placeholders.py：当无法获取字幕时，按视频列表生成占位章节（含来源链接）。
  - clean_content.py：清理除《000-introduction》外的章节，便于重新生成。
- talks.sample.json：示例输入结构（手工供稿时使用）。
- talks.json：实际抓取或人工汇总后生成的统一内容源。
- metadata.yaml：书籍元信息（标题、作者、语言等）。
- README.md：使用说明（含三条抓取路径与构建命令）。
- research_paper.md：本文档。

四、实现路线与方法
1) 播放列表发现
- 通过解析 YouTube 搜索结果与 YC 频道的 playlists 页面，自动得到 AI Startup School 的播放列表 ID，并导出视频清单至 build/videos.json。

2) 字幕抓取的三条路径（全部不下载视频本体）
- 路径 A：机器接口（首选，失败则降级）
  - youtube_transcript_api（官方/自动字幕）
  - YouTube timedtext API（直接获取 XML/JSON3/TTML/VTT）
  - 基于 watch 页面的 ytInitialPlayerResponse 解析 captionTracks.baseUrl
- 路径 B：yt-dlp + 浏览器/文件 cookies
  - 读取本机浏览器 cookies 或 cookies.txt，仅下载字幕（--skip-download，--write-auto-sub）。
  - 适用于需要登录/区域限制的字幕接口。
- 路径 C：Playwright UI/页面抓取（本次重点新增）
  - 真实浏览器加载页面，优先从 ytInitialPlayerResponse 读取字幕轨；若失败，自动点击“More actions → Show transcript/显示字幕”抓取侧栏文本。

五、关键技术挑战与诊断
- YouTube 反爬与签名（nsig）问题：
  - 多次出现“Only images are available for download”“Requested format is not available”，即使只请求字幕也会失败。
  - youtube_transcript_api 返回 TranscriptsDisabled；timedtext 返回 200 但 0 字节。
- Cookies 可用性：
  - 成功识别 cookies 并能在页面侧读到 captionTracks 元数据，但直接拉取 baseUrl 对应的字幕数据为空（200 长度 0）。
- UI 变化：
  - Playwright 能稳定加载页面，但当前账号/地区/视频设置下，UI 面板与机器接口均未提供可抓取文本。

六、当日产出与当前状态
- 完成从无到有的电子书工程脚手架：章节化内容组织、构建脚本、可选 Pandoc 导出。
- 自动发现播放列表，导出 build/videos.json（共 14 条）。
- 在字幕抓取受限情况下，生成了每讲一章的占位章节，并合并为 build/book.md。
- 实现并验证了多条抓取路径与降级策略：
  - 机器接口（失败）→ yt-dlp + cookies（失败/空数据）→ Playwright UI（当前账号/地区下同样无可抓取文本）。
- 已推送至 GitHub：Zhanbingli/my_ebooks_YC。

七、完整复现步骤（不含私有凭证）
1) 导出视频清单
- `python3 scripts/fetch_yc_ai_startup_school.py --series yc-ai-startup-school --export-videos`

2) 首选抓取路径（任选其一）
- A) yt-dlp + cookies.txt（不下载视频，仅字幕）
  - `python3 scripts/download_subs.py --series yc-ai-startup-school --cookies cookies.txt`
- B) Playwright（真实浏览器，不下载视频）
  - `python3 -m pip install --user playwright==1.46.0`
  - 小范围测试：
    - `python3 scripts/fetch_transcripts_playwright.py --series yc-ai-startup-school --cookies cookies.txt --limit 2 --headless`
  - 全量：
    - `python3 scripts/fetch_transcripts_playwright.py --series yc-ai-startup-school --cookies cookies.txt --headless`
- C) 人工供稿（完全离线）
  - 按 talks.sample.json 格式，手工整理后：
    - `python3 scripts/ingest_json.py --series yc-ai-startup-school`

3) 生成章节与合并书稿
- `python3 scripts/ingest_json.py --series yc-ai-startup-school --overwrite`
- `python3 scripts/build_book.py --series yc-ai-startup-school`（输出：build/yc-ai-startup-school/book.md）

4) 可选导出 EPUB/PDF（需 Pandoc）
- `pandoc --metadata-file=metadata/yc-ai-startup-school.yaml -o build/yc-ai-startup-school/yc-ai-startup-school.epub content/yc-ai-startup-school/*.md`
- `pandoc --metadata-file=metadata/yc-ai-startup-school.yaml -o build/yc-ai-startup-school/yc-ai-startup-school.pdf content/yc-ai-startup-school/*.md`

八、后续工作建议
- 若需“完整正文”：
  - 方案 C（建议）：仅下载音频轨并离线转写（Whisper），不下载视频画面，避免接口限制与账号/地区差异。
  - 目标：一键脚本化“音频→文本→章节→合并→EPUB/PDF”。
- UI 选择器兼容：
  - 若你的账号能在 YouTube 页面看到“Show transcript/显示字幕”，可提供精确菜单文本/截图，我将加强 Playwright 选择器以适配你的界面语言与布局。
- 元信息与排版：
  - 完善每章日期、讲者单位、演讲地点等补充信息；统一小标题、引用与代码块样式；封面与目录优化。
- 发布流程：
  - 可加 GitHub Actions，在不依赖私有 cookies 的情况下，自动构建 EPUB/PDF（仅基于已存在的 talks.json）。

九、合规与版权说明
- 本项目仅整合公开演讲内容与字幕，完整版权归原作者与 Y Combinator 所有。
- 仓库已将 cookies.txt 等私有凭证加入 .gitignore，避免泄露。
- 如用于分发，请保留来源链接与署名，遵守平台与版权方条款。

十、结语
- 今日完成了从脚手架、抓取管线到构建输出的整体工程化搭建，并验证了多条抓取路径。在当前环境与账号设置下，YouTube 端口径对字幕访问存在限制，导致无法即时获得全文。为如期交付完整电子书，下一步建议采用“仅音频离线转写”的技术路线，以稳定、可复现的方式生产高质量英文正文，并继续完善排版与导出方案。
