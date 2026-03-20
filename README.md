# AI News Auto-Push System

## 📋 Project Overview

This is a fully automated AI news collection and delivery system powered by **GitHub Actions**, designed to automatically gather the latest global AI news every morning at 8:00 AM and send it directly to your email inbox.

### ✨ Core Features

- ✅ **Global News Coverage:** Integrates over 15 top-tier domestic and international AI news sources.
- ✅ **Intelligent Prioritization:** Automatically analyzes and ranks news items by priority (High/Medium/Low).
- ✅ **Structured Content:** Includes a Title + One-sentence Summary + Detailed Content + Key Insights.
- ✅ **Beautiful HTML Emails:** Professionally formatted and mobile-friendly.
- ✅ **Completely Free:** Powered by GitHub Actions; no dedicated server required.
- ✅ **Automated Operation:** Delivered punctually every day at 8:00 AM (Beijing Time).

---

## 🚀 Quick Deployment Guide

### Step 1: Fork This Project to Your GitHub Account

1. Visit your GitHub account page.
2. Click the **Fork** button in the top-right corner to copy the project to your own account.

### Step 2: Obtain Your QQ Mail Authorization Code

**Important: This is NOT your QQ login password; it is a dedicated authorization code!** **

1. Log in to the [QQ Mail Web Version](https://mail.qq.com).
2. Click **Settings** → **Accounts** → Locate the **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV Services** section.
3. Enable **POP3/SMTP Services** or **IMAP/SMTP Services**.
4. Click **Generate Authorization Code**, then follow the prompts to scan the QR code using the QQ mobile app for verification.
5. **Copy and save the authorization code** (a 16-character string, e.g., `abcdEFGH12345678`).

### Step 3: Configure GitHub Secrets

1. Navigate to the page of the repository you forked.
2. Click **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret**, and add the following 3 secrets one by one:

| Name | Value | Description |
|------|-----|------|
| `SENDER_EMAIL` | `YourQQEmail@qq.com` | Sender's email address |
| `SENDER_PASSWORD` | `Your 16-digit authorization code` | QQ Mail authorization code (not your password) |
| `RECEIVER_EMAIL` | `paranoiawang0818@qq.com` | Recipient's email address (your email) |

**Example:**
```
SENDER_EMAIL = 123456789@qq.com
SENDER_PASSWORD = abcdEFGH12345678
RECEIVER_EMAIL = paranoiawang0818@qq.com
```

### Step 4: Enable GitHub Actions

1. Navigate to the **Actions** tab of your repository.
2. If you see the prompt: "Workflows aren't being run on this forked repository"
3. Click the green button: **I understand my workflows, go ahead and enable them**.

### Step 5: Test Run

**Method 1: Manually Trigger a Test**
1. Go to **Actions** → Select the **AI News Auto-Push** workflow.
2. Click **Run workflow** on the right side → Click the **Run workflow** button.
3. Wait 1–3 minutes, then check your email inbox to see if you have received a message.

**Method 2: Wait for Automatic Execution**
- The system will run automatically every day at 8:00 AM Beijing Time.
- For the initial deployment, it is recommended to perform a manual test first.

---

## 📊 List of News Sources

### 🇨🇳 Top Domestic AI Media
- **Synced (机器之心)**: Balancing AI academia and industry
- **Qubit (量子位)**: Updates on domestic AI enterprises
- **Xinzhiyuan (新智元)**: Frontier research and industrial applications
- **AI Technology Review (AI科技评论)**: In-depth industry analysis

### 🌍 Authoritative International News
- **OpenAI Blog**: Official updates on the GPT series
- **Google AI Blog**: Progress in Google's AI research
- **DeepMind Blog**: Breakthroughs in frontier AI
- **MIT Technology Review**: Analysis of technology trends
- **The Verge AI**: Coverage of the tech industry
- **VentureBeat AI**: Business and investment perspectives

### 🎓 Academic Frontiers
- **arXiv AI/ML**: Latest paper preprints
- **Papers With Code**: Open-source implementations and datasets

### 💼 Industry Updates
- **TechCrunch AI**: Startup and funding news
- **Hacker News**: Hot topics within the tech community

---

## 🎨 Email Content Format

Each news item follows this structure:

```
📰 [Source Tag] [Priority Tag]

1. Title: OpenAI Releases GPT-5 Multimodal Large Model

📝 Quick Glance: OpenAI officially releases GPT-5, supporting multimodal inputs including text, images, and audio...

💡 Insights: Keep an eye on the evolution of large model technology, which may impact the competitive landscape of products | Stay informed on industry dynamics to maintain technical acuity

🔗 Read Original Article
```

**Priority Classification:**
- 🔥 **High Priority**: Major releases, funding rounds, regulatory policies
- ⭐ **Medium Priority**: Technical research, product updates
- 📊 **General News**: Industry dynamics, trend analysis

---

## ⚙️ Advanced Configuration

### Modifying the Delivery Time

Edit the `.github/workflows/ai-news-daily.yml` file:

```yaml
schedule:
# 8:00 AM Beijing Time = 0:00 UTC
- cron: '0 0 * * *'

# Other time examples:
# Beijing Time 12:00 = UTC 4:00
# - cron: '0 4 * * *'

# Once in the morning and once in the evening daily (8:00 and 20:00)
# - cron: '0 0,12 * * *'
```

### Add More RSS Feeds

Edit the `RSS_FEEDS` dictionary in the `ai_news_collector.py` file:

```python
RSS_FEEDS = {
'Your Custom Feed': 'https://example.com/rss',
# ... Other feeds
}
```

### Adjust the Number of News Items

Modify the parameter within the `fetch_rss_news` function:

```python
for entry in feed.entries[:20]:  # Change this to your desired quantity
```

---

## 🔧 Troubleshooting

### Issue 1: Did not receive the email

**Checklist:**
1. ✅ Confirm that SMTP service is enabled for your QQ Mail account.
2. ✅ Confirm that you are using the **Authorization Code** rather than your QQ password.
3. ✅ Check if the GitHub Secrets configuration is correct.
4. ✅ Review the Actions run logs for any error messages.

### Issue 2: GitHub Actions did not run automatically

**Solution:**
1. Confirm that Actions are enabled (Settings → Actions → General → Allow all actions).
2. Forked repositories require workflows to be enabled manually.
3. Check if the `.github/workflows` file exists.

### Issue 3: RSS feed is inaccessible

**Cause:** Some RSS feeds may require a proxy or may have become defunct.

**Solution:**
- Use mirrored feeds provided by [RSSHub](https://rsshub.app/).
- Remove inaccessible feeds and retain the stable ones.

---

## 📈 System Architecture

```
┌─────────────────────────────────────────────┐
│         GitHub Actions (Scheduled Trigger)    │
│              Daily at 8:00 UTC+8              │
└──────────────────┬──────────────────────────┘
│
▼
┌─────────────────────────────────────────────┐
│          Python Script Execution            │
│  1. Collect 15+ RSS feeds (Concurrent Requests) │
│  2. Parse XML/JSON data                       │
│  3. │  Filter information from the last 24 hours │
│  4. Intelligent Importance Scoring           │
│  5. Generate HTML Email                      │
└──────────────────┬──────────────────────────┘
│
▼
┌─────────────────────────────────────────────┐
│         QQ Mail SMTP Service                 │
│      smtp.qq.com:465 (SSL)                  │
└──────────────────┬──────────────────────────┘
│
▼
┌─────────────────────────────────────────────┐
│        📧 Your Email Receives the Push       │
│     paranoiawang0818@qq.com                 │
└─────────────────────────────────────────────┘
```

---

## 🛡️ Security Notes

- ✅ All sensitive information (email passwords) is stored in GitHub Secrets and is protected by encryption.
- ✅ The code is open-source and transparent, posing no risk of privacy leakage.
- ✅ Only the official GitHub Actions runtime environment is used.
- ⚠️ **Never** hardcode your authorization key directly into the code!

---

## 📄 Open Source License

MIT License – Free to use, modify, and distribute.
