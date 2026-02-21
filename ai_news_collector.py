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


def generate_chinese_summary(news_item):
    """
    基于文章内容生成中文精准概括
    处理英文RSS源内容，提取核心信息并翻译为自然中文
    """
    title = news_item['title']
    summary = news_item['summary']
    text_lower = (title + ' ' + summary).lower()
    
    # 识别主体（公司/机构/产品）- 优先匹配
    who = ""
    companies = {
        'openai': 'OpenAI', 'google': 'Google', 'microsoft': 'Microsoft', 
        'meta': 'Meta', 'anthropic': 'Anthropic', 'deepmind': 'DeepMind',
        'amazon': 'Amazon', 'apple': 'Apple', 'nvidia': 'NVIDIA',
        '百度': '百度', '阿里': '阿里巴巴', '腾讯': '腾讯', '字节跳动': '字节跳动',
        '华为': '华为', '小米': '小米'
    }
    for key, name in companies.items():
        if key in text_lower:
            who = name
            break
    
    # 识别产品名
    if not who:
        products = {
            'gpt-5': 'GPT-5', 'gpt-4': 'GPT-4', 'gpt-3': 'GPT-3', 'chatgpt': 'ChatGPT',
            'claude': 'Claude', 'gemini': 'Gemini', 'llama': 'Llama', 'mistral': 'Mistral',
            'copilot': 'Copilot', 'midjourney': 'Midjourney', 'stable diffusion': 'Stable Diffusion',
            'sora': 'Sora', 'dall-e': 'DALL-E', 'runway': 'Runway'
        }
        for key, name in products.items():
            if key in text_lower:
                who = name
                break
    
    # 识别核心动作/事件（中英双语）
    action_keywords = {
        # 发布类
        'releases': '发布', 'launches': '推出', 'announces': '宣布', 'introduces': '推出',
        '发布': '发布', '推出': '推出', '宣布': '宣布',
        # 开源类
        'open source': '开源', 'open sources': '开源', '开源': '开源',
        # 融资类
        'raises': '获得', 'funding': '融资', '融资': '融资', 'investment': '投资',
        # 收购类
        'acquires': '收购', 'acquisition': '收购', '收购': '收购',
        # 合作类
        'partners': '与', 'partnership': '合作', 'collaborates': '合作', '合作': '合作',
        # 突破类
        'breakthrough': '实现突破', 'achieves': '实现', '突破': '实现突破',
        # 升级类
        'upgrades': '升级', 'updates': '更新', '升级': '升级', '更新': '更新',
        # 支持类
        'supports': '支持', 'enables': '支持', '支持': '支持'
    }
    
    what = ""
    for en_action, cn_action in action_keywords.items():
        if en_action in text_lower:
            what = cn_action
            break
    
    # 识别对象/内容
    obj = ""
    if any(word in text_lower for word in ['new model', '新模型', 'model', '模型']):
        obj = "新模型"
    elif any(word in text_lower for word in ['new feature', '新功能', 'feature', '功能']):
        obj = "新功能"
    elif any(word in text_lower for word in ['new product', '新产品', 'product', '产品']):
        obj = "新产品"
    elif any(word in text_lower for word in ['api', '接口']):
        obj = "API接口"
    elif any(word in text_lower for word in ['tool', '工具']):
        obj = "工具"
    elif any(word in text_lower for word in ['platform', '平台']):
        obj = "平台"
    elif any(word in text_lower for word in ['research', 'paper', '论文', '研究']):
        obj = "研究成果"
    elif any(word in text_lower for word in ['framework', '框架']):
        obj = "框架"
    
    # 识别价值/影响
    impact = ""
    if any(word in text_lower for word in ['improve', '提升', 'better', '更好']):
        impact = "性能提升"
    elif any(word in text_lower for word in ['faster', '更快', 'speed', '速度']):
        impact = "速度更快"
    elif any(word in text_lower for word in ['cheaper', '更便宜', 'cost', '成本']):
        impact = "成本降低"
    elif any(word in text_lower for word in ['free', '免费']):
        impact = "免费开放"
    elif any(word in text_lower for word in ['multimodal', '多模态']):
        impact = "支持多模态"
    
    # 组合生成中文概括
    if who and what:
        # 有主体和动作
        if '开源' in what:
            return f"{who} 开源{obj if obj else '项目/技术'}，开发者可免费使用"
        elif what in ['获得', '融资']:
            return f"{who} 获得{obj if obj else '新一轮'}融资，加速AI业务发展"
        elif what in ['收购']:
            return f"{who} 收购{obj if obj else '相关公司'}，拓展业务版图"
        elif what in ['合作', '与']:
            return f"{who} {what}合作伙伴{obj if obj else ''}，强强联合"
        elif what in ['发布', '推出', '宣布']:
            if obj:
                return f"{who} {what}{obj}{'，' + impact if impact else ''}"
            else:
                return f"{who} {what}重要更新，{impact if impact else '值得关注'}"
        elif what in ['升级', '更新']:
            return f"{who} {what}{obj if obj else '产品'}{'，' + impact if impact else ''}"
        elif what in ['实现突破']:
            return f"{who} {what}{obj if obj else ''}，推动AI技术进步"
        else:
            return f"{who} {what}{obj if obj else '新动态'}，{impact if impact else '值得关注'}"
    else:
        # 无法提取完整信息，基于内容类型生成
        if any(word in text_lower for word in ['paper', 'research', 'arxiv', '论文', '研究']):
            if who:
                return f"{who} 发布最新研究成果，提出创新方法"
            return "最新AI研究论文发布，提出新方法或取得突破"
        elif any(word in text_lower for word in ['regulation', 'policy', '监管', '政策', '法律']):
            return "AI监管政策更新，影响行业合规与发展方向"
        elif any(word in text_lower for word in ['funding', 'investment', '融资', '投资']):
            return "AI领域投融资动态，反映资本市场热点趋势"
        elif any(word in text_lower for word in ['open source', 'github', '开源']):
            return "开源AI项目发布，开发者可免费使用和贡献"
        elif any(word in text_lower for word in ['agent', 'autonomous', '智能体']):
            return "AI Agent技术新进展，推动自动化应用发展"
        elif any(word in text_lower for word in ['multimodal', 'image', 'video', '多模态', '图像', '视频']):
            return "多模态AI技术更新，拓展应用场景边界"
        elif any(word in text_lower for word in ['code', 'coding', 'programming', '编程']):
            return "AI编程工具更新，提升开发效率"
        else:
            # 提取核心内容，翻译为中文风格
            # 清理并简化摘要
            clean_summary = summary[:100] if len(summary) > 100 else summary
            # 如果是纯英文，返回一个通用的中文描述
            if who:
                return f"{who} 发布重要动态，涉及{obj if obj else 'AI技术'}领域"
            else:
                return f"AI领域新动态：{clean_summary[:60]}{'...' if len(clean_summary) > 60 else ''}"


def generate_contextual_insight(news_item):
    """
    基于文章具体内容生成个性化启示，完全结合文章内容
    """
    title = news_item['title']
    summary = news_item['summary']
    source = news_item['source']
    text = (title + ' ' + summary).lower()
    
    insights = []
    
    # 根据具体内容生成针对性建议
    
    # 1. 如果是新模型发布
    if any(word in text for word in ['gpt-4', 'gpt-5', 'claude 3', 'claude 4', 'gemini', 'llama 3', '新模型', 'new model']):
        model_name = ""
        if 'gpt-4' in text:
            model_name = "GPT-4"
        elif 'gpt-5' in text:
            model_name = "GPT-5"
        elif 'claude' in text:
            model_name = "Claude"
        elif 'gemini' in text:
            model_name = "Gemini"
        elif 'llama' in text:
            model_name = "Llama"
        
        if model_name:
            insights.append(f"【立即行动】访问官网申请{model_name}的API权限或试用资格，在你的实际业务场景中测试3-5个具体用例，对比现有方案在准确率、响应速度、成本三个维度的差异，记录测试结果作为是否切换的依据")
    
    # 2. 如果是开源项目
    if any(word in text for word in ['开源', 'open source', 'github', 'huggingface', '发布代码']):
        insights.append(f"【本周任务】点击原文链接进入项目主页，查看README文档了解项目功能，Fork代码到本地环境运行示例，评估该工具是否能解决你当前工作中的具体问题（如数据处理、模型训练、自动化等），如适用则集成到工作流")
    
    # 3. 如果是融资新闻
    if any(word in text for word in ['融资', 'funding', 'investment', '估值', 'billion', 'million']):
        company = ""
        amount = ""
        
        # 尝试提取公司名和金额
        import re
        amount_match = re.search(r'(\d+)\s*(million|billion|亿|百万|千万|十亿)', text)
        if amount_match:
            amount = amount_match.group(0)
        
        insights.append(f"【深度分析】研究这家公司的核心技术方向和产品形态，分析其解决的具体痛点；查看投资方名单（如红杉、A16Z等顶级机构投资说明赛道被看好），思考这个细分领域是否值得你投入时间学习或创业")
    
    # 4. 如果是监管政策
    if any(word in text for word in ['监管', 'regulation', 'policy', '合规', '法律', '法案', '欧盟', '美国']):
        region = ""
        if '欧盟' in text or 'european' in text or 'eu ' in text:
            region = "欧盟"
        elif '美国' in text or 'us ' in text or 'american' in text:
            region = "美国"
        elif '中国' in text or 'china' in text:
            region = "中国"
        
        if region:
            insights.append(f"【合规检查】{region}的新政策可能影响你的AI产品，立即检查：1）用户数据处理是否符合要求；2）模型训练数据是否有版权风险；3）是否需要增加用户告知和同意机制；4）如涉及跨境服务，评估是否需要调整业务模式")
        else:
            insights.append(f"【合规检查】新的监管政策可能影响你的AI产品，立即检查数据隐私、版权合规、用户告知等关键环节，必要时咨询专业法务")
    
    # 5. 如果是AI Agent相关
    if any(word in text for word in ['agent', '智能体', 'autonomous', 'auto-gpt', 'workflow自动化']):
        insights.append(f"【实践建议】列出你每周重复做的3-5项工作（如数据整理、邮件回复、报告生成、信息搜集），选择其中一项用AI Agent工具（如Dify、Coze、LangChain）搭建自动化流程，本周内完成第一个Agent的搭建和测试")
    
    # 6. 如果是编程开发工具
    if any(word in text for word in ['coding', '编程', 'code generation', 'developer', '程序员', 'ide', 'copilot', 'cursor']):
        insights.append(f"【效率提升】如果你还在手动写代码，立即下载安装Cursor或GitHub Copilot，在本周的编码工作中全程使用AI辅助，重点关注：1）代码补全准确率；2）Bug检测能力；3）重构建议质量；4）整体开发效率提升比例，记录对比数据")
    
    # 7. 如果是多模态/图像视频
    if any(word in text for word in ['multimodal', '多模态', 'image generation', 'video', 'audio', '图像生成', '视频生成', 'sora', 'midjourney', 'runway']):
        tool_name = ""
        if 'midjourney' in text:
            tool_name = "Midjourney"
        elif 'sora' in text:
            tool_name = "Sora"
        elif 'runway' in text:
            tool_name = "Runway"
        elif 'dall-e' in text or 'dalle' in text:
            tool_name = "DALL-E"
        
        if tool_name:
            insights.append(f"【创意实践】注册{tool_name}账号，本周用它完成一个实际任务：如为公众号/小红书生成3张配图、制作一个15秒的产品宣传视频、或设计一套品牌视觉素材，对比传统方式和AI生成在成本、时间、质量上的差异")
        else:
            insights.append(f"【创意实践】探索多模态AI在你工作中的应用场景：营销素材生成、产品演示视频、社交媒体配图等，选择一款工具（Midjourney/Runway/即梦）完成一个实际项目")
    
    # 8. 如果是RAG/知识库
    if any(word in text for word in ['rag', 'retrieval', 'knowledge base', '向量数据库', 'embedding', '知识库', '检索增强']):
        insights.append(f"【知识管理】整理你电脑中散落的文档（PDF、Word、笔记），选择一款工具（如AnythingLLM、FastGPT、Dify）搭建个人/团队知识库，上传10-20份核心文档，测试问答功能，评估是否能提升信息检索效率")
    
    # 9. 如果是学术论文
    if any(word in text for word in ['paper', '论文', 'research', 'arxiv', 'neurips', 'icml', 'iclr', 'cvpr']):
        insights.append(f"【学习路径】点击原文链接找到论文PDF，先读摘要和结论了解核心贡献，再看实验结果是否惊艳，如感兴趣则深入方法部分；检查论文是否开源代码，如有则在本地复现关键实验，理解技术原理")
    
    # 10. 如果是产品功能更新
    if any(word in text for word in ['feature', '功能', 'product', '产品', 'update', '更新']):
        insights.append(f"【体验反馈】立即注册/登录体验这个新功能，思考：1）它解决了什么痛点；2）交互设计是否流畅；3）与竞品相比优劣；4）是否值得你在工作中采用；5）对你的产品有何借鉴意义，记录体验报告")
    
    # 11. 如果是行业报告/趋势
    if any(word in text for word in ['report', '报告', 'trend', '趋势', 'market', '市场', 'survey', '调研']):
        insights.append(f"【战略参考】下载完整报告阅读关键章节（市场规模、增长预测、竞争格局、用户画像），提取3-5个关键数据点，思考这些数据对你的职业规划、产品方向、投资决策有何指导意义，形成一页纸的洞察总结")
    
    # 12. 如果是API/开发者工具
    if any(word in text for word in ['api', 'sdk', 'developer', '开发者', '接口', 'integration']):
        insights.append(f"【技术评估】查看API文档了解功能覆盖范围和定价策略，申请API Key在你的测试环境调用，评估：1）功能是否满足需求；2）稳定性和延迟表现；3）成本是否在预算内；4）集成难度，形成技术选型评估报告")
    
    # 如果没有匹配到特定类型，生成通用建议
    if not insights:
        # 基于摘要内容生成建议
        if len(summary) > 50:
            core_topic = summary[:60]
            insights.append(f"【深度了解】点击原文阅读完整内容，理解{core_topic}...的核心要点，思考这与你的专业领域或工作有何关联，是否需要进一步学习或调整方向")
        else:
            insights.append(f"【深度了解】点击原文阅读完整内容，提取核心观点和技术要点，评估对你当前工作的参考价值，如需深入了解可搜索相关技术文档或教程")
    
    # 返回最相关的建议（最多2条）
    return '\\n\\n'.join(insights[:2])


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
