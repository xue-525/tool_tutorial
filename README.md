# PDF to PPTX 转换工具

将 PDF 文件转换为 Markdown 格式，再转换为 PowerPoint 演示文稿的完整指南。

## 📋 目录

- [概述](#概述)
- [工具介绍](#工具介绍)
- [安装指南](#安装指南)
- [使用步骤](#使用步骤)
- [完整示例](#完整示例)
- [常见问题](#常见问题)

## 概述

本项目提供了一个完整的工作流程，用于将 PDF 文件（如学术论文、文档等）转换为 PowerPoint 演示文稿：

```
PDF 文件 → Markdown 文件 → PPTX 演示文稿
```

### 工作流优势

- ✅ **保留格式** - 保留 PDF 的文本、表格、列表等结构
- ✅ **易于编辑** - Markdown 格式便于手动调整和编辑
- ✅ **灵活转换** - 可在任何步骤进行手动干预
- ✅ **批量处理** - 支持脚本化批量转换

## 工具介绍

### MarkItDown

**用途**: 将 PDF 文件转换为 Markdown 格式

- 由 Microsoft 开发
- 支持多种文档格式（PDF、DOCX、PPTX 等）
- 保留文档结构和格式
- GitHub: https://github.com/microsoft/markitdown

### Pandoc

**用途**: 将 Markdown 文件转换为 PowerPoint 格式

- 通用文档转换工具
- 支持 40+ 种文档格式
- 高度可定制化
- 官网: https://pandoc.org

## 安装指南

### 1. 安装 MarkItDown

#### 方法 A: 使用 pip 安装（推荐）

```bash
pip install markitdown
```

#### 方法 B: 从源码安装

```bash
# 克隆仓库
git clone https://github.com/microsoft/markitdown.git

# 进入目录
cd markitdown

# 安装依赖
pip install -e .
```

**验证安装**:
```bash
markitdown --version
```

### 2. 安装 Pandoc

#### macOS 用户

使用 Homebrew 安装：
```bash
brew install pandoc
```

#### Ubuntu/Debian 用户

```bash
sudo apt-get update
sudo apt-get install pandoc
```

#### Windows 用户

下载安装程序：https://github.com/jgm/pandoc/releases/latest

或使用 Chocolatey：
```bash
choco install pandoc
```

#### 其他系统

访问官方下载页面：https://pandoc.org/installing.html

**验证安装**:
```bash
pandoc --version
```

### 3. 可选：安装 LibreOffice（增强 PDF 处理）

为了更好地处理复杂 PDF 文件，建议安装 LibreOffice：

#### macOS
```bash
brew install libreoffice
```

#### Ubuntu/Debian
```bash
sudo apt-get install libreoffice
```

#### Windows
下载安装程序：https://www.libreoffice.org/download/download/

## 使用步骤

### 步骤 1: 将 PDF 转换为 Markdown

```bash
markitdown input.pdf > output.md
```

**参数说明**:
- `input.pdf` - 输入的 PDF 文件路径
- `output.md` - 输出的 Markdown 文件路径
- `>` - 重定向输出到文件

**示例**:
```bash
# 转换论文
markitdown research_paper.pdf > paper.md

# 转换报告
markitdown annual_report.pdf > report.md
```

### 步骤 2: 编辑 Markdown 文件（可选）

转换后的 Markdown 文件可以进行手动编辑，以优化内容结构：

```bash
# 使用你喜欢的编辑器打开
nano output.md
# 或
vim output.md
# 或
code output.md  # VS Code
```

### 步骤 3: 将 Markdown 转换为 PowerPoint

```bash
pandoc -f markdown -t pptx input.md -o output.pptx
```

**参数说明**:
- `-f markdown` - 指定输入格式为 Markdown
- `-t pptx` - 指定输出格式为 PowerPoint
- `input.md` - 输入的 Markdown 文件
- `-o output.pptx` - 输出的 PowerPoint 文件

**示例**:
```bash
# 基础转换
pandoc -f markdown -t pptx paper.md -o paper.pptx

# 转换并指定输出路径
pandoc paper.md -o /path/to/output.pptx
```

### 高级 Pandoc 选项

#### 自定义幻灯片尺寸

```bash
pandoc -f markdown -t pptx input.md -o output.pptx \
  --slide-level=2
```

#### 使用参考文档样式

```bash
pandoc -f markdown -t pptx input.md \
  -o output.pptx \
  --reference-doc=template.pptx
```

#### 添加元数据

在 Markdown 文件开头添加 YAML 前置元数据：

```markdown
---
title: "演示文稿标题"
author: "作者名称"
date: "2026-05-17"
---

# 内容从这里开始
```

然后转换：
```bash
pandoc input.md -o output.pptx
```

## 完整示例

### 场景 1: 快速转换论文为演示文稿

```bash
# 步骤 1: PDF 转 Markdown
markitdown my_research_paper.pdf > paper.md

# 步骤 2: Markdown 转 PowerPoint
pandoc -f markdown -t pptx paper.md -o paper.pptx

# 完成！paper.pptx 已生成
```

### 场景 2: 批量转换多个 PDF 文件

创建脚本 `batch_convert.sh`：

```bash
#!/bin/bash

# 创建输出目录
mkdir -p output/md
mkdir -p output/pptx

# 遍历所有 PDF 文件
for pdf_file in *.pdf; do
    # 获取不含扩展名的文件名
    filename="${pdf_file%.*}"
    
    echo "正在处理: $pdf_file"
    
    # 转换为 Markdown
    markitdown "$pdf_file" > "output/md/${filename}.md"
    
    # 转换为 PowerPoint
    pandoc -f markdown -t pptx "output/md/${filename}.md" \
        -o "output/pptx/${filename}.pptx"
    
    echo "✓ 完成: ${filename}.pptx"
done

echo "所有转换完成！"
```

运行脚本：
```bash
chmod +x batch_convert.sh
./batch_convert.sh
```

### 场景 3: 使用自定义模板

```bash
# 首先，用 PowerPoint 创建或下载一个模板
# 然后使用它作为参考文档

pandoc -f markdown -t pptx input.md \
  -o output.pptx \
  --reference-doc=my_template.pptx
```

## 常见问题

### Q1: MarkItDown 无法正确识别 PDF 中的表格？

**解决方案**:
- 确保 PDF 不是扫描的图像
- 尝试在 PDF 编辑器中重新保存文件
- 考虑手动编辑生成的 Markdown 文件

### Q2: 转换后的 Markdown 文件过长如何处理？

**解决方案**:
```bash
# 分割过长的 Markdown 文件
# 或手动编辑后再转换

# 例如，只转换前 N 行
head -100 output.md | pandoc -f markdown -t pptx -o output.pptx
```

### Q3: 如何在 PowerPoint 中保留原始格式和样式？

**解决方案**:
1. 创建一个带有你想要样式的参考 PowerPoint 文件
2. 使用 `--reference-doc` 参数：
```bash
pandoc input.md -o output.pptx --reference-doc=styled_template.pptx
```

### Q4: 转换后的 PowerPoint 中的图像不显示？

**解决方案**:
- 确保图像路径正确
- 在 Markdown 中使用相对路径
- 将所有相关资源放在同一目录中

### Q5: 可以同时指定多个输入文件吗？

**是的**:
```bash
pandoc -f markdown -t pptx file1.md file2.md -o combined.pptx
```

### Q6: 如何指定每个幻灯片的标题级别？

```bash
# --slide-level 指定标题级别
# 1 = H1 作为幻灯片分割点
# 2 = H2 作为幻灯片分割点（默认）

pandoc -f markdown -t pptx input.md -o output.pptx --slide-level=1
```

## 工作流最佳实践

1. **验证 PDF 质量** - 确保 PDF 不是扫描图像
2. **预处理** - 使用 PDF 编辑器调整格式（如果需要）
3. **转换为 Markdown** - 运行 MarkItDown
4. **审查 Markdown** - 检查转换结果并手动调整
5. **优化结构** - 添加合适的标题级别和分割
6. **转换为 PPTX** - 运行 Pandoc
7. **最终审查** - 在 PowerPoint 中检查并进行最后的调整

## 故障排除

### 命令未找到错误

```bash
# 如果出现 "command not found" 错误

# 检查 MarkItDown 是否安装
pip show markitdown

# 检查 Pandoc 是否安装
pandoc --version

# 如果没有安装，使用上面的安装指南重新安装
```

### 权限被拒绝

```bash
# Linux/macOS 用户
chmod +x batch_convert.sh
./batch_convert.sh

# 或使用 sudo（不推荐）
sudo pandoc -f markdown -t pptx input.md -o output.pptx
```

### 文件编码问题

```bash
# 如果遇到编码问题，指定编码
markitdown --encoding utf-8 input.pdf > output.md
```

## 相关资源

- [MarkItDown 官方文档](https://github.com/microsoft/markitdown)
- [Pandoc 官方文档](https://pandoc.org/)
- [Pandoc 在线演示](https://pandoc.org/try/)
- [Markdown 基础教程](https://www.markdown.xyz/)

## 许可证

此项目涉及的工具遵循各自的开源许可证：
- MarkItDown: MIT License
- Pandoc: GNU General Public License v2

## 贡献

如果你有任何改进建议或发现问题，欢迎提交 Issue 或 Pull Request。

---

**最后更新**: 2026-05-17

**版本**: 1.0.0