import streamlit as st
import os
import json
from dotenv import load_dotenv
from utils.aws_bedrock import BedrockClient
from utils.aws_s3 import S3Client
from utils.aws_dynamodb import DynamoDBClient
from utils.common import display_error, display_success, display_info, display_warning

# Page configuration
st.set_page_config(
    page_title="配置中心 - Nova Creative Playground",
    page_icon="⚙️",
    layout="wide"
)

# Load environment variables
load_dotenv()

def save_config_to_env():
    """
    将配置保存到.env文件
    """
    config = st.session_state.config
    env_content = f"""# AWS Configuration
AWS_REGION={config['aws']['region']}
AWS_S3_BUCKET={config['aws']['s3_bucket']}
AWS_DYNAMODB_TABLE={config['aws']['dynamodb_table']}

# App Configuration
APP_THEME={config['app']['theme']}
APP_LANGUAGE={config['app']['language']}
APP_MAX_HISTORY_ITEMS={config['app']['max_history_items']}
"""
    
    try:
        # 写入.env文件
        with open(".env", "w") as f:
            f.write(env_content)
        display_success("配置已保存到.env文件！")
    except Exception as e:
        display_error(f"保存配置失败: {str(e)}")
        # 显示配置内容
        st.code(env_content, language="bash")
    
    # 重新加载环境变量
    load_dotenv(override=True)

def test_aws_connection():
    """
    测试AWS连接
    """
    config = st.session_state.config
    
    # 初始化客户端
    bedrock_client = BedrockClient(
        region=config["aws"]["region"]
    )
    
    s3_client = S3Client(
        region=config["aws"]["region"],
        bucket=config["aws"]["s3_bucket"]
    )
    
    dynamodb_client = DynamoDBClient(
        region=config["aws"]["region"],
        table_name=config["aws"]["dynamodb_table"]
    )
    
    # 测试连接
    bedrock_result = bedrock_client.test_connection()
    s3_result = s3_client.test_connection()
    dynamodb_result = dynamodb_client.test_connection()
    
    # 检查结果
    if not bedrock_result["success"]:
        return False, f"AWS Bedrock连接失败: {bedrock_result['message']}"
    
    if not s3_result["success"]:
        return False, f"AWS S3连接失败: {s3_result['message']}"
    
    if not dynamodb_result["success"]:
        return False, f"AWS DynamoDB连接失败: {dynamodb_result['message']}"
    
    return True, "AWS服务连接测试成功！"

def main():
    st.title("⚙️ 配置中心")
    
    st.markdown("""
    在这个页面，您可以配置应用程序的各项设置，包括API密钥、存储设置和应用程序首选项。
    请确保正确配置所有必要的API密钥，以便应用程序能够正常工作。
    """)
    
    # 创建配置选项卡
    tab1, tab3 = st.tabs(["AWS配置", "应用程序设置"])
    
    with tab1:
        st.subheader("AWS配置")
        st.markdown("配置AWS Bedrock、S3和DynamoDB的设置")
        
        # AWS区域
        aws_region_options = ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "ap-northeast-1", "ap-southeast-1", "eu-west-1"]
        aws_region = st.selectbox(
            "AWS区域",
            options=aws_region_options,
            index=aws_region_options.index(st.session_state.config["aws"]["region"]) if st.session_state.config["aws"]["region"] in aws_region_options else 0
        )
        
        # S3存储桶
        aws_s3_bucket = st.text_input(
            "S3存储桶名称",
            value=st.session_state.config["aws"]["s3_bucket"]
        )
        
        # DynamoDB表名
        aws_dynamodb_table = st.text_input(
            "DynamoDB表名",
            value=st.session_state.config["aws"]["dynamodb_table"]
        )
        
        # 更新配置
        if st.button("保存AWS配置"):
            st.session_state.config["aws"]["region"] = aws_region
            st.session_state.config["aws"]["s3_bucket"] = aws_s3_bucket
            st.session_state.config["aws"]["dynamodb_table"] = aws_dynamodb_table
            st.success("AWS配置已更新！")
        
        # 测试连接
        if st.button("测试AWS连接"):
            success, message = test_aws_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
    
    with tab3:
        st.subheader("应用程序设置")
        st.markdown("配置应用程序的外观和行为")
        
        # 主题设置
        theme_options = ["light", "dark"]
        theme = st.selectbox(
            "应用主题",
            options=theme_options,
            index=theme_options.index(st.session_state.config["app"]["theme"]) if st.session_state.config["app"]["theme"] in theme_options else 0
        )
        
        # 语言设置
        language_options = ["zh", "en"]
        language = st.selectbox(
            "应用语言",
            options=language_options,
            index=language_options.index(st.session_state.config["app"]["language"]) if st.session_state.config["app"]["language"] in language_options else 0
        )
        
        # 历史记录设置
        max_history_items = st.slider(
            "最大历史记录项数",
            min_value=5,
            max_value=50,
            value=st.session_state.config["app"]["max_history_items"],
            step=5
        )
        
        # 更新配置
        if st.button("保存应用程序设置"):
            st.session_state.config["app"]["theme"] = theme
            st.session_state.config["app"]["language"] = language
            st.session_state.config["app"]["max_history_items"] = max_history_items
            st.success("应用程序设置已更新！")
    
    # 保存所有配置到.env文件
    st.markdown("---")
    if st.button("保存所有配置到.env文件", type="primary"):
        save_config_to_env()
    
    # 显示当前配置
    with st.expander("查看当前配置"):
        st.json(st.session_state.config)

if __name__ == "__main__":
    main()
