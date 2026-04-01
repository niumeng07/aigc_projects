import streamlit as st
import os
from dotenv import load_dotenv
from utils.common import init_session_state

# Load environment variables
load_dotenv()

# Configure page settings
st.set_page_config(
    page_title="Google Ads Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
init_session_state()

# Main page content
def main():
    st.title("AWS Ads Assistant")
    
    st.markdown("""
    ## 欢迎使用 AWS Ads Assistant
    
    这个应用程序可以帮助您：
    * 生成创意广告内容和素材
    * 将创意图片转换为视频
    * 管理API配置和设置
    
    请使用左侧导航栏选择功能模块。
    """)
    
    # Display app info
    st.sidebar.success("选择上方的功能页面")
    
    # Display app version and info in the sidebar footer
    st.sidebar.markdown("---")
    st.sidebar.caption("AWS Ads Assistant v1.0")
    
    # Add GitHub link
    # st.sidebar.markdown("[查看源代码](https://github.com/yourusername/aws-ads-assistant)")

if __name__ == "__main__":
    main()
