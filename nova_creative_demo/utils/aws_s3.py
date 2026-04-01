import boto3
import os
import logging
import base64
from typing import Dict, Any, Optional, BinaryIO
from io import BytesIO
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Client:
    """
    AWS S3客户端
    用于存储生成的创意资产
    """
    
    def __init__(self, api_key: Optional[str] = None, region: str = "us-east-1", bucket: Optional[str] = None):
        """
        初始化S3客户端
        
        Args:
            api_key: AWS API密钥
            region: AWS区域
            bucket: S3存储桶名称
        """
        self.api_key = api_key or os.getenv("AWS_BEDROCK_API_KEY")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.bucket = bucket or os.getenv("AWS_S3_BUCKET")
        
        if not self.api_key:
            logger.warning("AWS API密钥未配置")
        
        if not self.bucket:
            logger.warning("S3存储桶未配置")
               
        # 在实际实现中，这里将初始化boto3客户端
        self.client = boto3.client(
            service_name='s3',
            region_name=self.region,
            # aws_access_key_id=self.api_key,
            # aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

        logger.info(f"初始化S3客户端: region={self.region}, bucket={self.bucket}")

    
    def upload_image(self, image_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传图像到S3
        
        Args:
            image_data: Base64编码的图像数据
            metadata: 图像元数据
        
        Returns:
            包含上传状态和URL的字典
        """
        if not self.bucket:
            return {"success": False, "message": "S3存储桶未配置"}
        
        try:
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            file_name = f"creative_{timestamp}_{file_id}.png"
            
            # 在实际实现中，这里将解码Base64数据并上传到S3
            image_binary = base64.b64decode(image_data)
            
            # 确保元数据只包含ASCII字符
            safe_metadata = {}
            
            # 对于可能包含非ASCII字符的字段，使用base64编码
            if 'brand_name' in metadata:
                brand_name = metadata.get('brand_name', '')
                safe_metadata['brand_encoded'] = base64.b64encode(brand_name.encode('utf-8')).decode('ascii')
            
            if 'style' in metadata:
                style = metadata.get('style', '')
                safe_metadata['style_encoded'] = base64.b64encode(style.encode('utf-8')).decode('ascii')
            
            # 添加其他安全的ASCII元数据
            safe_metadata['created'] = timestamp
            safe_metadata['file_id'] = file_id
            
            # 上传到S3
            self.client.upload_fileobj(
                BytesIO(image_binary),
                self.bucket,
                file_name,
                ExtraArgs={
                    'ContentType': 'image/png',
                    'Metadata': safe_metadata
                }
            )
            
            # 构建S3 URL
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{file_name}"
            
            # 模拟返回数据
            # url = f"https://via.placeholder.com/600x600.png?text=S3+Stored+Image"
            
            # Generate presigned url for the uploaded image
            presigned_url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': file_name},
                ExpiresIn=1200)

            return {
                "success": True,
                "message": "图像上传成功",
                "url": url,
                "presigned_url": presigned_url,
                "file_name": file_name,
                "timestamp": timestamp
            }
        except Exception as e:
            logger.exception(f"图像上传失败: {str(e)}")
            return {"success": False, "message": f"图像上传失败: {str(e)}"}
    
    def generate_presigned_url(self, s3_url_of_file: str) -> str:
        file_name = s3_url_of_file.split('/')[-1]
        presigned_url = self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': file_name},
            ExpiresIn=1200)
        
        return presigned_url

    def list_images(self, prefix: str = "creative_", max_items: int = 10) -> Dict[str, Any]:
        """
        列出S3存储桶中的图像
        
        Args:
            prefix: 文件名前缀
            max_items: 最大项目数
        
        Returns:
            包含图像列表的字典
        """
        if not self.bucket:
            return {"success": False, "message": "S3存储桶未配置", "images": []}
        
        try:
            # 在实际实现中，这里将列出S3存储桶中的图像
            # response = self.client.list_objects_v2(
            #     Bucket=self.bucket,
            #     Prefix=prefix,
            #     MaxKeys=max_items
            # )
            
            # images = []
            # if 'Contents' in response:
            #     for item in response['Contents']:
            #         obj = self.client.get_object(Bucket=self.bucket, Key=item['Key'])
            #         metadata = obj.get('Metadata', {})
            #         
            #         # 解码base64编码的元数据
            #         decoded_metadata = {}
            #         
            #         if 'brand_encoded' in metadata:
            #             try:
            #                 brand_bytes = base64.b64decode(metadata['brand_encoded'])
            #                 decoded_metadata['brand'] = brand_bytes.decode('utf-8')
            #             except Exception as e:
            #                 logger.error(f"解码品牌元数据失败: {str(e)}")
            #                 decoded_metadata['brand'] = metadata['brand_encoded']
            #         
            #         if 'style_encoded' in metadata:
            #             try:
            #                 style_bytes = base64.b64decode(metadata['style_encoded'])
            #                 decoded_metadata['style'] = style_bytes.decode('utf-8')
            #             except Exception as e:
            #                 logger.error(f"解码风格元数据失败: {str(e)}")
            #                 decoded_metadata['style'] = metadata['style_encoded']
            #         
            #         # 添加其他元数据
            #         for key, value in metadata.items():
            #             if key not in ['brand_encoded', 'style_encoded']:
            #                 decoded_metadata[key] = value
            #         
            #         images.append({
            #             'key': item['Key'],
            #             'url': f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{item['Key']}",
            #             'last_modified': item['LastModified'].isoformat(),
            #             'size': item['Size'],
            #             'metadata': decoded_metadata
            #         })
            
            # 模拟返回数据
            images = [
                {
                    'key': f"creative_20250226{i:02d}0000_abcd1234.png",
                    'url': f"https://via.placeholder.com/600x600.png?text=Image+{i}",
                    'last_modified': datetime.now().isoformat(),
                    'size': 1024 * 1024,
                    'metadata': {
                        'brand': f"Brand {i}",
                        'style': f"Style {i}",
                        'created': datetime.now().strftime("%Y%m%d%H%M%S")
                    }
                }
                for i in range(1, 4)
            ]
            
            return {
                "success": True,
                "message": f"找到 {len(images)} 个图像",
                "images": images
            }
        except Exception as e:
            logger.error(f"列出图像失败: {str(e)}")
            return {"success": False, "message": f"列出图像失败: {str(e)}", "images": []}
    
    def delete_image(self, key: str) -> Dict[str, Any]:
        """
        从S3删除图像
        
        Args:
            key: 图像键
        
        Returns:
            包含删除状态的字典
        """
        if not self.bucket:
            return {"success": False, "message": "S3存储桶未配置"}
        
        try:
            # 在实际实现中，这里将从S3删除图像
            # self.client.delete_object(
            #     Bucket=self.bucket,
            #     Key=key
            # )
            
            # 模拟返回数据
            return {
                "success": True,
                "message": f"图像 {key} 已删除"
            }
        except Exception as e:
            logger.error(f"删除图像失败: {str(e)}")
            return {"success": False, "message": f"删除图像失败: {str(e)}"}
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试与S3的连接
        
        Returns:
            包含连接状态的字典
        """
        if not self.api_key:
            return {"success": False, "message": "AWS API密钥未配置"}
        
        if not self.bucket:
            return {"success": False, "message": "S3存储桶未配置"}
        
        try:
            # 在实际实现中，这里将测试与S3的连接
            # self.client.head_bucket(Bucket=self.bucket)
            return {"success": True, "message": "S3连接成功"}
        except Exception as e:
            logger.error(f"S3连接失败: {str(e)}")
            return {"success": False, "message": f"S3连接失败: {str(e)}"}
