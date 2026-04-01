import boto3
import os
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDBClient:
    """
    AWS DynamoDB客户端
    用于存储创意和优化洞察的元数据
    """
    
    def __init__(self, api_key: Optional[str] = None, region: str = "us-east-1", table_name: Optional[str] = None):
        """
        初始化DynamoDB客户端
        
        Args:
            api_key: AWS API密钥
            region: AWS区域
            table_name: DynamoDB表名
        """
        self.api_key = api_key or os.getenv("AWS_BEDROCK_API_KEY")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.table_name = table_name or os.getenv("AWS_DYNAMODB_TABLE", "ads-assistant")
        self.insight_table_name = os.getenv("AWS_DYNAMODB_INSIGHT_TABLE", "ads-assistant-insight")

        
        if not self.api_key:
            logger.warning("AWS API密钥未配置")
        
        if not self.table_name:
            logger.warning("DynamoDB表名未配置")
        
        # 在实际实现中，这里将初始化boto3客户端
        self.client = boto3.resource(
            'dynamodb',
            region_name=self.region,
            # aws_access_key_id=self.api_key,
            # aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        # Check if table exists, if not, create it
        try:
            self.table = self.client.Table(self.table_name)
            self.client.meta.client.describe_table(TableName=self.table_name)
            logger.info(f"Table {self.table_name} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self.table = self.client.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                # Wait for the table to be created
                self.table.wait_until_exists()
                logger.info(f"Table {self.table_name} created successfully")
            else:
                raise e
            
        try:
            self.insight_table = self.client.Table(self.insight_table_name)
            self.client.meta.client.describe_table(TableName=self.insight_table_name)
            logger.info(f"Table {self.insight_table} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self.insight_table = self.client.create_table(
                    TableName=self.insight_table_name,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'},
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'},
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                # Wait for the table to be created
                self.insight_table.wait_until_exists()
                logger.info(f"Table {self.insight_table_name} created successfully")
            else:
                raise e
    
    def save_creative(self, creative_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存创意元数据到DynamoDB
        
        Args:
            creative_data: 创意数据
        
        Returns:
            包含保存状态的字典
        """
        if not self.table_name:
            return {"success": False, "message": "DynamoDB表名未配置"}
        
        try:
            # 确保有ID
            if "id" not in creative_data:
                creative_data["id"] = str(uuid.uuid4())
            
            # 添加时间戳
            if "timestamp" not in creative_data:
                creative_data["timestamp"] = datetime.now().isoformat()
            
            # 添加项目类型
            creative_data["item_type"] = "creative"

            # 不保存presigned_url
            temp = None
            if "presigned_url" in creative_data:
                temp = creative_data['presigned_url']
                del creative_data["presigned_url"]
            
            # 在实际实现中，这里将保存到DynamoDB
            self.table.put_item(Item=creative_data)

            creative_data['presigned_url'] = temp
            
            # 模拟返回数据
            return {
                "success": True,
                "message": "创意元数据已保存",
                "id": creative_data["id"]
            }
        except Exception as e:
            logger.error(f"保存创意元数据失败: {str(e)}")
            return {"success": False, "message": f"保存创意元数据失败: {str(e)}"}
    
    def save_insight(self, insight_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存优化洞察到DynamoDB
        
        Args:
            insight_data: 洞察数据
        
        Returns:
            包含保存状态的字典
        """
        if not self.insight_table_name:
            return {"success": False, "message": "DynamoDB表名未配置"}
        
        try:
            # 确保有ID
            if "id" not in insight_data:
                insight_data["id"] = str(uuid.uuid4())
            
            # 添加时间戳
            if "timestamp" not in insight_data:
                insight_data["timestamp"] = datetime.now().isoformat()
            
            # 添加项目类型
            insight_data["item_type"] = "insight"
            
            print('start save insight')
            # 在实际实现中，这里将保存到DynamoDB
            self.insight_table.put_item(Item=insight_data)
            print('end save insight')

            # 模拟返回数据
            return {
                "success": True,
                "message": "优化洞察已保存",
                "id": insight_data["id"]
            }
        except Exception as e:
            logger.error(f"保存优化洞察失败: {str(e)}")
            return {"success": False, "message": f"保存优化洞察失败: {str(e)}"}
    
    def get_creatives(self, limit: int = 10) -> Dict[str, Any]:
        """
        从DynamoDB获取创意列表
        
        Args:
            limit: 最大项目数
        
        Returns:
            包含创意列表的字典
        """
        if not self.table_name:
            return {"success": False, "message": "DynamoDB表名未配置", "items": []}
        
        try:
            # 使用scan操作获取创意列表
            response = self.table.scan(
                FilterExpression=Key('item_type').eq('creative'),
                Limit=limit
            )
            items = response.get('Items', [])
            
            return {
                "success": True,
                "message": f"找到 {len(items)} 个创意",
                "items": items
            }
        except Exception as e:
            logger.error(f"获取创意列表失败: {str(e)}")
            return {"success": False, "message": f"获取创意列表失败: {str(e)}", "items": []}

    def get_all_items(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取DynamoDB表中的所有项目
        
        Args:
            table_name: DynamoDB表名
        
        Returns:
            包含所有项目的列表
        """
        try:
            table = self.client.Table(table_name)
            response = table.scan()
            items = response['Items']

            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])

            return items
        except Exception as e:
            logger.error(f"获取所有项目失败: {str(e)}")
            return []

    def get_all_items_with_ad_id(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取DynamoDB表中的所有项目
        
        Args:
            table_name: DynamoDB表名
        
        Returns:
            包含所有项目的列表
        """
        try:
            table = self.client.Table(table_name)
            response = table.scan()
            items = response['Items']

            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])

            # Filter out items without ext_ad_id
            items = [item for item in items if 'external_ad_id' in item and item['external_ad_id']]

            return items
        except Exception as e:
            logger.error(f"获取所有项目失败: {str(e)}")
            return []

    def update_item(self, table_name: str, item_id: str, timestamp: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新DynamoDB表中的项目
        
        Args:
            table_name: DynamoDB表名
            item_id: 要更新的项目ID
            update_data: 要更新的数据字典
        
        Returns:
            包含更新状态的字典
        """
        try:
            table = self.client.Table(table_name)
            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in update_data.keys())
            expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
            expression_attribute_values = {f":{k}": v for k, v in update_data.items()}

            response = table.update_item(
                Key={'id': item_id, 'timestamp': timestamp},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="UPDATED_NEW"
            )

            return {"success": True, "message": "项目已更新", "updated_attributes": response.get('Attributes', {})}
        except Exception as e:
            logger.error(f"更新项目失败: {str(e)}")
            return {"success": False, "message": f"更新项目失败: {str(e)}"}
    
    def get_insights(self, limit: int = 10) -> Dict[str, Any]:
        """
        从DynamoDB获取优化洞察列表
        
        Args:
            limit: 最大项目数
        
        Returns:
            包含洞察列表的字典
        """
        if not self.table_name:
            return {"success": False, "message": "DynamoDB表名未配置", "items": []}
        
        try:
            # 在实际实现中，这里将查询DynamoDB
            # response = self.table.query(
            #     IndexName="ItemTypeIndex",
            #     KeyConditionExpression=Key('item_type').eq('insight'),
            #     ScanIndexForward=False,
            #     Limit=limit
            # )
            # items = response.get('Items', [])
            
            # 模拟返回数据
            items = [
                {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "metrics_analyzed": ["CTR", "ROAS", "CPC"],
                    "insights": [
                        {
                            "title": f"优化建议 {i}.1",
                            "description": f"描述 {i}.1",
                            "priority": "高" if i % 2 == 0 else "中",
                            "action": f"建议操作 {i}.1",
                            "status": "pending"
                        },
                        {
                            "title": f"优化建议 {i}.2",
                            "description": f"描述 {i}.2",
                            "priority": "中",
                            "action": f"建议操作 {i}.2",
                            "status": "applied" if i % 2 == 0 else "pending"
                        }
                    ],
                    "item_type": "insight"
                }
                for i in range(1, 3)
            ]
            
            return {
                "success": True,
                "message": f"找到 {len(items)} 个优化洞察",
                "items": items
            }
        except Exception as e:
            logger.error(f"获取优化洞察列表失败: {str(e)}")
            return {"success": False, "message": f"获取优化洞察列表失败: {str(e)}", "items": []}
    
    def update_insight_status(self, insight_id: str, insight_index: int, status: str) -> Dict[str, Any]:
        """
        更新优化洞察状态
        
        Args:
            insight_id: 洞察ID
            insight_index: 洞察索引
            status: 新状态
        
        Returns:
            包含更新状态的字典
        """
        if not self.table_name:
            return {"success": False, "message": "DynamoDB表名未配置"}
        
        try:
            # 在实际实现中，这里将更新DynamoDB中的洞察状态
            # 首先获取当前项目
            # response = self.table.get_item(Key={"id": insight_id})
            # if "Item" not in response:
            #     return {"success": False, "message": f"未找到ID为 {insight_id} 的洞察"}
            
            # item = response["Item"]
            # if "insights" not in item or insight_index >= len(item["insights"]):
            #     return {"success": False, "message": f"洞察索引 {insight_index} 无效"}
            
            # # 更新状态
            # item["insights"][insight_index]["status"] = status
            
            # # 保存回DynamoDB
            # self.table.put_item(Item=item)
            
            # 模拟返回数据
            return {
                "success": True,
                "message": f"洞察状态已更新为 {status}"
            }
        except Exception as e:
            logger.error(f"更新洞察状态失败: {str(e)}")
            return {"success": False, "message": f"更新洞察状态失败: {str(e)}"}
    
    def delete_item(self, item_id: str) -> Dict[str, Any]:
        """
        从DynamoDB删除项目
        
        Args:
            item_id: 项目ID
        
        Returns:
            包含删除状态的字典
        """
        if not self.table_name:
            return {"success": False, "message": "DynamoDB表名未配置"}
        
        try:
            # 在实际实现中，这里将从DynamoDB删除项目
            # self.table.delete_item(Key={"id": item_id})
            
            # 模拟返回数据
            return {
                "success": True,
                "message": f"项目 {item_id} 已删除"
            }
        except Exception as e:
            logger.error(f"删除项目失败: {str(e)}")
            return {"success": False, "message": f"删除项目失败: {str(e)}"}
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试与DynamoDB的连接
        
        Returns:
            包含连接状态的字典
        """
        if not self.api_key:
            return {"success": False, "message": "AWS API密钥未配置"}
        
        if not self.table_name:
            return {"success": False, "message": "DynamoDB表名未配置"}
        
        try:
            # 在实际实现中，这里将测试与DynamoDB的连接
            # self.client.meta.client.describe_table(TableName=self.table_name)
            return {"success": True, "message": "DynamoDB连接成功"}
        except Exception as e:
            logger.error(f"DynamoDB连接失败: {str(e)}")
            return {"success": False, "message": f"DynamoDB连接失败: {str(e)}"}
