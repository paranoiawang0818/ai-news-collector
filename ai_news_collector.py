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


def translate_to_chinese(text):
    """
    简单的英文到中文翻译映射
    基于常见AI术语和句式进行翻译
    """
    # 定义翻译映射表
    translations = {
        # 常见动词
        'announces': '宣布',
        'launches': '推出',
        'releases': '发布',
        'introduces': '推出',
        'unveils': ' unveiled',
        'debuts': '首次亮相',
        'introducing': '推出',
        'presents': '展示',
        'reveals': ' revealed',
        
        # 常见名词
        'new model': '新模型',
        'new feature': '新功能',
        'new product': '新产品',
        'ai model': 'AI模型',
        'language model': '语言模型',
        'multimodal model': '多模态模型',
        'open source': '开源',
        'api': 'API接口',
        'benchmark': '基准测试',
        'performance': '性能',
        'accuracy': '准确率',
        'efficiency': '效率',
        'capability': '能力',
        'feature': '功能',
        'update': '更新',
        'version': '版本',
        
        # 常见形容词
        'improved': '改进的',
        'enhanced': '增强的',
        'advanced': '先进的',
        'powerful': '强大的',
        'faster': '更快的',
        'better': '更好的',
        'larger': '更大的',
        'smaller': '更小的',
        
        # 常见句式
        'is now available': '现已可用',
        'is now open': '现已开放',
        'is released': '已发布',
        'can now': '现在可以',
        'allows users to': '允许用户',
        'enables': '使能够',
        'supports': '支持',
        'includes': '包括',
        'offers': '提供',
        'provides': '提供',
        
        # 技术术语
        'training': '训练',
        'inference': '推理',
        'fine-tuning': '微调',
        'prompt': '提示词',
        'token': '令牌',
        'parameter': '参数',
        'dataset': '数据集',
        'algorithm': '算法',
        'architecture': '架构',
        
        # 应用场景
        'coding': '编程',
        'writing': '写作',
        'analysis': '分析',
        'generation': '生成',
        'translation': '翻译',
        'summarization': '摘要',
        'classification': '分类',
        'prediction': '预测',
    }
    
    # 转换为小写进行匹配
    text_lower = text.lower()
    result = text
    
    # 替换匹配的词组
    for eng, chn in translations.items():
        if eng.lower() in text_lower:
            # 保留原始大小写匹配
            import re
            result = re.sub(re.escape(eng), chn, result, flags=re.IGNORECASE)
    
    return result


def generate_chinese_summary(news_item):
    """
    基于文章内容生成中文概括
    提取文章核心内容并翻译为中文
    """
    title = news_item['title']
    summary = news_item['summary']
    
    # 提取核心句子
    import re
    text = summary if len(summary) > 50 else title + ' ' + summary
    
    # 分割句子并选择第一句
    sentences = re.split(r'[.!?。！？]+', text)
    first_sentence = ''
    for sent in sentences:
        sent = sent.strip()
        if len(sent) > 20:
            first_sentence = sent
            break
    
    if not first_sentence:
        first_sentence = text[:150]
    
    # 翻译为中文
    chinese_summary = translate_to_chinese(first_sentence)
    
    # 限制长度
    if len(chinese_summary) > 120:
        chinese_summary = chinese_summary[:120] + '...'
    
    return chinese_summary


def generate_actionable_insight(news_item):
    """
    基于文章具体内容生成建议
    不使用预设语料库，直接分析文章内容
    """
    title = news_item['title']
    summary = news_item['summary']
    full_text = (title + ' ' + summary).lower()
    
    # 提取文章中提到的具体名词（技术、产品、公司等）
    import re
    
    # 提取大写单词（通常是产品名、公司名）
    capitalized_words = re.findall(r'\b[A-Z][a-zA-Z]+\b', title)
    
    # 提取引号中的内容
    quoted_text = re.findall(r'["\']([^"\']+)["\']', title + ' ' + summary)
    
    # 提取版本号
    version_pattern = re.findall(r'\b(v?\d+\.?\d*)\b', title)
    
    # 提取URL中的项目名
    url_pattern = re.findall(r'github\.com/(\S+)', summary)
    
    # 构建建议 - 完全基于提取的内容
    suggestions = []
    
    # 如果有提到具体产品/技术名称
    if capitalized_words:
        items = capitalized_words[:3]  # 最多取3个
        items_str = '、'.join(items)
        suggestions.append(f"了解文章中提到的{items_str}的具体信息，评估是否与你当前的工作或学习相关")
    
    # 如果有版本号
    if version_pattern:
        ver = version_pattern[0]
        suggestions.append(f"关注{ver}版本的新特性，对比之前版本的变化，思考是否需要升级或尝试")
    
    # 如果有GitHub链接
    if url_pattern:
        repo = url_pattern[0]
        suggestions.append(f"访问GitHub仓库({repo})查看项目详情，阅读文档了解使用方法，如有兴趣可克隆到本地测试")
    
    # 如果有引用的重要内容
    if quoted_text:
        quote = quoted_text[0][:50]
        suggestions.append(f"文章中提到「{quote}...」，深入理解这个概念或技术的含义和应用场景")
    
    # 如果没有提取到具体内容，基于文章长度和来源给出通用建议
    if not suggestions:
        if len(summary) > 200:
            suggestions.append("文章内容较丰富，点击原文链接阅读完整内容，提取对你有价值的信息点")
        else:
            suggestions.append("点击原文链接了解详细信息，评估该资讯对你当前工作或学习的参考价值")
    
    # 返回最多2条建议
    return '\\n'.join(suggestions[:2])


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
