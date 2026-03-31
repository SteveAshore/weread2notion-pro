#!/usr/bin/env python3
"""
微信读书阅读时间热力图生成器
使用 SVG 生成类似 GitHub 贡献图的阅读热力图
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

from weread2notionpro.cookie_manager import CookieManager
from weread2notionpro.weread_api import WeReadApi


def generate_heatmap_svg(
    read_time_data: Dict[str, int],
    year: int = None,
    title: str = "微信读书阅读热力图",
    background_color: str = "#FFFFFF",
    track_color: str = "#ACE7AE",
    special_color1: str = "#69C16E",
    special_color2: str = "#549F57",
    dom_color: str = "#EBEDF0",
    text_color: str = "#000000"
) -> str:
    """
    生成阅读时间热力图 SVG
    
    参数:
        read_time_data: 日期到阅读分钟数的字典，格式 {"2024-01-01": 30}
        year: 年份，默认当前年
        title: 图表标题
        background_color: 背景色
        track_color: 基础颜色
        special_color1: 特殊颜色1（阅读较多）
        special_color2: 特殊颜色2（阅读很多）
        dom_color: 无阅读日期颜色
        text_color: 文本颜色
    
    返回:
        SVG 字符串
    """
    if year is None:
        year = datetime.now().year
    
    # 获取该年的所有日期
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    
    # 计算需要显示多少周
    first_weekday = start_date.weekday()
    total_days = (end_date - start_date).days + 1
    total_weeks = (total_days + first_weekday + 6) // 7
    
    # 格子大小和间距
    cell_size = 11
    cell_gap = 2
    week_width = cell_size + cell_gap
    
    # 边距
    margin_left = 30
    margin_top = 40
    margin_right = 20
    margin_bottom = 30
    
    # 计算 SVG 尺寸
    svg_width = margin_left + total_weeks * week_width + margin_right
    svg_height = margin_top + 7 * week_width + margin_bottom
    
    # 确定阅读时间的阈值
    max_minutes = max(read_time_data.values()) if read_time_data else 0
    
    def get_color(minutes: int) -> str:
        """根据阅读分钟数返回颜色"""
        if minutes == 0:
            return dom_color
        elif minutes < 30:
            return track_color
        elif minutes < 60:
            return special_color1
        else:
            return special_color2
    
    # 开始生成 SVG
    svg_parts = [
        f'<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="100%" height="100%" fill="{background_color}"/>',
        f'<text x="{margin_left}" y="25" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="{text_color}">{title} - {year}</text>',
    ]
    
    # 添加月份标签
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i, month in enumerate(months):
        # 计算该月第一周的位置
        month_date = datetime(year, i + 1, 1)
        days_from_start = (month_date - start_date).days
        week_index = (days_from_start + first_weekday) // 7
        x = margin_left + week_index * week_width
        svg_parts.append(f'<text x="{x}" y="{margin_top - 5}" font-family="Arial, sans-serif" font-size="10" fill="{text_color}">{month}</text>')
    
    # 添加星期标签
    weekdays = ["", "Mon", "", "Wed", "", "Fri", ""]
    for i, day in enumerate(weekdays):
        if day:
            y = margin_top + i * week_width + cell_size
            svg_parts.append(f'<text x="5" y="{y}" font-family="Arial, sans-serif" font-size="9" fill="{text_color}">{day}</text>')
    
    # 生成日期格子
    current_date = start_date
    day_index = 0
    
    while current_date <= end_date:
        # 计算格子位置
        week = (day_index + first_weekday) // 7
        weekday = (day_index + first_weekday) % 7
        
        x = margin_left + week * week_width
        y = margin_top + weekday * week_width
        
        # 获取该日期的阅读时间
        date_str = current_date.strftime("%Y-%m-%d")
        minutes = read_time_data.get(date_str, 0)
        color = get_color(minutes)
        
        # 添加格子
        tooltip = f"{date_str}: {minutes} 分钟"
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}" rx="2" ry="2">')
        svg_parts.append(f'<title>{tooltip}</title>')
        svg_parts.append('</rect>')
        
        current_date += timedelta(days=1)
        day_index += 1
    
    # 添加图例
    legend_x = margin_left
    legend_y = svg_height - 20
    svg_parts.append(f'<text x="{legend_x}" y="{legend_y}" font-family="Arial, sans-serif" font-size="10" fill="{text_color}">Less</text>')
    
    legend_items = [
        (dom_color, "0 min"),
        (track_color, "<30 min"),
        (special_color1, "30-60 min"),
        (special_color2, ">60 min")
    ]
    
    for i, (color, label) in enumerate(legend_items):
        x = legend_x + 35 + i * 45
        svg_parts.append(f'<rect x="{x}" y="{legend_y - 9}" width="{cell_size}" height="{cell_size}" fill="{color}" rx="2" ry="2"/>')
        svg_parts.append(f'<text x="{x + 15}" y="{legend_y}" font-family="Arial, sans-serif" font-size="9" fill="{text_color}">{label}</text>')
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def generate_weread_heatmap(
    year: int = None,
    output_path: str = "OUT_FOLDER/weread.svg",
    **kwargs
) -> bool:
    """
    生成微信读书阅读热力图
    
    参数:
        year: 年份，默认当前年
        output_path: 输出文件路径
        **kwargs: 颜色配置参数
    
    返回:
        是否成功
    """
    try:
        if year is None:
            year = datetime.now().year
        
        print(f"正在生成 {year} 年的阅读热力图...")
        
        # 获取 Cookie
        manager = CookieManager()
        cookies = manager.get_cookies()
        if not cookies or not manager.is_valid:
            print("❌ Cookie 无效，无法获取阅读时间数据")
            return False
        
        # 使用 WeReadApi 获取阅读时间数据
        api = WeReadApi()
        
        # 从 API 获取阅读时间历史数据
        try:
            read_time_data = api.get_read_time_history(year)
            if not read_time_data:
                print(f"未获取到 {year} 年的阅读时间数据，将生成空热力图")
                # 生成空数据
                read_time_data = {}
        except Exception as e:
            print(f"获取阅读时间数据失败: {e}，将生成空热力图")
            read_time_data = {}
        
        # 生成 SVG
        svg_content = generate_heatmap_svg(
            read_time_data,
            year=year,
            title=kwargs.get("title", "微信读书阅读热力图"),
            background_color=kwargs.get("background_color", "#FFFFFF"),
            track_color=kwargs.get("track_color", "#ACE7AE"),
            special_color1=kwargs.get("special_color1", "#69C16E"),
            special_color2=kwargs.get("special_color2", "#549F57"),
            dom_color=kwargs.get("dom_color", "#EBEDF0"),
            text_color=kwargs.get("text_color", "#000000")
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存 SVG 文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        
        print(f"✅ 热力图已生成: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ 生成热力图失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 命令行入口
    import argparse
    
    parser = argparse.ArgumentParser(description="生成微信读书阅读热力图")
    parser.add_argument("--year", type=int, default=None, help="年份")
    parser.add_argument("--output", type=str, default="OUT_FOLDER/weread.svg", help="输出文件路径")
    parser.add_argument("--title", type=str, default="微信读书阅读热力图", help="图表标题")
    parser.add_argument("--background-color", type=str, default="#FFFFFF", help="背景色")
    parser.add_argument("--track-color", type=str, default="#ACE7AE", help="基础颜色")
    parser.add_argument("--special-color1", type=str, default="#69C16E", help="特殊颜色1")
    parser.add_argument("--special-color2", type=str, default="#549F57", help="特殊颜色2")
    parser.add_argument("--dom-color", type=str, default="#EBEDF0", help="无阅读颜色")
    parser.add_argument("--text-color", type=str, default="#000000", help="文本颜色")
    
    args = parser.parse_args()
    
    success = generate_weread_heatmap(
        year=args.year,
        output_path=args.output,
        title=args.title,
        background_color=args.background_color,
        track_color=args.track_color,
        special_color1=args.special_color1,
        special_color2=args.special_color2,
        dom_color=args.dom_color,
        text_color=args.text_color
    )
    
    sys.exit(0 if success else 1)
