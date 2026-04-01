import streamlit as st
import pandas as pd
from utils.aws_dynamodb import DynamoDBClient
from utils.aws_bedrock import BedrockClient
from utils.aws_s3 import S3Client
import os

st.set_page_config(page_title="创意库", page_icon="📚", layout="wide")

dynamodb_client = DynamoDBClient(
    api_key=os.getenv("AWS_BEDROCK_API_KEY"),
    region=os.getenv("AWS_REGION", "us-east-1"),
    table_name=os.getenv("AWS_DYNAMODB_TABLE", "ads-assistant")
)

bedrock_client = BedrockClient(
    api_key=os.getenv("AWS_BEDROCK_API_KEY"),
    region=os.getenv("AWS_REGION", "us-east-1")
)

s3_client = S3Client(
    api_key=os.getenv("AWS_BEDROCK_API_KEY"),
    region=os.getenv("AWS_REGION", "us-east-1"),
    bucket=os.getenv("AWS_S3_BUCKET")
)

st.title("创意库")

# Fetch all creatives from DynamoDB
creatives = dynamodb_client.get_all_items("ads-assistant")

if creatives:
    # Display creatives in a list
    for creative in creatives:
        creative["external_ad_id"] = creative['external_ad_id'] if "external_ad_id" in creative else None
    df = pd.DataFrame(creatives)
    # print(creatives)
    st.dataframe(df[["id", "brand_name", "size", "timestamp", "external_ad_id"]], use_container_width=True)

    # Creative details
    selected_creative = st.selectbox("选择创意查看详情", df["id"].tolist())
    if selected_creative:
        creative = df[df["id"] == selected_creative].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            presigned_url = s3_client.generate_presigned_url(creative["image_url"])
            st.image(presigned_url, use_column_width=True)
        with col2:
            st.write(f"Prompt: {creative['prompt']}")
            
            # Update External_AD_ID
            new_external_ad_id = st.text_input("External AD ID", value=creative.get("external_ad_id", ""))
            if st.button("更新 External AD ID"):
                dynamodb_client.update_item("ads-assistant", creative["id"], creative["timestamp"], {"external_ad_id": new_external_ad_id})
                st.success("External AD ID 已更新")
            
            # Generate dimension tags
            if st.button("生成维度标签"):
                tags_response = bedrock_client.generate_image_tags(presigned_url)
                if tags_response["success"]:
                    tags = tags_response["tags"]
                    print(tags)
                    dynamodb_client.update_item("ads-assistant", creative["id"], creative["timestamp"], {"dimension_tags": tags})
                    st.success("维度标签已生成")
                else:
                    st.error("生成维度标签失败")

            # Display existing tags
            if "dimension_tags" in creative:
                st.write("维度标签:")
                st.write(creative["dimension_tags"])
else:
    st.write("没有找到创意，请先生成一些创意。")
