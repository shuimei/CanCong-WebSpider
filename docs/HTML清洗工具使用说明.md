# HTML内容清洗和提取工具使用说明

## 🎯 功能概述

HTML内容清洗工具用于将爬取的HTML文件转换为纯净的Markdown格式，专门针对政府网站、新闻网站等进行内容提取和清洗。

## 📁 相关文件

- `scripts/html_cleaner.py` - 主要清洗脚本
- `scripts/clean_duplicates.py` - 清理重复文件工具
- `webpages/` - 输入HTML文件目录（爬虫抓取的原始HTML）
- `mdpages/` - 输出Markdown文件目录（清洗后的纯净内容）

## 🚀 使用方法

### 1. 基本使用

```bash
# 运行HTML清洗脚本
python scripts/html_cleaner.py
```

### 2. 清理重复文件

```bash
# 删除带_1后缀的重复文件
python scripts/clean_duplicates.py
```

## ⚙️ 清洗功能特性

### 🧹 清洗内容

工具会自动移除以下无关内容：

**HTML标签清理：**
- 导航菜单 (`nav`, `menu`)
- 页头页脚 (`header`, `footer`)
- 侧边栏 (`aside`, `sidebar`)
- 脚本样式 (`script`, `style`)
- 表单元素 (`form`, `input`, `button`)
- 框架元素 (`iframe`)

**CSS类名过滤：**
- 导航类：`nav`, `navigation`, `menu`
- 布局类：`header`, `footer`, `sidebar`
- 广告类：`ad`, `advertisement`, `banner`
- 社交分享：`social`, `share`
- 评论分页：`comment`, `pagination`

**链接和图片：**
- 移除所有链接的href属性（保留文本）
- 移除所有图片标签
- 清理空的div和span标签

### 🎯 内容提取策略

**智能主内容识别：**
1. 优先查找标准主内容容器：
   - `main`, `article`, `[role="main"]`
   - `.content`, `.main-content`, `.article-content`
   - `#content`, `#main-content`

2. 备选方案：
   - 按文本长度排序容器
   - 选择内容最丰富的区域（>500字符）

3. 最后保障：
   - 使用body标签内容

### 📄 转换特性

**支持两种转换引擎：**
- `html2text` - 默认选择，更好的中文支持
- `markdownify` - 备选方案

**转换配置：**
- 忽略链接但保留文本
- 忽略图片
- 保留表格结构
- 使用ATX标题风格（# ## ###）
- 单行换行模式

**后处理：**
- 移除多余空行
- 清理行首行尾空白
- 保持适当的段落间距

## 📊 处理结果示例

### 处理前（HTML片段）
```html
<nav class="navbar">...</nav>
<div class="sidebar">...</div>
<article class="main-content">
    <h1>重要新闻标题</h1>
    <p>这是新闻正文内容...</p>
    <a href="link">更多信息</a>
</article>
<footer>...</footer>
```

### 处理后（Markdown）
```markdown
# 重要新闻标题

这是新闻正文内容...

更多信息
```

## 📈 使用统计

以当前项目为例：
- 输入HTML文件：612个
- 处理成功：612个
- 输出Markdown文件：566个（去重后）
- 文件大小范围：0.1KB - 47KB
- 平均处理时间：约200ms/文件

## 🔧 自定义配置

可以在`html_cleaner.py`中修改以下配置：

```python
# 修改不需要的标签
self.unwanted_tags = [
    'nav', 'header', 'footer', 'aside', 'menu',
    # 添加更多标签...
]

# 修改不需要的CSS类名
self.unwanted_classes = [
    'nav', 'navigation', 'menu',
    # 添加更多类名...
]

# 配置html2text选项
self.h2t.ignore_links = True  # 是否忽略链接
self.h2t.ignore_images = True  # 是否忽略图片
self.h2t.body_width = 0  # 行宽限制
```

## ⚠️ 注意事项

1. **文件编码**：脚本使用UTF-8编码，支持中文内容
2. **文件命名**：输出文件名基于原文件名和URL路径
3. **重复处理**：重复运行会生成带数字后缀的文件
4. **内容过滤**：只处理HTML文件，跳过其他格式
5. **错误处理**：处理失败的文件会记录错误信息

## 📚 应用场景

- **政府网站内容提取**：清洗政务信息、政策文件
- **新闻网站内容整理**：提取新闻正文，去除广告
- **学术资料处理**：整理网络资源为纯文本
- **知识库建设**：将网页内容转为可检索格式
- **内容分析预处理**：为文本分析提供干净数据

## 🎉 处理效果评估

工具特别适合处理：
- ✅ 政府官网（如：mnr.gov.cn, cq.gov.cn）
- ✅ 新闻门户（标准HTML结构）
- ✅ 学术机构网站
- ✅ 企业官网

处理效果良好的特征：
- 内容结构清晰
- 主文本区域明确
- 标准HTML语义标签