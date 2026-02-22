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

# 财富认知知识库
WEALTH_KNOWLEDGE = [
    {
        "book": "《百万富翁快车道》",
        "knowledge": "财富不是靠省钱积累的，而是通过创造价值获得的。真正的财富来自于建立能够产生被动收入的系统，而不是出卖时间换取金钱。"
    },
    {
        "book": "《百万富翁快车道》",
        "knowledge": "时间是你最宝贵的资产。富人用金钱购买时间，穷人用时间换取金钱。要学会将时间投资在能够产生复利效应的事情上。"
    },
    {
        "book": "《定投改变命运》",
        "knowledge": "定投的核心不是择时，而是纪律。长期坚持定投优质资产，利用时间的复利效应，普通人也能实现财富自由。"
    },
    {
        "book": "《定投改变命运》",
        "knowledge": "投资最重要的是认知升级。你永远赚不到超出你认知范围之外的钱，除非靠运气，但靠运气赚到的钱最终会凭实力亏掉。"
    },
    {
        "book": "《有钱人和你想的不一样》",
        "knowledge": "富人关注机会，穷人关注障碍。当面对挑战时，富人问'我怎样才能做到'，穷人说'我做不到'。思维方式决定财富结果。"
    },
    {
        "book": "《有钱人和你想的不一样》",
        "knowledge": "富人让钱为他们努力工作，穷人努力工作赚钱。要学会建立资产，让资产产生现金流，而不是一直靠劳动换取收入。"
    },
    {
        "book": "《财富自由之路》",
        "knowledge": "注意力是你最宝贵的财富。把注意力放在成长上，而不是抱怨上；放在解决方案上，而不是问题上；放在未来上，而不是过去上。"
    },
    {
        "book": "《财富自由之路》",
        "knowledge": "所谓财富自由，就是被动收入大于日常开支。实现财富自由的关键是提升个人商业价值，建立可持续的收入来源。"
    },
    {
        "book": "《邻家的百万富翁》",
        "knowledge": "真正的富人往往生活简朴，他们不会为了炫耀而消费。他们把钱投资在能够增值的资产上，而不是贬值的消费品上。"
    },
    {
        "book": "《邻家的百万富翁》",
        "knowledge": "积累财富的公式：收入 - 支出 = 储蓄，储蓄 × 投资回报率 = 财富。控制支出、提高储蓄率、学会投资，是积累财富的三大支柱。"
    },
    {
        "book": "《纳瓦尔宝典》",
        "knowledge": "致富需要杠杆。商业杠杆来自资本、人力和边际成本为零的产品（代码和媒体）。学会利用杠杆，才能实现财富的指数级增长。"
    },
    {
        "book": "《纳瓦尔宝典》",
        "knowledge": "要想获得财富，你必须拥有股权。打工只能获得线性收入，拥有股权才能获得指数级回报。要么创业，要么加入早期公司获得股权。"
    },
    {
        "book": "《小狗钱钱》",
        "knowledge": "每天写下你的梦想清单，明确你想要的生活。把大目标分解成小步骤，每天进步一点点，坚持下去就能实现财务目标。"
    },
    {
        "book": "《小狗钱钱》",
        "knowledge": "建立你的'梦想储蓄罐'，把收入的至少10%存起来用于投资。先支付自己，再支付别人，这是积累财富的第一步。"
    },
    {
        "book": "《富爸爸穷爸爸》",
        "knowledge": "资产是能把钱放进你口袋的东西，负债是把钱从你口袋取走的东西。富人买入资产，穷人买入负债，中产阶级买入自以为是资产的负债。"
    },
    {
        "book": "《富爸爸穷爸爸》",
        "knowledge": "财商教育比学历教育更重要。学校教你如何为钱工作，财商教育教你如何让钱为你工作。要不断学习投资、税务、法律和会计知识。"
    },
    {
        "book": "《百万富翁快车道》",
        "knowledge": "不要追求工作与生活的平衡，而要追求工作与生活的整合。当你热爱你的工作，工作就是生活的一部分，而不是负担。"
    },
    {
        "book": "《纳瓦尔宝典》",
        "knowledge": "学会销售，学会构建产品。如果你两者都会，你将势不可挡。技术能力让你创造价值，销售能力让你传递价值。"
    },
    {
        "book": "《财富自由之路》",
        "knowledge": "升级你的操作系统（思维方式）比升级你的应用程序（技能）更重要。改变思维方式，才能从根本上改变行为模式和结果。"
    },
    {
        "book": "《有钱人和你想的不一样》",
        "knowledge": "富人选择根据结果获得报酬，穷人选择根据时间获得报酬。要勇于承担风险，追求与成果挂钩的收入方式。"
    }
]

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


def generate_chinese_summary(news_item):
    """
    生成中文一句话概括
    提取文章核心要素，用简洁的中文表达
    """
    title = news_item['title']
    summary = news_item['summary']
    text = (title + ' ' + summary).lower()
    
    # 提取主体（公司/产品）
    who = ""
    companies = {
        'openai': 'OpenAI', 'google': '谷歌', 'microsoft': '微软',
        'meta': 'Meta', 'anthropic': 'Anthropic', 'deepmind': 'DeepMind',
        'amazon': '亚马逊', 'apple': '苹果', 'nvidia': '英伟达',
        '百度': '百度', '阿里': '阿里巴巴', '腾讯': '腾讯', '字节跳动': '字节跳动'
    }
    for key, name in companies.items():
        if key in text:
            who = name
            break
    
    # 如果没有识别到公司，识别产品
    if not who:
        products = {
            'gpt-4': 'GPT-4', 'gpt-5': 'GPT-5', 'chatgpt': 'ChatGPT',
            'claude': 'Claude', 'gemini': 'Gemini', 'llama': 'Llama',
            'copilot': 'Copilot', 'cursor': 'Cursor',
            'midjourney': 'Midjourney', 'stable diffusion': 'Stable Diffusion',
            'sora': 'Sora', 'dall-e': 'DALL-E'
        }
        for key, name in products.items():
            if key in text:
                who = name
                break
    
    # 识别核心事件
    event = ""
    if any(w in text for w in ['announces', 'announced', '宣布']):
        event = "宣布"
    elif any(w in text for w in ['launches', 'launched', '推出']):
        event = "推出"
    elif any(w in text for w in ['releases', 'released', '发布']):
        event = "发布"
    elif any(w in text for w in ['open source', '开源']):
        event = "开源"
    elif any(w in text for w in ['acquires', 'acquired', '收购']):
        event = "收购"
    elif any(w in text for w in ['raises', 'raised', '融资']):
        event = "获得融资"
    elif any(w in text for w in ['partnership', 'partners', '合作']):
        event = "达成合作"
    elif any(w in text for w in ['update', 'updates', '更新']):
        event = "更新"
    
    # 识别内容
    content = ""
    if any(w in text for w in ['new model', '模型', 'model']):
        content = "新模型"
    elif any(w in text for w in ['new feature', '功能', 'feature']):
        content = "新功能"
    elif any(w in text for w in ['new product', '产品', 'product']):
        content = "新产品"
    elif any(w in text for w in ['api']):
        content = "API"
    elif any(w in text for w in ['tool', '工具']):
        content = "工具"
    elif any(w in text for w in ['platform', '平台']):
        content = "平台"
    elif any(w in text for w in ['framework', '框架']):
        content = "框架"
    elif any(w in text for w in ['paper', '论文', 'research', '研究']):
        content = "研究成果"
    elif any(w in text for w in ['dataset', '数据集']):
        content = "数据集"
    
    # 识别关键特性
    feature = ""
    if any(w in text for w in ['multimodal', '多模态', 'image', 'video', '图像', '视频']):
        feature = "支持多模态"
    elif any(w in text for w in ['faster', 'speed', '更快', '速度']):
        feature = "速度更快"
    elif any(w in text for w in ['improved', 'better', '提升', '改进']):
        feature = "性能提升"
    elif any(w in text for w in ['free', '免费']):
        feature = "免费开放"
    elif any(w in text for w in ['open source', '开源']):
        feature = "开源"
    
    # 组合成一句话中文概括
    result_parts = []
    if who:
        result_parts.append(who)
    if event:
        result_parts.append(event)
    if content:
        result_parts.append(content)
    
    # 如果有特性，用逗号连接
    if feature and len(result_parts) >= 2:
        result = ''.join(result_parts) + "，" + feature
    elif len(result_parts) >= 2:
        result = ''.join(result_parts)
    elif len(result_parts) == 1:
        result = result_parts[0] + "有新动态"
    else:
        # 无法提取时，返回简化版标题
        result = title[:60] if len(title) <= 60 else title[:60] + "..."
    
    return result


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
    return generate_actionable_insight(news_item)


def get_daily_wealth_knowledge():
    """
    获取每日财富认知小知识
    基于日期选择，确保每天不同
    """
    import random
    # 使用日期作为种子，确保每天相同
    today = datetime.now().strftime('%Y-%m-%d')
    random.seed(today)
    # 随机选择一条知识
    knowledge = random.choice(WEALTH_KNOWLEDGE)
    return knowledge


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
    
    # 获取今日财富知识
    wealth_knowledge = get_daily_wealth_knowledge()
    
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
            .reminder {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 25px; text-align: center; font-size: 16px; font-weight: bold; border: 3px solid #ff4757; box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3); }}
            .reminder-text {{ font-size: 18px; line-height: 1.6; }}
            .wealth-section {{ background: linear-gradient(135deg, #f1c40f 0%, #f39c12 100%); padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 5px solid #e67e22; }}
            .wealth-title {{ font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
            .wealth-content {{ color: #2c3e50; line-height: 1.6; font-size: 14px; }}
            .wealth-source {{ color: #7f8c8d; font-size: 12px; margin-top: 8px; font-style: italic; }}
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
            
            <!-- 每日提醒 -->
            <div class="reminder">
                <div class="reminder-text">
                    📢 每天安排好自己的计划了吗？背单词/课内学业/经典阅读/IP表达/LPT课程/... 不要忘记了！
                </div>
            </div>
            
            <!-- 每日财富认知 -->
            <div class="wealth-section">
                <div class="wealth-title">💰 每日财富认知提升</div>
                <div class="wealth-content">{wealth_knowledge['knowledge']}</div>
                <div class="wealth-source">—— {wealth_knowledge['book']}</div>
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
