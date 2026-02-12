# -*- coding: utf-8 -*-
"""
AI资讯自动采集与推送系统
每日8:00自动搜集全球AI最新资讯并发送邮件
"""

import feedparser
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os
import time
from bs4 import BeautifulSoup
import re

# ==================== 配置区域 ====================
# 邮件配置
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'your_email@qq.com')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', 'your_qq_auth_code')  # QQ邮箱授权码
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', 'paranoiawang0818@qq.com')

# RSS订阅源配置（全球AI资讯）
RSS_FEEDS = {
    # 国内AI媒体
    '机器之心': 'https://rsshub.app/jiqizhixin/recommends',
    '量子位': 'https://rsshub.app/qbitai',
    '新智元': 'https://rsshub.app/thepaper/featured/25489',
    'AI科技评论': 'https://rsshub.app/leiphone/category/ai',
    
    # 国际AI资讯
    'OpenAI Blog': 'https://openai.com/blog/rss.xml',
    'Google AI Blog': 'https://ai.googleblog.com/feeds/posts/default',
    'DeepMind Blog': 'https://deepmind.google/blog/rss.xml',
    'MIT Technology Review AI': 'https://www.technologyreview.com/feed/',
    'The Verge AI': 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
    'VentureBeat AI': 'https://venturebeat.com/category/ai/feed/',
    
    # 学术资源
    'arXiv AI': 'https://rss.arxiv.org/rss/cs.AI',
    'arXiv ML': 'https://rss.arxiv.org/rss/cs.LG',
    'Papers With Code': 'https://rsshub.app/paperswithcode/trending',
    
    # 产业动态
    'TechCrunch AI': 'https://techcrunch.com/category/artificial-intelligence/feed/',
    'Hacker News': 'https://hnrss.org/newest?q=AI+OR+GPT+OR+LLM',
}

# ==================== 核心功能 ====================

def fetch_rss_news(feed_url, source_name, hours=24):
    """
    获取RSS源的最新资讯
    """
    try:
        feed = feedparser.parse(feed_url)
        news_list = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for entry in feed.entries[:20]:  # 限制每个源最多20条
            try:
                # 解析发布时间
                pub_time = None
                if hasattr(entry, 'published_parsed'):
                    pub_time = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    pub_time = datetime(*entry.updated_parsed[:6])
                
                # 只保留24小时内的新闻
                if pub_time and pub_time < cutoff_time:
                    continue
                
                # 提取内容
                title = entry.get('title', '无标题')
                link = entry.get('link', '')
                summary = entry.get('summary', entry.get('description', ''))
                
                # 清理HTML标签
                summary = BeautifulSoup(summary, 'html.parser').get_text()
                summary = re.sub(r'\s+', ' ', summary).strip()[:300]
                
                news_list.append({
                    'source': source_name,
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'pub_time': pub_time or datetime.now()
                })
                
            except Exception as e:
                print(f"解析条目失败 [{source_name}]: {e}")
                continue
        
        return news_list
    
    except Exception as e:
        print(f"获取RSS失败 [{source_name}]: {e}")
        return []


def analyze_importance(news_item):
    """
    分析资讯重要性（简单规则，可扩展为AI模型）
    """
    title = news_item['title'].lower()
    summary = news_item['summary'].lower()
    text = title + ' ' + summary
    
    # 高优先级关键词
    high_priority_keywords = [
        'gpt-5', 'gpt5', 'claude', 'gemini', 'breakthrough', '突破',
        'openai', 'google', 'microsoft', 'meta', 'anthropic',
        '发布', 'release', 'launch', '开源', 'open source',
        '融资', 'funding', 'billion', '亿', '监管', 'regulation'
    ]
    
    # 中优先级关键词
    medium_priority_keywords = [
        'model', 'llm', 'transformer', 'agent', '模型',
        'research', '研究', 'paper', '论文', 'dataset'
    ]
    
    score = 0
    for keyword in high_priority_keywords:
        if keyword in text:
            score += 3
    
    for keyword in medium_priority_keywords:
        if keyword in text:
            score += 1
    
    return score


def generate_insight(news_item):
    """
    生成启示（基于关键词匹配，可接入LLM优化）
    """
    title = news_item['title'].lower()
    summary = news_item['summary'].lower()
    
    insights = []
    
    if any(word in title + summary for word in ['gpt', 'claude', 'gemini', '大模型']):
        insights.append("💡 关注大模型技术演进，可能影响产品竞争格局")
    
    if any(word in title + summary for word in ['开源', 'open source', 'github']):
        insights.append("🔧 开源资源可直接应用于项目开发")
    
    if any(word in title + summary for word in ['融资', 'funding', '投资']):
        insights.append("💰 资本动向反映行业热点，可作为方向参考")
    
    if any(word in title + summary for word in ['监管', 'regulation', '政策', 'policy']):
        insights.append("⚖️ 政策变化可能影响业务合规要求")
    
    if any(word in title + summary for word in ['agent', '智能体', 'autonomous']):
        insights.append("🤖 AI Agent是当前技术前沿，值得深入研究")
    
    if not insights:
        insights.append("📊 了解行业动态，保持技术敏感度")
    
    return ' | '.join(insights)


def format_news_html(news_list):
    """
    格式化新闻为HTML邮件
    """
    # 按重要性排序
    for news in news_list:
        news['importance'] = analyze_importance(news)
    
    news_list.sort(key=lambda x: (x['importance'], x['pub_time']), reverse=True)
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 8px; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
            .news-item {{ border-left: 4px solid #667eea; padding: 20px; margin-bottom: 25px; background: #f9f9f9; border-radius: 5px; }}
            .news-item.high {{ border-left-color: #e74c3c; background: #fff5f5; }}
            .news-item.medium {{ border-left-color: #f39c12; background: #fffbf0; }}
            .source {{ display: inline-block; background: #667eea; color: white; padding: 3px 10px; border-radius: 3px; font-size: 12px; margin-bottom: 10px; }}
            .title {{ font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px 0; }}
            .summary {{ color: #555; line-height: 1.6; margin: 10px 0; }}
            .insight {{ background: #e8f4f8; border-left: 3px solid #3498db; padding: 10px; margin: 10px 0; font-size: 14px; color: #2c3e50; }}
            .link {{ color: #3498db; text-decoration: none; font-size: 14px; }}
            .link:hover {{ text-decoration: underline; }}
            .footer {{ text-align: center; color: #999; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            .stats {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI资讯日报</h1>
                <p>📅 {datetime.now().strftime('%Y年%m月%d日 %A')} | 昨日8:00 - 今日8:00</p>
            </div>
            
            <div class="stats">
                <strong>📊 今日统计：</strong> 共收集 {len(news_list)} 条资讯，来自 {len(set(n['source'] for n in news_list))} 个信息源
            </div>
    """
    
    for i, news in enumerate(news_list, 1):
        priority_class = 'high' if news['importance'] >= 6 else ('medium' if news['importance'] >= 3 else '')
        priority_label = '🔥 高优先级' if news['importance'] >= 6 else ('⭐ 中优先级' if news['importance'] >= 3 else '')
        
        html += f"""
            <div class="news-item {priority_class}">
                <span class="source">{news['source']}</span>
                {f'<span class="source" style="background:#e74c3c;margin-left:10px;">{priority_label}</span>' if priority_label else ''}
                <div class="title">{i}. {news['title']}</div>
                <div class="summary"><strong>📝 速览：</strong>{news['summary']}</div>
                <div class="insight"><strong>💡 启示：</strong>{generate_insight(news)}</div>
                <a href="{news['link']}" class="link" target="_blank">🔗 查看原文</a>
            </div>
        """
    
    html += """
            <div class="footer">
                <p>本邮件由 GitHub Actions 自动生成并发送</p>
                <p>⚙️ 技术栈：Python + RSS + GitHub Actions</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_email(subject, html_content):
    """
    发送HTML邮件
    """
    try:
        message = MIMEMultipart('alternative')
        message['From'] = Header(f"AI资讯助手 <{SENDER_EMAIL}>", 'utf-8')
        message['To'] = Header(RECEIVER_EMAIL, 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)
        
        # 连接QQ邮箱SMTP服务器
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        server.quit()
        
        print(f"✅ 邮件发送成功！收件人：{RECEIVER_EMAIL}")
        return True
    
    except Exception as e:
        print(f"❌ 邮件发送失败：{e}")
        return False


def main():
    """
    主函数
    """
    print("=" * 60)
    print("🚀 AI资讯采集系统启动")
    print(f"⏰ 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_news = []
    
    # 采集所有RSS源
    for source_name, feed_url in RSS_FEEDS.items():
        print(f"\n📡 正在采集：{source_name}")
        news = fetch_rss_news(feed_url, source_name)
        all_news.extend(news)
        print(f"   ✓ 获取 {len(news)} 条资讯")
        time.sleep(1)  # 避免请求过快
    
    print(f"\n📊 总计采集：{len(all_news)} 条资讯")
    
    if not all_news:
        print("⚠️ 未获取到任何资讯，跳过发送")
        return
    
    # 生成邮件内容
    print("\n📧 生成邮件内容...")
    subject = f"AI资讯日报 | {datetime.now().strftime('%Y-%m-%d')} | 共{len(all_news)}条"
    html_content = format_news_html(all_news)
    
    # 发送邮件
    print("\n📮 发送邮件...")
    send_email(subject, html_content)
    
    print("\n" + "=" * 60)
    print("✅ 任务完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
