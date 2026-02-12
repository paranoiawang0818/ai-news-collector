# -*- coding: utf-8 -*-
"""
本地测试脚本 - 用于验证系统功能
不会真正发送邮件，只会生成HTML预览文件
"""

import sys
import os

# 设置测试环境变量
os.environ['SENDER_EMAIL'] = 'test@qq.com'
os.environ['SENDER_PASSWORD'] = 'test_password'
os.environ['RECEIVER_EMAIL'] = 'paranoiawang0818@qq.com'

# 导入主脚本
from ai_news_collector import *

def test_rss_fetch():
    """测试RSS采集功能"""
    print("\n" + "="*60)
    print("🧪 测试1：RSS源采集")
    print("="*60)
    
    test_feeds = {
        '机器之心': 'https://rsshub.app/jiqizhixin/recommends',
        'Hacker News': 'https://hnrss.org/newest?q=AI',
    }
    
    all_news = []
    for source, url in test_feeds.items():
        print(f"\n📡 测试源：{source}")
        news = fetch_rss_news(url, source, hours=48)  # 扩大到48小时
        print(f"   ✓ 获取 {len(news)} 条资讯")
        all_news.extend(news)
    
    return all_news

def test_importance_analysis(news_list):
    """测试重要性分析"""
    print("\n" + "="*60)
    print("🧪 测试2：重要性分析")
    print("="*60)
    
    for news in news_list[:5]:
        score = analyze_importance(news)
        print(f"\n标题：{news['title'][:50]}...")
        print(f"来源：{news['source']}")
        print(f"重要性得分：{score}")

def test_html_generation(news_list):
    """测试HTML生成"""
    print("\n" + "="*60)
    print("🧪 测试3：HTML邮件生成")
    print("="*60)
    
    if not news_list:
        print("⚠️ 没有资讯数据，使用模拟数据")
        news_list = [{
            'source': '测试源',
            'title': 'OpenAI发布GPT-5：性能提升10倍',
            'link': 'https://example.com',
            'summary': '这是一条测试资讯的摘要内容，用于验证HTML生成功能是否正常工作。',
            'pub_time': datetime.now(),
            'importance': 9
        }]
    
    html = format_news_html(news_list)
    
    # 保存HTML文件
    output_file = 'test_email_preview.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML已生成：{output_file}")
    print(f"📊 资讯数量：{len(news_list)} 条")
    
    # 尝试在浏览器中打开
    try:
        import webbrowser
        abs_path = os.path.abspath(output_file)
        webbrowser.open('file://' + abs_path)
        print(f"🌐 已在浏览器中打开预览")
    except:
        print(f"💡 请手动打开文件查看：{output_file}")

def main():
    """主测试流程"""
    print("="*60)
    print("🚀 AI资讯系统 - 本地测试模式")
    print("="*60)
    
    # 测试1：RSS采集
    news_list = test_rss_fetch()
    
    if not news_list:
        print("\n⚠️ 未获取到资讯，可能是网络问题或RSS源失效")
        print("💡 将使用模拟数据继续测试...")
    
    # 测试2：重要性分析
    if news_list:
        test_importance_analysis(news_list)
    
    # 测试3：HTML生成
    test_html_generation(news_list)
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)
    print("\n📝 注意事项：")
    print("1. 本测试不会发送真实邮件")
    print("2. 已生成HTML预览文件供查看")
    print("3. 如需测试邮件发送，请配置真实的邮箱信息")
    print("\n💡 下一步：")
    print("1. 检查生成的HTML文件")
    print("2. 配置GitHub Secrets")
    print("3. 推送代码到GitHub")
    print("4. 在GitHub Actions中手动触发测试")

if __name__ == "__main__":
    main()
