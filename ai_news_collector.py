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


def extract_key_sentences(text, max_sentences=2):
    """
    从文本中提取关键句子
    """
    # 清理文本
    text = text.replace('  ', ' ').strip()
    
    # 按句子分割（支持中英文标点）
    import re
    sentences = re.split(r'[.!?。！？]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    # 选择前几个有意义的句子
    key_sentences = []
    for sent in sentences[:max_sentences]:
        if len(sent) > 20:
            key_sentences.append(sent)
    
    return ' '.join(key_sentences) if key_sentences else text[:150]


def generate_chinese_summary(news_item):
    """
    基于文章内容生成中文精准概括
    直接提取文章核心内容，不做预设模板匹配
    """
    title = news_item['title']
    summary = news_item['summary']
    
    # 提取文章核心内容（优先使用摘要，提取关键句子）
    core_content = extract_key_sentences(summary, max_sentences=1)
    
    # 如果摘要太短，结合标题
    if len(core_content) < 30:
        core_content = title + ' ' + core_content
    
    # 限制长度，确保简洁
    if len(core_content) > 120:
        core_content = core_content[:120] + '...'
    
    return core_content


def extract_actionable_insight(news_item):
    """
    基于文章具体内容提取可操作建议
    直接分析文章内容，给出针对性建议
    """
    title = news_item['title']
    summary = news_item['summary']
    full_text = title + ' ' + summary
    text_lower = full_text.lower()
    
    insights = []
    
    # 分析文章提到的具体技术/工具/方法
    mentioned_items = []
    
    # 检测提到的模型/产品
    models = {
        'gpt-4': 'GPT-4', 'gpt-5': 'GPT-5', 'chatgpt': 'ChatGPT',
        'claude': 'Claude', 'gemini': 'Gemini', 'llama': 'Llama',
        'copilot': 'Copilot', 'cursor': 'Cursor',
        'midjourney': 'Midjourney', 'stable diffusion': 'Stable Diffusion',
        'sora': 'Sora', 'dall-e': 'DALL-E'
    }
    for key, name in models.items():
        if key in text_lower:
            mentioned_items.append(('model', name))
    
    # 检测提到的技术/框架
    techs = {
        'langchain': 'LangChain', 'autogpt': 'AutoGPT',
        'rag': 'RAG', 'vector database': '向量数据库',
        'fine-tuning': '微调', 'prompt engineering': '提示工程',
        'embedding': 'Embedding', 'transformer': 'Transformer'
    }
    for key, name in techs.items():
        if key in text_lower:
            mentioned_items.append(('tech', name))
    
    # 检测提到的应用场景
    applications = []
    if any(word in text_lower for word in ['coding', 'programming', 'developer', '代码', '编程']):
        applications.append('编程开发')
    if any(word in text_lower for word in ['writing', 'content', '写作', '内容']):
        applications.append('内容创作')
    if any(word in text_lower for word in ['image', 'video', '图像', '视频', 'generation']):
        applications.append('图像视频生成')
    if any(word in text_lower for word in ['data', 'analysis', '数据', '分析']):
        applications.append('数据分析')
    if any(word in text_lower for word in ['customer service', 'chatbot', '客服', '机器人']):
        applications.append('客服对话')
    if any(word in text_lower for word in ['automation', 'workflow', '自动化', '工作流']):
        applications.append('工作流自动化')
    
    # 根据检测到的内容生成具体建议
    
    # 如果有具体模型/产品被提到
    if mentioned_items:
        items_str = '、'.join([item[1] for item in mentioned_items[:2]])
        if any(item[0] == 'model' for item in mentioned_items):
            insights.append(f"【立即体验】访问官网了解{items_str}的具体功能，申请试用权限，在你的实际工作场景中测试其效果，记录使用体验和适用场景")
    
    # 如果有具体技术被提到
    tech_items = [item[1] for item in mentioned_items if item[0] == 'tech']
    if tech_items:
        tech_str = '、'.join(tech_items[:2])
        insights.append(f"【技术学习】搜索{tech_str}的官方文档和教程，了解其原理和应用场景，尝试搭建一个最小可行示例，评估是否能解决你的实际问题")
    
    # 如果有应用场景
    if applications:
        app_str = '、'.join(applications[:2])
        insights.append(f"【场景应用】思考{app_str}场景下你当前的工作流程，找出可以引入AI优化的环节，选择一款合适的工具进行试点")
    
    # 如果提到开源
    if any(word in text_lower for word in ['open source', 'github', '开源']):
        insights.append(f"【开源实践】点击原文链接查看项目GitHub仓库，阅读README了解使用方法，克隆代码到本地运行，评估是否适合集成到你的项目中")
    
    # 如果提到研究/论文
    if any(word in text_lower for word in ['paper', 'research', 'arxiv', '论文', '研究']):
        insights.append(f"【学习跟进】点击原文链接阅读论文摘要，了解核心创新点，查看是否有开源代码，如有则尝试复现关键实验，理解技术原理")
    
    # 如果提到数据/性能指标
    if any(word in text_lower for word in ['accuracy', 'performance', 'benchmark', '准确率', '性能']):
        insights.append(f"【对比评估】关注文中提到的性能数据，与你当前使用的方案进行对比，评估是否值得切换或尝试")
    
    # 如果没有提取到具体建议，基于内容生成通用建议
    if not insights:
        # 提取文章关键词
        keywords = []
        important_words = ['AI', 'model', 'tool', 'platform', 'technology', 'feature', 'update']
        for word in important_words:
            if word.lower() in text_lower:
                keywords.append(word)
        
        if keywords:
            insights.append(f"【深入了解】点击原文阅读完整内容，重点关注{'、'.join(keywords[:3])}相关信息，思考对你当前工作或学习的参考价值")
        else:
            insights.append(f"【信息跟进】点击原文链接阅读详细内容，提取核心观点和技术要点，评估是否需要进一步学习或采取行动")
    
    # 返回最多2条建议
    return '\\n\\n'.join(insights[:2])


def generate_contextual_insight(news_item):
    """
    基于文章具体内容提取可操作建议
    直接分析文章内容，给出针对性建议
    """
    return extract_actionable_insight(news_item)


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
        
        # 生成中文精准概括
        chinese_summary = generate_chinese_summary(news)
        
        # 生成基于文章内容的个性化启示
        contextual_insight = generate_contextual_insight(news)
        
        html += f"""
            <div class="news-item {priority_class}">
                <div style="margin-bottom:10px;">
                    <span class="source">{news['source']}</span>
                    {f'<span class="source" style="background:#e74c3c;margin-left:10px;">{priority_label}</span>' if priority_label else ''}
                </div>
                <div class="title">{i}. {news['title']}</div>
                <div class="summary"><strong>📝 一句话速览：</strong>{chinese_summary}</div>
                <div class="insight"><strong>💡 对你能做什么：</strong><br>{contextual_insight.replace(chr(10), '<br>')}</div>
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
