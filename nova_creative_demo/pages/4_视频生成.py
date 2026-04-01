import streamlit as st
import os
import json
import base64
from datetime import datetime
import time
from utils.aws_bedrock import BedrockClient
from utils.aws_s3 import S3Client
from utils.aws_dynamodb import DynamoDBClient
from utils.common import display_error, display_success, display_info
import requests

# Page configuration
st.set_page_config(
    page_title="视频生成 - Nova Creative Playground",
    page_icon="🎥",
    layout="wide"
)

# Initialize clients
bedrock_client = BedrockClient(
    api_key=os.getenv("AWS_BEDROCK_API_KEY"),
    region=os.getenv("AWS_REGION", "us-east-1")
)

s3_client = S3Client(
    api_key=os.getenv("AWS_BEDROCK_API_KEY"),
    region=os.getenv("AWS_REGION", "us-east-1"),
    bucket=os.getenv("AWS_S3_BUCKET")
)

dynamodb_client = DynamoDBClient(
    api_key=os.getenv("AWS_BEDROCK_API_KEY"),
    region=os.getenv("AWS_REGION", "us-east-1"),
    table_name=os.getenv("AWS_DYNAMODB_TABLE")
)

# 初始化会话状态
if "video_tasks" not in st.session_state:
    st.session_state.video_tasks = {}

def get_creative_images():
    """
    从DynamoDB获取之前生成的创意图片列表
    """
    result = dynamodb_client.get_creatives(limit=50)
    if not result["success"]:
        st.error(f"获取创意列表失败: {result['message']}")
        return []
    return result["items"]

def check_task_status(task_id: str):
    """
    检查视频生成任务的状态
    """
    if task_id not in st.session_state.video_tasks:
        return None
    
    task = st.session_state.video_tasks[task_id]
    if task["status"] in ["COMPLETED", "FAILED"]:
        return task
    
    # 检查任务状态
    result = bedrock_client.check_video_status(task["invocation_arn"])
    
    if result["success"]:
        task["status"] = result["status"]
        if result["status"] == "COMPLETED":
            task["output_location"] = result["output_location"]
        elif result["status"] == "FAILED":
            task["error"] = result.get("error", "Unknown error")
    
    return task

def get_image_base64(presigned_url):
    try:
        # Download the image from the presigned URL
        response = requests.get(presigned_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Convert the image content to base64
        base64_image = base64.b64encode(response.content).decode('utf-8')
        return base64_image
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None


def main():
    st.title("🎥 视频生成")
    
    st.markdown("""
    在这个页面，您可以将之前生成的创意图片转换为引人注目的视频。
    选择一个创意图片，添加场景描述，我们将使用AI为您生成一个6秒的视频。
    
    注意：视频生成大约需要3-4分钟的时间。
    """)
    
    # 获取创意图片列表
    creatives = get_creative_images()
    
    if not creatives:
        st.warning("没有找到可用的创意图片。请先在创意生成页面生成一些图片。")
        return
    
    # 创建输入区域
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # 选择创意图片
        selected_creative = None
        presigned_url = None
        # print(creatives)
        creative_options = {f"{c['brand_name']} - {c['size']} - {c['timestamp'].split('.')[0]}": c for c in sorted(creatives, key=lambda x: x['timestamp'], reverse=True)}
        selected_name = st.selectbox(
            "选择创意图片",
            options=list(creative_options.keys()),
            format_func=lambda x: x
        )

        if selected_name:
            # Generate presigned url of the image url in the s3 url format.
            presigned_url = s3_client.generate_presigned_url(
                creative_options[selected_name]["image_url"]
            )
            selected_creative = creative_options[selected_name]
            st.image(presigned_url, caption=selected_name)

            background_video_prompt = creative_options[selected_name].get("background_video_prompt", """
Peaceful garden scene with gentle natural movement. Slow motion.
Early morning atmosphere with filtered sunlight in the background.""")
            mask_prompt = creative_options[selected_name].get("mask_prompt", 'product')
        
    with col2:
        # 场景描述
        st.markdown("### 场景描述")
        st.markdown("""
        描述您希望在视频中看到的场景和氛围。例如：
        - 自然光线和环境元素（晨光、薄雾等）
        - 背景氛围（平静的花园、现代办公室等）
        - 光线效果（柔和的自然光、背光等）
        """)
        
        scene_description = st.text_area(
            "场景描述",
            placeholder="例如：平静的花园场景，晨光透过树叶形成柔和的光影。背景有轻微的晨雾，营造出清新自然的氛围。",
            height=100,
            value=background_video_prompt
        )
    
    # 生成按钮
    if st.button("生成视频", type="primary", disabled=not (selected_creative and scene_description)):
        if not selected_creative or not scene_description or not presigned_url:
            st.error("请选择创意图片并填写场景描述")
        else:
            with st.spinner("正在启动视频生成任务..."):
                # 生成视频
                # Convert image from url to base64 str
                image_base64 = get_image_base64(presigned_url)
                result = bedrock_client.generate_video(
                    image_base64,
                    scene_description,
                    os.getenv("AWS_S3_BUCKET"),
                    mask_prompt
                )
                
                if result["success"]:
                    task_id = datetime.now().strftime("%Y%m%d%H%M%S")
                    st.session_state.video_tasks[task_id] = {
                        "id": task_id,
                        "invocation_arn": result["invocation_arn"],
                        "status": result["status"],
                        "creative": selected_creative,
                        "scene_description": scene_description,
                        "start_time": datetime.now().isoformat(),
                        "presigned_url": presigned_url
                    }
                    st.success("视频生成任务已启动！")
                else:
                    st.error(f"启动视频生成任务失败: {result.get('message', '未知错误')}")
    
    # 显示任务列表
    if st.session_state.video_tasks:
        st.markdown("---")
        st.subheader("视频生成任务")
        for task_id, task in st.session_state.video_tasks.items():
            with st.expander(f"任务 {task_id} - {task['creative']['brand_name']}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(task['presigned_url'], width=200)
                
                with col2:
                    st.markdown(f"**状态**: {task['status']}")
                    st.markdown(f"**开始时间**: {task['start_time']}")
                    st.markdown(f"**场景描述**: {task['scene_description']}")
                
                # 检查任务状态
                updated_task = check_task_status(task_id)
                if updated_task:
                    if updated_task["status"] == "COMPLETED":
                        st.success("视频生成完成！")
                        # 在这里添加视频播放器
                        st.video(updated_task["output_location"])
                    elif updated_task["status"] == "FAILED":
                        st.error(f"视频生成失败: {updated_task.get('error', '未知错误')}")
                    elif updated_task["status"] == "IN_PROGRESS":
                        st.info("视频正在生成中...")
                        st.progress(0.5)  # 显示进度条

if __name__ == "__main__":
    main()
