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
    分析资讯重要性（优化评分算法，筛选最有价值的内容）
    """
    title = news_item['title'].lower()
    summary = news_item['summary'].lower()
    text = title + ' ' + summary
    
    score = 0
    
    # 超高优先级关键词（+10分）- 重大发布和突破
    ultra_high_keywords = [
        'gpt-5', 'gpt5', 'claude 4', 'gemini ultra', 'breakthrough', '重大突破',
        'agi', '通用人工智能', 'billion dollar', '数十亿', '百亿'
    ]
    for keyword in ultra_high_keywords:
        if keyword in text:
            score += 10
    
    # 高优先级关键词（+5分）- 重要产品和公司动态
    high_priority_keywords = [
        'openai', 'anthropic', 'google ai', 'microsoft', 'meta ai', 'deepmind',
        'gpt-4', 'claude', 'gemini', 'llama', 'mistral',
        '发布', 'release', 'launch', 'announce', '开源', 'open source',
        '融资', 'funding', 'acquisition', '收购', '监管', 'regulation',
        'api', 'multimodal', '多模态', 'reasoning', '推理'
    ]
    for keyword in high_priority_keywords:
        if keyword in text:
            score += 5
    
    # 中优先级关键词（+3分）- 技术进展
    medium_priority_keywords = [
        'agent', 'autonomous', '智能体', 'rag', 'fine-tuning', '微调',
        'prompt engineering', 'embedding', 'vector database',
        'transformer', 'attention', 'dataset', '数据集',
        'benchmark', '基准测试', 'evaluation', '评估'
    ]
    for keyword in medium_priority_keywords:
        if keyword in text:
            score += 3
    
    # 应用场景关键词（+2分）- 实际应用
    application_keywords = [
        'coding', '编程', 'code generation', 'automation', '自动化',
        'customer service', '客服', 'chatbot', 'search', '搜索',
        'image generation', '图像生成', 'video', '视频'
    ]
    for keyword in application_keywords:
        if keyword in text:
            score += 2
    
    # 学术论文降权（-2分）- 除非是顶会
    if 'arxiv' in news_item.get('source', '').lower():
        score -= 2
        # 顶会论文加回来
        if any(conf in text for conf in ['neurips', 'icml', 'iclr', 'cvpr', 'acl']):
            score += 5
    
    return score


def generate_insight(news_item):
    """
    生成具体可操作的启示建议
    """
    title = news_item['title'].lower()
    summary = news_item['summary'].lower()
    text = title + ' ' + summary
    
    insights = []
    
    # 大模型发布类
    if any(word in text for word in ['gpt-4', 'gpt-5', 'claude', 'gemini', 'llama', '发布', 'release']):
        insights.append("【行动】测试新模型在你的业务场景中的表现，对比现有方案的成本和效果；关注API定价变化，评估是否切换模型")
    
    # 开源项目类
    if any(word in text for word in ['开源', 'open source', 'github', 'huggingface']):
        insights.append("【行动】Fork项目到本地测试，查看文档和示例代码；评估是否可以集成到现有工作流中，降低开发成本")
    
    # 融资投资类
    if any(word in text for word in ['融资', 'funding', 'investment', 'billion', 'million', '估值']):
        insights.append("【行动】研究被投公司的技术方向和商业模式，分析市场热点；关注投资方背景，判断赛道潜力")
    
    # 监管政策类
    if any(word in text for word in ['监管', 'regulation', 'policy', '合规', '法律']):
        insights.append("【行动】评估你的AI产品是否符合新政策要求；关注数据隐私、版权、安全等合规要点；必要时咨询法务")
    
    # AI Agent类
    if any(word in text for word in ['agent', '智能体', 'autonomous', 'workflow', '自动化']):
        insights.append("【行动】梳理你工作中的重复性任务，尝试用AI Agent替代；学习LangChain、AutoGPT等框架，构建个人工作流")
    
    # 编程开发类
    if any(word in text for word in ['coding', '编程', 'code generation', 'developer', '程序员']):
        insights.append("【行动】将AI编程助手（如Copilot、Cursor）集成到IDE中；用AI生成代码模板和单元测试，提升开发效率")
    
    # 多模态类
    if any(word in text for word in ['multimodal', '多模态', 'image', 'video', 'audio', '图像', '视频']):
        insights.append("【行动】探索多模态AI在你的业务中的应用场景，如自动生成营销素材、视频内容分析等；评估Midjourney、Runway等工具")
    
    # RAG和知识库类
    if any(word in text for word in ['rag', 'retrieval', 'knowledge base', '向量数据库', 'embedding']):
        insights.append("【行动】整理你的文档资料，搭建私有知识库；尝试用RAG技术构建企业内部的AI问答系统，提升信息检索效率")
    
    # 学术研究类
    if any(word in text for word in ['paper', '论文', 'research', 'arxiv', 'neurips', 'icml']):
        insights.append("【行动】阅读论文摘要和方法部分，了解技术原理；关注论文是否有开源代码，尝试复现关键实验")
    
    # 产品应用类
    if any(word in text for word in ['product', '产品', 'feature', '功能', '应用']):
        insights.append("【行动】分析该产品的目标用户和核心价值，思考是否有借鉴之处；注册试用，体验产品交互设计")
    
    # 默认建议
    if not insights:
        insights.append("【行动】将该资讯加入收藏或笔记，定期回顾；思考与你当前工作的关联性，是否有启发")
    
    # 返回最重要的2条建议
    return '\\n'.join(insights[:2])


def format_news_html(news_list):
    """
    格式化新闻为HTML邮件（优化版：只展示15条最有价值的资讯）
    """
    # 按重要性排序
    for news in news_list:
        news['importance'] = analyze_importance(news)
    
    news_list.sort(key=lambda x: (x['importance'], x['pub_time']), reverse=True)
    
    # 只保留前15条最有价值的资讯
    news_list = news_list[:15]
    
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
            .news-item.ultra {{ border-left-color: #8e44ad; background: #f5f0ff; border-left-width: 6px; }}
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
                <strong>📊 今日精选：</strong> 从众多资讯中为您精选 <strong>{len(news_list)} 条</strong> 最有价值的AI资讯
            </div>
    """
    
    for i, news in enumerate(news_list, 1):
        # 根据重要性分配优先级标签
        if news['importance'] >= 15:
            priority_class = 'ultra'
            priority_label = '🔥 重磅'
        elif news['importance'] >= 8:
            priority_class = 'high'
            priority_label = '⭐ 重要'
        elif news['importance'] >= 4:
            priority_class = 'medium'
            priority_label = '📌 关注'
        else:
            priority_class = ''
            priority_label = ''
        
        # 生成一句话精简概括（限制字数）
        brief_summary = news['summary'][:120] + '...' if len(news['summary']) > 120 else news['summary']
        
        html += f"""
            <div class="news-item {priority_class}">
                <div style="margin-bottom:10px;">
                    <span class="source">{news['source']}</span>
                    {f'<span class="source" style="background:#e74c3c;margin-left:10px;">{priority_label}</span>' if priority_label else ''}
                    <span style="color:#999;font-size:12px;margin-left:10px;">重要性:{news['importance']}</span>
                </div>
                <div class="title">{i}. {news['title']}</div>
                <div class="summary"><strong>📝 一句话速览：</strong>{brief_summary}</div>
                <div class="insight"><strong>💡 对你能做什么：</strong><br>{generate_insight(news).replace(chr(10), '<br>')}</div>
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
        from email.utils import formataddr
        
        message = MIMEMultipart('alternative')
        # 修复From字段格式，符合RFC5322标准
        message['From'] = formataddr(('AI资讯助手', SENDER_EMAIL))
        message['To'] = RECEIVER_EMAIL
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
