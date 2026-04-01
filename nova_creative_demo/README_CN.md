# Nova Creative Playground

Nova Creative Playground 是一个基于 Streamlit 的应用程序，用于生成广告创意内容、视频。

## 功能特点

- **创意生成**：使用 AWS Bedrock 生成广告创意内容和素材
- **视频生成**：将创意图片转换为引人注目的视频
- **配置中心**：管理 API 密钥和应用程序设置

## 项目结构

```
project/
├── main.py          # 主入口
├── pages/
│   ├── 1_创意生成.py
│   ├── 9_配置中心.py
│   └── 4_视频生成.py
│   └── 6_创意库.py
├── utils/           # 工具函数
│   ├── aws_bedrock.py
│   ├── aws_s3.py
│   ├── aws_dynamodb.py
│   └── common.py
├── .env             # 环境变量（需要从.env.template创建）
└── requirements.txt # 依赖项
└── create_final_video.py # 生成最终贴图过的视频

```

## 安装与设置

### 1. 克隆仓库

```bash
git clone <repository-url>
cd <repo_folder>
```

### 2. 创建虚拟环境

推荐python3.12+的版本

```bash
# 使用 venv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

从模板创建 `.env` 文件：

```bash
cp .env.template .env
```

然后编辑 `.env` 文件，填入您的 API 密钥和其他配置：

注意: AWS Credential请另外配置

**请在AWS Console上创建S3存储桶，桶的Region和下面的配置项要一致。**

**DynamoDB的表会自动创建**

```
# AWS Configuration
AWS_REGION=us-east-1
AWS_S3_BUCKET=your_s3_bucket_name_here
AWS_DYNAMODB_TABLE=nova-creative-playground
```

## 运行应用程序

```bash
streamlit run main.py
```

应用程序将在 http://localhost:8501 启动。

## 使用指南

### 创意图片生成

1. 导航到"创意生成"页面
2. 输入品牌名称和产品描述
3. 选择风格偏好和尺寸
4. 点击"生成创意"按钮
5. 查看生成的创意内容

### 视频生成

1. 导航到"视频生成"页面
2. 选择之前生成的创意图片
3. 输入场景描述
4. 点击"生成视频"按钮
5. 等待视频生成完成（约3-4分钟）
6. 查看和下载生成的视频

**注意: 如果需要高质量的产品贴图后的视频，请在生成视频后，手动执行create_final_video.py脚本**

### 配置中心

1. 导航到"配置中心"页面
2. 配置 AWS 和 DeepSeek API 密钥
3. 调整应用程序设置
4. 点击"保存配置"按钮

### 创意库

1. 导航到"创意库"页面
2. 浏览和管理之前生成的创意内容
3. 对创意进行评分和标记
4. 导出选定的创意内容

## 注意事项

- 本应用程序需要有效的 AWS Credential密钥才能正常工作
- 确保您的 AWS 账户有足够的权限访问 Bedrock、S3 和 DynamoDB 服务
- 生成的创意内容、视频仅供参考，请根据实际情况进行调整
- 视频生成功能使用 AWS Bedrock 的 Nova Reel 模型，生成时间约为3-4分钟

## 技术栈

- **前端**：Streamlit
- **后端**：Python
- **AI 服务**：AWS Bedrock (Claude3.5, Nova Canvas和Nova Reel)
- **存储**：AWS S3, DynamoDB
