import streamlit as st
import os
import json
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import io

def init_session_state():
    """
    初始化Streamlit会话状态
    """
    # 创意生成模块
    if "generated_creatives" not in st.session_state:
        st.session_state.generated_creatives = []
    
    # 优化洞察模块
    if "campaign_data" not in st.session_state:
        st.session_state.campaign_data = None
    
    if "optimization_insights" not in st.session_state:
        st.session_state.optimization_insights = []
    
    # 配置模块
    if "config" not in st.session_state:
        # 默认配置
        st.session_state.config = {
            "aws": {
                "bedrock_api_key": os.getenv("AWS_BEDROCK_API_KEY", ""),
                "region": os.getenv("AWS_REGION", "us-east-1"),
                "s3_bucket": os.getenv("AWS_S3_BUCKET", ""),
                "dynamodb_table": os.getenv("AWS_DYNAMODB_TABLE", "google-ads-assistant")
            },
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "model": os.getenv("DEEPSEEK_MODEL", "deepseek-r1")
            },
            "app": {
                "theme": "light",
                "language": "zh",
                "max_history_items": 10
            }
        }

def load_sample_data() -> pd.DataFrame:
    """
    加载示例广告活动数据
    
    Returns:
        包含示例数据的DataFrame
    """
    sample_data = {
        "Campaign": ["夏季促销", "新品发布", "品牌推广"],
        "Impressions": [15000, 8500, 12000],
        "Clicks": [450, 320, 280],
        "CTR": [0.03, 0.0376, 0.0233],
        "CPC": [2.5, 3.2, 1.8],
        "Conversions": [25, 18, 12],
        "Cost": [1125, 1024, 504],
        "ROAS": [3.2, 2.8, 4.1]
    }
    return pd.DataFrame(sample_data)

def parse_csv_upload(uploaded_file) -> Dict[str, Any]:
    """
    解析上传的CSV文件
    
    Args:
        uploaded_file: 上传的文件对象
    
    Returns:
        包含解析状态和数据的字典
    """
    try:
        # 读取CSV文件
        data = pd.read_csv(uploaded_file)
        return {
            "success": True,
            "message": "文件解析成功",
            "data": data
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"文件解析失败: {str(e)}",
            "data": None
        }

def format_timestamp(timestamp: str) -> str:
    """
    格式化ISO时间戳为友好的显示格式
    
    Args:
        timestamp: ISO格式的时间戳
    
    Returns:
        格式化后的时间字符串
    """
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

def get_image_download_link(image_url: str, file_name: str) -> str:
    """
    生成图像下载链接
    
    Args:
        image_url: 图像URL
        file_name: 下载文件名
    
    Returns:
        HTML下载链接
    """
    # 注意：这个函数在实际实现中需要处理图像数据
    # 目前返回一个模拟的下载链接
    return f'<a href="{image_url}" download="{file_name}">下载图像</a>'

def export_insights_to_csv(insights: List[Dict[str, Any]]) -> str:
    """
    将优化洞察导出为CSV
    
    Args:
        insights: 优化洞察列表
    
    Returns:
        CSV数据的Base64编码字符串
    """
    # 创建一个扁平化的数据结构
    rows = []
    for insight_result in insights:
        for insight in insight_result.get("insights", []):
            rows.append({
                "时间戳": format_timestamp(insight_result.get("timestamp", "")),
                "指标": ", ".join(insight_result.get("metrics_analyzed", [])),
                "标题": insight.get("title", ""),
                "描述": insight.get("description", ""),
                "优先级": insight.get("priority", ""),
                "建议操作": insight.get("action", ""),
                "状态": insight.get("status", "")
            })
    
    # 创建DataFrame
    df = pd.DataFrame(rows)
    
    # 转换为CSV
    csv = df.to_csv(index=False)
    
    # Base64编码
    b64 = base64.b64encode(csv.encode()).decode()
    
    return b64

def display_error(message: str):
    """
    显示错误消息
    
    Args:
        message: 错误消息
    """
    st.error(message)

def display_success(message: str):
    """
    显示成功消息
    
    Args:
        message: 成功消息
    """
    st.success(message)

def display_info(message: str):
    """
    显示信息消息
    
    Args:
        message: 信息消息
    """
    st.info(message)

def display_warning(message: str):
    """
    显示警告消息
    
    Args:
        message: 警告消息
    """
    st.warning(message)
