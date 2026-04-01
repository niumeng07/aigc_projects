import streamlit as st
import os
import json
import base64
from datetime import datetime
import uuid
from io import BytesIO
from PIL import Image
from utils.aws_bedrock import BedrockClient
from utils.aws_s3 import S3Client
from utils.aws_dynamodb import DynamoDBClient
from utils.common import format_timestamp, get_image_download_link, display_error, display_success, display_info

# Page configuration
st.set_page_config(
    page_title="创意生成 - Nova Creative Playground",
    page_icon="🎨",
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
    table_name=os.getenv("AWS_DYNAMODB_TABLE", "google-ads-assistant")
)

def process_uploaded_image(uploaded_file):
    """
    处理上传的图像文件
    
    Args:
        uploaded_file: 上传的图像文件
    
    Returns:
        处理后的图像数据（Base64编码）
    """
    try:
        if uploaded_file is None:
            return None
        
        # 读取图像文件
        image_bytes = uploaded_file.getvalue()
        
        # 使用PIL打开图像进行处理
        image = Image.open(BytesIO(image_bytes))
        
        # 调整图像大小（如果需要）
        max_size = (1024, 1024)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # 转换为Base64编码
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return image_base64
    except Exception as e:
        display_error(f"处理图像时出错: {str(e)}")
        return None

def generate_creative(brand_name, prompt: str, style, size, product_image=None, product_desc:str=None, mask:str='product', background_video_prompt: str=None):
    """
    使用AWS Bedrock API生成创意内容
    
    Args:
        brand_name: 品牌名称
        prompt: 背景提示词
        style: 风格偏好
        size: 图像尺寸
        product_image: 产品图像（Base64编码，可选）
    """
    try:
        # 构建提示
        # if product_image:
        #     prompt = f"为品牌 '{brand_name}' 创建一个广告图像，使用上传的产品图像作为主体。产品描述: {product_description}。风格: {style}。"
        # else:
        #     prompt = f"为品牌 '{brand_name}' 创建一个广告图像。产品描述: {product_description}。风格: {style}。"
        
        # 调用Bedrock API生成图像
        result = bedrock_client.generate_image(prompt, style, size, product_image, mask)
        
        if not result.get("success", False):
            display_error(f"生成图像失败: {result.get('message', '未知错误')}")
            return None
        
        # 创建创意对象
        creative_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        creative = {
            "id": creative_id,
            "brand_name": brand_name,
            "product_desc": product_desc,
            "prompt": prompt,
            "style": style,
            "size": size,
            "has_reference_image": product_image is not None,
            "timestamp": timestamp,
            # "image_url": result["image_url"],
            "status": "completed",
            "background_video_prompt": background_video_prompt,
            "mask_prompt": mask
        }
        
        # 保存到S3和DynamoDB
        # 在实际实现中，这里将上传图像到S3
        s3_result = s3_client.upload_image(result["image_url"][0], creative)
        creative["image_url"] = s3_result["url"]
        creative["presigned_url"] = s3_result["presigned_url"]
        
        # 保存元数据到DynamoDB
        dynamodb_client.save_creative(creative)
        
        # 添加到会话状态
        st.session_state.generated_creatives.append(creative)
        return creative
    except Exception as e:
        display_error(f"生成创意时出错: {str(e)}")
        return None

# 初始化会话状态
if "generated_creatives" not in st.session_state:
    st.session_state.generated_creatives = []

if "prompt_suggestions" not in st.session_state:
    st.session_state.prompt_suggestions = None

if "edited_prompt" not in st.session_state:
    st.session_state.edited_prompt = ""

if "edited_mask" not in st.session_state:
    st.session_state.edited_mask = ""

if "background_video_prompt" not in st.session_state:
    st.session_state.background_video_prompt = ""

def main():
    st.title("🎨 广告创意生成")
    
    st.markdown("""
    在这个页面，您可以生成适用于Google Ads的创意内容。
    填写品牌和产品信息，上传产品图片，然后使用AI分析图片并生成创意提示词。
    您可以编辑提示词，然后生成最终的广告创意。
    """)
    
    # 创建基本信息输入区域（不在表单内，以便支持多步操作）
    col1, col2 = st.columns(2)
    
    with col1:
        brand_name = st.text_input("品牌名称", placeholder="例如：Apple, Nike, Amazon等")
        product_description = st.text_area(
            "产品描述", 
            placeholder="请详细描述您的产品或服务...",
            height=150
        )
        
        # 添加图片上传控件
        uploaded_file = st.file_uploader(
            "上传产品图片", 
            type=["png", "jpg", "jpeg"],
            help="上传产品图片作为图像生成的主体"
        )
    
    with col2:
        # style_options = [
        #     "现代简约", "复古怀旧", "奢华高端", 
        #     "活力青春", "科技感", "自然有机",
        #     "专业商务", "卡通可爱", "极简主义"
        # ]
        # style = st.selectbox("风格偏好", options=style_options)
        style = "normal"

        size_options = [
            "横向 (16:9)", "竖向 (9:16)",
            "正方形 (1:1)", "横幅 (4:1)",
            "方形横幅 (1:1.91)"
        ]
        size = st.selectbox("尺寸", options=size_options)
    
    # 显示上传的图片预览
    if 'uploaded_file' in locals() and uploaded_file is not None:
        st.subheader("上传的产品图片预览")
        st.image(uploaded_file, width=300)
        
        # 添加分析图片按钮
        if st.button("分析图片生成提示词", disabled=not (brand_name and product_description)):
            if not brand_name or not product_description:
                st.error("请先填写品牌名称和产品描述")
            else:
                with st.spinner("正在使用Claude 3分析图片，生成提示词..."):
                    # 处理上传的图片
                    product_image = process_uploaded_image(uploaded_file)
                    if product_image is None:
                        st.error("图片处理失败，请重新上传")
                    else:
                        # 分析图片
                        analysis_result = bedrock_client.analyze_image(product_image, brand_name, product_description)
                        
                        if analysis_result["success"]:
                            st.session_state.prompt_suggestions = analysis_result["analysis"]
                            st.session_state.edited_prompt = analysis_result["analysis"]["complete_prompt"]
                            st.session_state.edited_mask = analysis_result["analysis"]["mask"]
                            st.session_state.background_video_prompt = analysis_result["analysis"]["background_video_prompt"]
                            st.success("图片分析完成，已生成提示词建议！")
                        else:
                            st.error(f"图片分析失败: {analysis_result.get('message', '未知错误')}")
    
    # 显示提示词建议和编辑区域
    if st.session_state.prompt_suggestions is not None:
        st.markdown("---")
        st.subheader("🔍 图片分析结果")
        
        with st.expander("查看详细分析", expanded=True):
            suggestions = st.session_state.prompt_suggestions
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 建议背景")
                st.write(suggestions["background_suggestion"])
                
                st.markdown("### 配色方案")
                st.write(suggestions["color_scheme"])
            
            with col2:
                st.markdown("### 整体氛围")
                st.write(suggestions["atmosphere"])
        
        st.subheader("✏️ 编辑提示词")
        st.markdown("您可以根据需要编辑以下提示词，然后点击'生成创意'按钮")
        
        edited_prompt = st.text_area(
            "提示词",
            value=st.session_state.edited_prompt,
            height=150
        )
        st.session_state.edited_prompt = edited_prompt
        
        edited_mask = st.text_input(
            "蒙版",
            value=st.session_state.edited_mask
        )
        st.session_state.edited_mask = edited_mask
        
        # 生成创意按钮
        if st.button("生成创意", type="primary", disabled=not edited_prompt):
            if not edited_prompt:
                st.error("请输入提示词")
            else:
                with st.spinner("正在生成创意内容，请稍候..."):
                    # 处理上传的图片
                    product_image = None
                    if 'uploaded_file' in locals() and uploaded_file is not None:
                        product_image = process_uploaded_image(uploaded_file)
                        if product_image is None:
                            st.warning("图片处理失败，将不使用参考图片生成创意")
                    
                    # 使用编辑后的提示词生成创意
                    creative = generate_creative(brand_name, edited_prompt, style, size, product_image, 
                                                 product_description, edited_mask, st.session_state.background_video_prompt)

                if creative:
                    # 显示生成的创意
                    st.success("创意内容生成成功！")
                    
                    # 显示预览
                    st.subheader("预览")
                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        st.image(creative["presigned_url"], caption=f"{brand_name} - {style}")
                    
                    with col2:
                        # copy a creative and delete presigned_url property
                        creative_copy = creative.copy()
                        del creative_copy["presigned_url"]
                        st.json(creative_copy)
                else:
                    st.error("创意内容生成失败，请重试")
    
    # 显示历史生成的创意
    if st.session_state.generated_creatives:
        st.markdown("---")
        st.subheader("历史创意")
        
        for i, creative in enumerate(reversed(st.session_state.generated_creatives)):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.image(creative["presigned_url"], width=200)
            
            with col2:
                st.markdown(f"**品牌**: {creative['brand_name']}")
                st.markdown(f"**风格**: {creative['style']}")
                st.markdown(f"**尺寸**: {creative['size']}")
                st.markdown(f"**生成时间**: {creative['timestamp']}")
            
            with col3:
                st.button("下载", key=f"download_{i}")
                st.button("删除", key=f"delete_{i}")
            
            st.markdown("---")

if __name__ == "__main__":
    main()
