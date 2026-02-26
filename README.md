# AI资讯自动推送系统

## 📋 项目简介

这是一个基于 **GitHub Actions** 的全自动AI资讯采集与推送系统，每天早上8:00自动搜集全球AI最新资讯并发送到您的邮箱。

### ✨ 核心功能

- ✅ **全球资讯覆盖**：整合15+国内外顶级AI信息源
- ✅ **智能重要性排序**：自动分析资讯优先级（高/中/低）
- ✅ **结构化内容**：标题 + 一句话速览 + 具体内容 + 启示
- ✅ **精美HTML邮件**：专业排版，移动端友好
- ✅ **完全免费**：基于GitHub Actions，无需服务器
- ✅ **自动化运行**：每天北京时间8:00准时推送

---

## 🚀 快速部署指南

### 第一步：Fork 本项目到你的 GitHub

1. 访问你的GitHub账号：https://github.com/paranoiawang0818
2. 点击右上角 **Fork** 按钮，将项目复制到你的账号下

### 第二步：获取QQ邮箱授权码

**重要：这不是QQ密码，是专门的授权码！**

1. 登录 [QQ邮箱网页版](https://mail.qq.com)
2. 点击 **设置** → **账户** → 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务**
3. 开启 **POP3/SMTP服务** 或 **IMAP/SMTP服务**
4. 点击 **生成授权码**，按提示用手机QQ扫码验证
5. **复制保存授权码**（16位字符，类似：`abcdEFGH12345678`）

### 第三步：配置 GitHub Secrets

1. 进入你Fork的仓库页面
2. 点击 **Settings（设置）** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**，依次添加以下3个密钥：

| 名称 | 值 | 说明 |
|------|-----|------|
| `SENDER_EMAIL` | `你的QQ邮箱@qq.com` | 发件邮箱 |
| `SENDER_PASSWORD` | `你的16位授权码` | QQ邮箱授权码（非密码） |
| `RECEIVER_EMAIL` | `paranoiawang0818@qq.com` | 收件邮箱（你的邮箱） |

**示例：**
```
SENDER_EMAIL = 123456789@qq.com
SENDER_PASSWORD = abcdEFGH12345678
RECEIVER_EMAIL = paranoiawang0818@qq.com
```

### 第四步：启用 GitHub Actions

1. 进入仓库的 **Actions** 标签页
2. 如果看到提示 "Workflows aren't being run on this forked repository"
3. 点击绿色按钮 **I understand my workflows, go ahead and enable them**

### 第五步：测试运行

**方式1：手动触发测试**
1. 进入 **Actions** → 选择 **AI资讯自动推送** 工作流
2. 点击右侧 **Run workflow** → **Run workflow** 按钮
3. 等待1-3分钟，查看邮箱是否收到邮件

**方式2：等待自动执行**
- 系统将在每天北京时间早上8:00自动运行
- 首次部署建议先手动测试

---

## 📊 资讯来源清单

### 🇨🇳 国内顶级AI媒体
- **机器之心**：AI学术与产业并重
- **量子位**：国内AI企业动态
- **新智元**：前沿研究与产业应用
- **AI科技评论**：深度行业分析

### 🌍 国际权威资讯
- **OpenAI Blog**：GPT系列官方动态
- **Google AI Blog**：谷歌AI研究进展
- **DeepMind Blog**：前沿AI突破
- **MIT Technology Review**：技术趋势分析
- **The Verge AI**：科技产业报道
- **VentureBeat AI**：商业与投资视角

### 🎓 学术前沿
- **arXiv AI/ML**：最新论文预印本
- **Papers With Code**：开源实现与数据集

### 💼 产业动态
- **TechCrunch AI**：创业与融资新闻
- **Hacker News**：技术社区热议话题

---

## 🎨 邮件内容格式

每条资讯包含以下结构：

```
📰 [来源标签] [优先级标签]

1. 标题：OpenAI发布GPT-5多模态大模型

📝 速览：OpenAI正式发布GPT-5，支持文本、图像、音频多模态输入...

💡 启示：关注大模型技术演进，可能影响产品竞争格局 | 了解行业动态，保持技术敏感度

🔗 查看原文
```

**优先级分类：**
- 🔥 **高优先级**：重大发布、融资、监管政策
- ⭐ **中优先级**：技术研究、产品更新
- 📊 **普通资讯**：行业动态、趋势分析

---

## ⚙️ 高级配置

### 修改推送时间

编辑 `.github/workflows/ai-news-daily.yml` 文件：

```yaml
schedule:
  # 北京时间8:00 = UTC 0:00
  - cron: '0 0 * * *'
  
  # 其他时间示例：
  # 北京时间12:00 = UTC 4:00
  # - cron: '0 4 * * *'
  
  # 每天早晚各一次（8:00和20:00）
  # - cron: '0 0,12 * * *'
```

### 添加更多RSS源

编辑 `ai_news_collector.py` 文件的 `RSS_FEEDS` 字典：

```python
RSS_FEEDS = {
    '你的自定义源': 'https://example.com/rss',
    # ... 其他源
}
```

### 调整资讯数量

修改 `fetch_rss_news` 函数中的参数：

```python
for entry in feed.entries[:20]:  # 改为你想要的数量
```

---

## 🔧 故障排查

### 问题1：没有收到邮件

**检查清单：**
1. ✅ 确认QQ邮箱已开启SMTP服务
2. ✅ 确认使用的是**授权码**而非QQ密码
3. ✅ 检查GitHub Secrets配置是否正确
4. ✅ 查看Actions运行日志是否有报错

### 问题2：GitHub Actions未自动运行

**解决方案：**
1. 确认已启用Actions（Settings → Actions → General → Allow all actions）
2. Fork的仓库需要手动启用工作流
3. 检查 `.github/workflows` 文件是否存在

### 问题3：RSS源无法访问

**原因：** 部分RSS源可能需要代理或已失效

**解决方案：**
- 使用 [RSSHub](https://rsshub.app/) 提供的镜像源
- 删除无法访问的源，保留稳定源

---

## 📈 系统架构

```
┌─────────────────────────────────────────────┐
│         GitHub Actions (定时触发)            │
│              每天 8:00 UTC+8                 │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          Python 脚本执行                     │
│  1. 采集15+个RSS源（并发请求）               │
│  2. 解析XML/JSON数据                         │
│  3. 过滤24小时内资讯                         │
│  4. 智能重要性评分                           │
│  5. 生成HTML邮件                             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│         QQ邮箱 SMTP 服务                     │
│      smtp.qq.com:465 (SSL)                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│        📧 你的邮箱收到推送                   │
│     paranoiawang0818@qq.com                 │
└─────────────────────────────────────────────┘
```

---

## 🛡️ 安全说明

- ✅ 所有敏感信息（邮箱密码）存储在GitHub Secrets中，加密保护
- ✅ 代码开源透明，无隐私泄露风险
- ✅ 仅使用官方GitHub Actions运行环境
- ⚠️ **切勿**将授权码直接写入代码！

---

## 📝 更新日志

### v1.1.0
- ✨ 添加自定义内容
- ✅ 调整启示内容
- ✅ 优化概览，语言调整为中文
- ✅ 解决了部分链接打不开的问题

### v1.0.0
- ✨ 初始版本发布
- ✅ 支持15+全球AI资讯源
- ✅ 智能重要性排序
- ✅ 精美HTML邮件模板
- ✅ GitHub Actions自动化

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

**改进建议：**
- 🔍 添加更多优质RSS源
- 🤖 接入LLM生成更智能的"启示"
- 📊 增加数据可视化图表
- 🌐 支持更多邮件服务商

---

## 📄 开源协议

MIT License - 自由使用、修改、分发

---

## 💬 联系方式

- **GitHub Issues**：[提交问题](https://github.com/paranoiawang0818/ai-news-collector/issues)
- **邮箱**：paranoiawang0818@qq.com

---

## ⭐ Star History

如果这个项目对你有帮助，请给个Star支持一下！

---

**Made with ❤️ by GitHub Actions & Python**
