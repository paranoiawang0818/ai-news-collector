# AI资讯自动推送系统 - 部署检查清单

## ✅ 部署前准备

### 1. GitHub 账号准备
- [ ] 已有GitHub账号：https://github.com/paranoiawang0818
- [ ] 已Fork本项目到个人仓库

### 2. QQ邮箱配置
- [ ] 登录QQ邮箱：https://mail.qq.com
- [ ] 进入 设置 → 账户
- [ ] 开启 POP3/SMTP 服务
- [ ] 生成授权码（16位）：`________________`
- [ ] 已保存授权码（注意：不是QQ密码！）

### 3. GitHub Secrets 配置
进入仓库 Settings → Secrets and variables → Actions

- [ ] 添加 `SENDER_EMAIL`：你的QQ邮箱
- [ ] 添加 `SENDER_PASSWORD`：QQ邮箱授权码
- [ ] 添加 `RECEIVER_EMAIL`：paranoiawang0818@qq.com

### 4. GitHub Actions 启用
- [ ] 进入仓库 Actions 标签页
- [ ] 点击启用工作流（如有提示）

---

## 🧪 测试步骤

### 手动触发测试
1. [ ] 进入 Actions → AI资讯自动推送
2. [ ] 点击 Run workflow → Run workflow
3. [ ] 等待1-3分钟
4. [ ] 检查邮箱是否收到邮件

### 检查运行日志
- [ ] 查看Actions运行状态（绿色✅表示成功）
- [ ] 如有错误，查看详细日志排查问题

---

## 📋 常见问题自查

### 问题：没有收到邮件
- [ ] 检查QQ邮箱是否开启SMTP
- [ ] 确认使用的是授权码（非QQ密码）
- [ ] 检查垃圾邮件箱
- [ ] 查看Actions日志是否有报错

### 问题：Actions未自动运行
- [ ] 确认工作流文件路径：`.github/workflows/ai-news-daily.yml`
- [ ] 确认已启用Actions权限
- [ ] 等待到第二天8:00观察是否自动运行

### 问题：RSS源无法访问
- [ ] 检查网络连接
- [ ] 部分源可能需要时间响应
- [ ] 可删除无法访问的源

---

## 🎯 部署完成标志

- [x] ✅ 文件已创建到本地目录
- [ ] ✅ 代码已推送到GitHub仓库
- [ ] ✅ Secrets配置完成
- [ ] ✅ 手动测试成功收到邮件
- [ ] ✅ 等待次日8:00自动推送验证

---

## 📝 下一步操作

1. **将文件推送到GitHub：**
   ```bash
   cd /path/to/your/repo
   git add .
   git commit -m "Add AI news auto-push system"
   git push origin main
   ```

2. **配置Secrets（必须）**

3. **手动测试运行**

4. **等待自动推送**

---

## 🔗 快速链接

- GitHub仓库：https://github.com/paranoiawang0818
- QQ邮箱设置：https://mail.qq.com
- RSSHub文档：https://docs.rsshub.app

---

**祝部署顺利！🎉**
