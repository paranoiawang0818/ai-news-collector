# 📁 项目文件结构说明

```
ai-news-collector/
│
├── 📄 ai_news_collector.py          # 核心脚本：RSS采集 + 邮件发送
├── 📄 requirements.txt               # Python依赖包列表
├── 📄 README.md                      # 完整使用文档
├── 📄 DEPLOYMENT_CHECKLIST.md        # 部署检查清单
├── 📄 test_local.py                  # 本地测试脚本
├── 📄 deploy.bat                     # Windows快速部署脚本
├── 📄 .gitignore                     # Git忽略文件配置
│
└── 📁 .github/
    └── 📁 workflows/
        └── 📄 ai-news-daily.yml      # GitHub Actions工作流配置
```

---

## 📄 核心文件说明

### 1. `ai_news_collector.py` （核心脚本）

**功能模块：**
- `fetch_rss_news()` - RSS源采集
- `analyze_importance()` - 资讯重要性评分
- `generate_insight()` - 生成启示建议
- `format_news_html()` - HTML邮件生成
- `send_email()` - QQ邮箱SMTP发送

**配置项：**
- `RSS_FEEDS` - 15+个全球AI资讯源
- `SENDER_EMAIL` - 发件邮箱（从环境变量读取）
- `SENDER_PASSWORD` - 邮箱授权码（从环境变量读取）
- `RECEIVER_EMAIL` - 收件邮箱

**运行方式：**
```bash
python ai_news_collector.py
```

---

### 2. `.github/workflows/ai-news-daily.yml` （自动化配置）

**触发条件：**
- 定时触发：每天UTC 0:00（北京时间8:00）
- 手动触发：GitHub Actions页面手动运行

**执行步骤：**
1. 检出代码
2. 设置Python 3.11环境
3. 安装依赖包
4. 运行采集脚本（从Secrets读取邮箱配置）
5. 输出执行结果

**环境变量：**
- 从GitHub Secrets读取敏感信息
- 确保安全性

---

### 3. `requirements.txt` （依赖包）

```
feedparser==6.0.11      # RSS解析
requests==2.31.0        # HTTP请求
beautifulsoup4==4.12.3  # HTML解析
lxml==5.1.0             # XML解析加速
```

**安装命令：**
```bash
pip install -r requirements.txt
```

---

### 4. `test_local.py` （本地测试）

**功能：**
- 测试RSS采集功能
- 测试重要性分析
- 生成HTML预览文件（不发送邮件）
- 自动在浏览器打开预览

**运行方式：**
```bash
python test_local.py
```

**输出文件：**
- `test_email_preview.html` - 邮件预览

---

### 5. `deploy.bat` （Windows部署脚本）

**功能：**
- 初始化Git仓库
- 添加并提交文件
- 显示推送命令提示

**运行方式：**
双击运行或在命令行执行：
```bash
deploy.bat
```

---

## 🔧 配置文件位置

### GitHub Secrets（必须配置）
位置：`Settings → Secrets and variables → Actions`

| 密钥名 | 说明 | 示例 |
|--------|------|------|
| `SENDER_EMAIL` | 发件QQ邮箱 | `123456789@qq.com` |
| `SENDER_PASSWORD` | QQ邮箱授权码 | `abcdEFGH12345678` |
| `RECEIVER_EMAIL` | 收件邮箱 | `paranoiawang0818@qq.com` |

---

## 📊 数据流程

```
┌─────────────┐
│ GitHub      │
│ Actions     │ 每天8:00触发
│ (定时器)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ ai_news_collector.py            │
│                                 │
│ 1. 读取环境变量                 │
│ 2. 并发采集15+个RSS源           │
│ 3. 过滤24小时内资讯             │
│ 4. 智能评分排序                 │
│ 5. 生成HTML邮件                 │
│ 6. SMTP发送                     │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│ QQ邮箱      │
│ SMTP服务器  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 你的邮箱    │
│ 收到推送    │
└─────────────┘
```

---

## 🛠️ 自定义修改指南

### 修改推送时间
编辑 `.github/workflows/ai-news-daily.yml`：
```yaml
schedule:
  - cron: '0 0 * * *'  # 改为你想要的时间
```

### 添加RSS源
编辑 `ai_news_collector.py` 的 `RSS_FEEDS` 字典

### 修改邮件样式
编辑 `format_news_html()` 函数中的CSS样式

### 调整重要性算法
编辑 `analyze_importance()` 函数的评分规则

---

## 🔒 安全注意事项

✅ **正确做法：**
- 使用GitHub Secrets存储敏感信息
- 使用QQ邮箱授权码（非密码）
- 定期更换授权码

❌ **禁止操作：**
- 将密码写入代码
- 将Secrets提交到Git
- 公开分享授权码

---

## 📞 技术支持

遇到问题？查看以下资源：

1. **README.md** - 完整使用文档
2. **DEPLOYMENT_CHECKLIST.md** - 部署检查清单
3. **GitHub Issues** - 提交问题
4. **Actions日志** - 查看运行详情

---

**祝使用愉快！🎉**
