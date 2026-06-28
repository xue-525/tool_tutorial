# paper_figure_extractor

从论文 PDF 中自动截取图片，**按图注（`Figure N: <title>`）命名**，并生成 Markdown 索引文件。

## 工作原理

1. 用 [PyMuPDF](https://pymupdf.readthedocs.io/) 解析每页文本块，识别图注（支持 `Figure 1:`, `Fig. 2.`, `图 3` 等格式，中英文都行）。
2. 在图注上方汇总所有 image rect + vector drawing 边界框，得到完整的图区（能正确合并多 subplot 子图）。
3. 用 `page.get_pixmap(clip=bbox, dpi=...)` 把该区域渲染为 PNG。
4. 文件名形如 `figure_1_<sanitized_title>.png`。
5. 生成 `figures.txt`（Markdown 列表，包含文件名、页码、原始图注）。

如果 PDF 是扫描版（无嵌入文本），加 `--ocr` 会回退到 [pytesseract](https://github.com/madmaze/pytesseract) 做 OCR。

## 安装

```bash
cd paper_figure_extractor
pip install -r requirements.txt
```

OCR 模式额外需要系统 `tesseract` 二进制：

```bash
# Ubuntu / Debian / WSL
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim

# macOS
brew install tesseract tesseract-lang
```

## 使用

最基础的用法：

```bash
python3 main.py path/to/paper.pdf
```

默认会把图片写到 `./figures/` 目录，并生成 `./figures/figures.txt`。

### 完整参数

```
python3 main.py PDF [-o OUTPUT] [--dpi DPI] [--ocr] [--lang LANG]
```

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `PDF` | — | 输入的论文 PDF 路径（必填） |
| `-o, --output` | `figures` | 图片输出目录 |
| `--dpi` | `200` | 渲染分辨率，调高图片更清晰、文件更大 |
| `--ocr` | off | 强制走 OCR 路径（用于扫描版 PDF） |
| `--lang` | `eng+chi_sim` | Tesseract 语言包，多语言用 `+` 连接 |

### 示例

```bash
# 普通论文，输出到 ./out
python3 main.py mypaper.pdf -o out

# 高清渲染（适合做幻灯片）
python3 main.py mypaper.pdf --dpi 300

# 扫描版中文论文
python3 main.py scanned_cn.pdf --ocr --lang chi_sim+eng
```

## 输出示例

```
figures/
├── figure_1_Bar_chart_comparing_four_conditions.png
├── figure_2_Scatter_plot_of_measured_values.png
└── figures.txt
```

`figures.txt`：

```markdown
# Extracted Figures

- `figure_1_Bar_chart_comparing_four_conditions.png` (page 1): Figure 1. Bar chart comparing four conditions
- `figure_2_Scatter_plot_of_measured_values.png` (page 2): Figure 2. Scatter plot of measured values
```

## 常见问题

**没检测到任何图片？**
程序会提示 `No figures detected ... try re-running with --ocr`。先确认 PDF 里有 `Figure N:` 这样的图注；若是扫描版就加 `--ocr`。

**图区切得不完整 / 多切了文字？**
论文排版差异较大，目前的策略是「图注正上方所有视觉元素的联合 bbox」。如果遇到双栏论文图跨栏，可适当调高 `--dpi` 或事后手动裁剪。

**中文图注识别不到？**
确保 OCR 装了中文语言包（`tesseract-ocr-chi-sim`），并用 `--lang chi_sim+eng`。

## 文件结构

```
paper_figure_extractor/
├── main.py            # CLI 入口
├── extractor.py       # 提取 + OCR 后备的核心逻辑
├── captions.py        # 图注正则解析、文件名清洗
├── requirements.txt
└── README.md
```
