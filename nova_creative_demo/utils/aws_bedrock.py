import boto3
import json
import os
import logging
import base64
import random
from typing import Dict, Any, Optional, List
from random import randint
from datetime import datetime
from utils.image_gen import BedrockImageGenerator, resize_and_pad_image, get_image_base64
import utils.file_utils as file_utils
import utils.video_utils as amazon_video_util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockClient:
    """
    AWS Bedrock API客户端
    用于生成创意内容
    """
    
    def __init__(self, api_key: Optional[str] = None, region: str = "us-east-1"):
        """
        初始化Bedrock客户端
        
        Args:
            api_key: AWS Bedrock API密钥
            region: AWS区域
        """
        self.api_key = api_key or os.getenv("AWS_BEDROCK_API_KEY")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        
        if not self.api_key:
            logger.warning("AWS Bedrock API密钥未配置")
        
        # 在实际实现中，这里将初始化boto3客户端
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region,
            # aws_access_key_id=self.api_key,
            # aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        self.nova_reel_client = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1',
            # aws_access_key_id=self.api_key,
            # aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
    
    def generate_image(self, prompt: str, style: str, size: str, reference_image: Optional[str] = None, mask:str = 'product') -> Dict[str, Any]:
        """
        使用AWS Bedrock生成图像
        
        Args:
            prompt: 图像生成提示
            style: 图像风格
            size: 图像尺寸
            reference_image: 参考图像的Base64编码（可选）
        
        Returns:
            包含生成图像URL的字典
        """
        logger.info(f"生成图像: {prompt}, 风格: {style}, 尺寸: {size}, 使用参考图像: {reference_image is not None}")
        
        # 解析尺寸
        size_mapping = {
            "正方形 (1:1)": {"width": 1024, "height": 1024},
            "横向 (16:9)": {"width": 1280, "height": 720},
            "竖向 (9:16)": {"width": 720, "height": 1280},
            "横幅 (4:1)": {"width": 2048, "height": 512},
            "方形横幅 (1:1.91)": {"width": 1200, "height": 628}
        }
        
        dimensions = size_mapping.get(size, {"width": 1024, "height": 1024})
        
        # 在实际实现中，这里将调用AWS Bedrock API
        # 目前返回模拟数据
        # 实际实现示例:
        # 如果有参考图像，使用图像到图像生成
        if reference_image:
            # Load and pad the image
            source_image_base64 = resize_and_pad_image(reference_image, dimensions['width'], dimensions['height'], 50, 50, 50)

            # Save the image to the output directory
            output_directory = os.path.join("output", datetime.now().strftime("%Y%m%d_%H%M%S"))                        # Define an output directory with a unique name.
            generation_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_directory = f"output/bk-replacement-{generation_id}"

            file_utils.save_base64_images([source_image_base64], output_directory, "pad_image")

            # Configure the inference parameters.
            inference_params = {
                "taskType": "OUTPAINTING",
                "outPaintingParams": {
                    "image": source_image_base64,
                    "text": prompt,  # Description of the background to generate
                    "negativeText": 'logo, faces, hands, illustration, drawing, blurry, blur, text, watermark, render, 3D, NSFW, nude, CGI, monochrome, B&W, cartoon, painting, smooth, plastic, blurry, low-resolution, deep-fried, oversaturated',
                    "maskPrompt": mask,  # The element(s) to keep
                    "outPaintingMode": "PRECISE",  # "DEFAULT" softens the mask. "PRECISE" keeps it sharp.
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,  # Number of variations to generate. 1 to 5.
                    "quality": "standard",  # Allowed values are "standard" and "premium"
                    "cfgScale": 6.5,  # How closely the prompt will be followed
                    "seed": randint(0, 858993459),  # Use a random seed
                },
            }


            # Create the generator.
            generator = BedrockImageGenerator(
                output_directory=output_directory
            )

            # Generate the image(s).
            response_background_replacement = generator.generate_images(inference_params)

            if "images" in response_background_replacement:
                # Save and display each image
                images = file_utils.save_base64_images(response_background_replacement["images"], output_directory, "image")
                # for image in images:
                #     display(image)
                
                return {
                    "success": True,
                    "image_url": response_background_replacement["images"],
                    "prompt": prompt,
                    "style": style,
                    "size": size,
                    "dimensions": dimensions,
                    "used_reference_image": reference_image is not None
                }
            # response = self.client.invoke_model(
            #     modelId="stability.stable-diffusion-xl-v1",
            #     body=json.dumps({
            #         "text_prompts": [{"text": f"{prompt}, {style}"}],
            #         "init_image": reference_image,
            #         "image_strength": 0.35,  # 控制参考图像的影响程度
            #         "cfg_scale": 7,
            #         "steps": 30,
            #         "width": dimensions["width"],
            #         "height": dimensions["height"]
            #     })
            # )
        else:
            return {
                "success": False,
                "message": "参考图像未提供",
            }
        # else:
        #     # 文本到图像生成
        #     response = self.client.invoke_model(
        #         modelId="stability.stable-diffusion-xl-v1",
        #         body=json.dumps({
        #             "text_prompts": [{"text": f"{prompt}, {style}"}],
        #             "cfg_scale": 7,
        #             "steps": 30,
        #             "width": dimensions["width"],
        #             "height": dimensions["height"]
        #         })
        #     )
        # result = json.loads(response["body"].read())
        # image_data = result["artifacts"][0]["base64"]
        
        # 模拟返回数据
        # image_type = "Reference-Based" if reference_image else "Generated"
        # return {
        #     "success": True,
        #     "image_url": f"https://via.placeholder.com/{dimensions['width']}x{dimensions['height']}.png?text={image_type}+Image",
        #     "prompt": prompt,
        #     "style": style,
        #     "size": size,
        #     "dimensions": dimensions,
        #     "used_reference_image": reference_image is not None
        # }
    
    def analyze_image(self, image_base64: str, brand_name: str, product_description: str) -> Dict[str, Any]:
        """
        使用Claude 3多模态能力分析图像并生成提示词
        
        Args:
            image_base64: Base64编码的图像数据
            brand_name: 品牌名称
            product_description: 产品描述
        
        Returns:
            包含分析结果和提示词的字典
        """
        logger.info(f"分析图像: 品牌 '{brand_name}'")
        
        try:
            """
            
            Areas to Consider for Prompt:
            1. Composition
            - Camera angle and distance
            - Subject placement and framing
            - Perspective and viewpoint
            - Background elements and negative space

            2. Lighting and Atmosphere
            - Light direction and quality
            - Time of day and environmental conditions
            - Mood and emotional impact
            - Color temperature and contrast

            3. Technical Specifications
            - Resolution and detail level
            - Focus and depth of field
            - Color grading and processing
            - Format-specific parameters

            4. Style and Medium (when appropriate)
            - Artistic techniques
            - Rendering methods
            - Visual effects
            - Textural elements

            PROMPT STRUCTURE GUIDELINES:
            - Keep changes focused and purposeful
            - Maintain professional quality standards
            - Avoid unnecessary artistic liberties with commercial/product imagery
            - Use technical parameters sparingly and only when they enhance the result
            - Start each prompt with a clear description of the main subject (the background texture/pattern)
            - Describe the environment and context that relates to the product's themes
            - Specify lighting details to match the product's mood (soft, dramatic, ethereal, etc.)
            - Mention specific visual style or artistic medium that complements the product
            - Use descriptive language rather than commands (describe what you see, not what to do)
            - Include technical parameters (1:1 aspect ratio, soft focus on edges, etc.)

            """
            # 提示词(Prompt)应该包括:
            # 1. 产品的主要特点
            # 2. 理想的背景场景
            # 3. 色彩和光线建议, 提升视觉对比度
            # 4. 整体氛围和风格
            # 5. 高质量画质(Professional product photography, 8K resolution)
            # 在实际实现中，这里将调用AWS Bedrock Claude 3 API
            # 构建多模态请求
            prompt = f"""
            你是一位广告创意专家。请分析这张产品图片，并为以下品牌和产品生成广告创意提示词。
            
            品牌: {brand_name}
            产品描述: {product_description}
            
            请详细描述图片中的产品特点、背景、色彩和氛围。然后生成一个详细的英文提示词(Prompt)，用于创建一个引人注目的产品背景图。

            提示词(Prompt)应该包括:
              1. 产品的主要特点
              2. 理想的背景场景
              3. 色彩和光线建议, 提升视觉对比度
              4. 整体氛围和风格
              5. 高质量画质(Professional product photography, 8K resolution)

            提示词不能超过200个Token.
            
            提示词Example:
            Serene outdoor garden setting, soft morning light filtered through leaves. 
            The product is placed in the middle of a white stone or marble platform, surrounded by lavender plants in soft focus. 
            Fresh dewdrops on foliage catching sunlight. Delicate morning mist in background. 
            Depth of field emphasizing product in foreground. Natural color palette with soft purples, greens, and white tones. 
            Professional product photography, 8K resolution. Golden hour lighting creating gentle rim light on bottle edge and generating a shadow of the product. 
            Hyper-realistic botanical details with macro-style flower elements. Clean, fresh atmosphere matching product aesthetic.

            请以JSON格式返回结果，包含以下字段:

            - background_suggestion: 建议的背景场景（中文）
            - color_scheme: 建议的配色方案（中文）
            - atmosphere: 建议的整体氛围（中文）
            - complete_prompt: 完整的提示词(英文)
            - mask: 蒙版的对象（一个描述商品主体的单词），从提示词里获取
            - background_video_prompt: Specify video generation prompt. Phrase your prompt as a summary rather than a command. Maximum 100 tokens.
            """
            
            # 构建请求体
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.client.invoke_model(
                # modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",

                body=json.dumps(request_body)
            )
            
            result = json.loads(response["body"].read())
            response_text = result["content"][0]["text"]
            
            # 解析JSON响应
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            analysis_result = json.loads(json_str)

            # 模拟返回数据
            # analysis_result = {
            #     "product_features": [
            #         "高品质材质",
            #         "现代简约设计",
            #         "人体工学结构",
            #         "多功能用途"
            #     ],
            #     "background_suggestion": "明亮、简约的现代家居或办公环境，带有自然光线",
            #     "color_scheme": "主色调为中性色(白色、灰色)，搭配品牌色作为点缀",
            #     "atmosphere": "专业、高端、舒适",
            #     "complete_prompt": f"展示{brand_name}的产品在明亮、简约的现代环境中，强调其高品质材质和人体工学设计。使用自然光线突出产品细节，整体色调以中性色为主，营造专业、高端的氛围。产品应是画面的焦点，周围环境简洁不杂乱。"
            # }
            
            return {
                "success": True,
                "analysis": analysis_result
            }
        except Exception as e:
            logger.error(f"分析图像失败: {str(e)}")
            return {
                "success": False,
                "message": f"分析图像失败: {str(e)}"
            }
    
    def generate_video(self, image_base64: str, prompt: str, s3_bucket: str, mask: str) -> Dict[str, Any]:
        """
        使用AWS Bedrock Nova Reel模型从图像生成视频
        
        Args:
            image_base64: Base64编码的图像数据
            prompt: 视频生成提示词
            s3_bucket: 存储生成视频的S3存储桶名称
        
        Returns:
            包含异步任务信息的字典
        """
        logger.info("开始生成视频...")
        
        try:
            # 固定前缀，确保生成静态视频
            FIXED_PREFIX = f"Static camera shot. The {mask} remains completely still."
            
            # 构建完整的提示词
            full_prompt = f"""
            {FIXED_PREFIX}
            {prompt}
            """
            
            # 构建模型输入
            model_input = {
                "taskType": "TEXT_VIDEO",
                "textToVideoParams": {
                    "text": full_prompt,
                    "images": [
                        {
                            "format": "png",
                            "source": {
                                "bytes": image_base64
                            }
                        }
                    ]
                },
                "videoGenerationConfig": {
                    "durationSeconds": 6,  # 目前仅支持6秒
                    "fps": 24,  # 目前仅支持24fps
                    "dimension": "1280x720",  # 目前仅支持1280x720
                    "seed": random.randint(0, 2147483648)  # 随机种子确保每次生成不同的结果
                }
            }
            
            # 启动异步视频生成任务
            invocation = self.nova_reel_client.start_async_invoke(
                modelId="amazon.nova-reel-v1:0",
                modelInput=model_input,
                outputDataConfig={"s3OutputDataConfig": {"s3Uri": f"s3://{s3_bucket}"}}
            )
            
            return {
                "success": True,
                "message": "视频生成任务已启动",
                "invocation_arn": invocation["invocationArn"],
                "status": "IN_PROGRESS"
            }
            
        except Exception as e:
            logger.exception(f"启动视频生成任务失败: {str(e)}")
            return {
                "success": False,
                "message": f"启动视频生成任务失败: {str(e)}"
            }
    
    def check_video_status(self, invocation_arn: str) -> Dict[str, Any]:
        """
        检查视频生成任务的状态
        
        Args:
            invocation_arn: 异步任务的ARN
        
        Returns:
            包含任务状态的字典
        """
        try:
            output_directory_video = amazon_video_util.monitor_and_download_video(invocation_arn, "output")

            # response = self.nova_reel_client.get_async_invoke_status(invocationArn=invocation_arn)
            
            # status = response["status"]
            # result = {
            #     "success": True,
            #     "status": status,
            #     "invocation_arn": invocation_arn
            # }
            
            # if status == "COMPLETED":
            #     result["output_location"] = response["outputLocation"]
            # elif status == "FAILED":
            #     result["error"] = response.get("failureReason", "Unknown error")
            
            result = {
                "success": True,
                "status": "COMPLETED",
                "invocation_arn": invocation_arn,
                "output_location": output_directory_video
            }
            return result
        except Exception as e:
            logger.error(f"检查视频生成任务状态失败: {str(e)}")
            return {
                "success": False,
                "message": f"检查任务状态失败: {str(e)}"
            }
    
    def generate_image_tags(self, image_url: str) -> Dict[str, Any]:
        """
        为图像生成维度标签
        
        Args:
            image_url: 图像的URL
        
        Returns:
            包含生成的标签的字典
        """
        logger.info(f"为图像生成标签: {image_url}")
        
        try:
            # 在实际实现中，这里将调用AWS Bedrock Claude 3 API来分析图像并生成标签
            # 目前返回模拟数据
            prompt = f"""
            分析这张图片，并生成以下两个维度的标签：
            1. 图片主元素
            2. 图片主色调
            
            请以JSON格式返回结果，包含这两个维度的标签列表。
            """

            image_base64 = get_image_base64(image_url)
            
            # 构建请求体
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.client.invoke_model(
                # modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                body=json.dumps(request_body)
            )
            
            result = json.loads(response["body"].read())
            response_text = result["content"][0]["text"]
            
            # 解析JSON响应
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            tags = json.loads(json_str)
            
            return {
                "success": True,
                "tags": tags
            }
        except Exception as e:
            logger.error(f"生成图像标签失败: {str(e)}")
            return {
                "success": False,
                "message": f"生成图像标签失败: {str(e)}"
            }

    def test_connection(self) -> Dict[str, Any]:
        """
        测试与AWS Bedrock的连接
        
        Returns:
            包含连接状态的字典
        """
        if not self.api_key:
            return {"success": False, "message": "AWS Bedrock API密钥未配置"}
        
        try:
            # 在实际实现中，这里将测试与AWS Bedrock的连接
            # 目前返回模拟数据
            # self.client.list_foundation_models(maxResults=1)
            return {"success": True, "message": "AWS Bedrock连接成功"}
        except Exception as e:
            logger.error(f"AWS Bedrock连接失败: {str(e)}")
            return {"success": False, "message": f"AWS Bedrock连接失败: {str(e)}"}
