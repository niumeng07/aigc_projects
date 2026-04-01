from fastapi import FastAPI, File, UploadFile, HTTPException
import uvicorn
import os
import mimetypes

# 保存路径（你要的视频存放目录）
SAVE_DIR = "/root/llm/ComfyUI/input"  # ⚠️ 改成你服务器上的路径
os.makedirs(SAVE_DIR, exist_ok=True)

app = FastAPI()

# 支持的文件类型
SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}


def get_file_extension(filename):
    """获取文件扩展名"""
    if filename:
        return os.path.splitext(filename.lower())[1]
    return ""


def is_video_file(filename):
    """检查是否为视频文件"""
    ext = get_file_extension(filename)
    return ext in SUPPORTED_VIDEO_EXTENSIONS


def is_image_file(filename):
    """检查是否为图片文件"""
    ext = get_file_extension(filename)
    return ext in SUPPORTED_IMAGE_EXTENSIONS
async def save_file(file: UploadFile, file_type: str):
    """通用文件保存函数"""
    # 从完整路径中提取文件名（处理不同操作系统的路径分隔符）
    original_filename = file.filename
    if original_filename:
        # 使用 os.path.basename 提取文件名，自动处理 / 和 \ 分隔符
        clean_filename = os.path.basename(original_filename)
    else:
        clean_filename = f"unknown_{file_type}"

    # 打印调试信息
    print(f"原始文件名: {original_filename}")
    print(f"清理后文件名: {clean_filename}")
    print(f"文件类型: {file_type}")

    file_path = os.path.join(SAVE_DIR, clean_filename)

    # 保存上传的文件
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "status": "success",
        "file_type": file_type,
        "original_filename": original_filename,
        "saved_filename": clean_filename,
        "saved_to": file_path,
        "file_size": len(content)
    }

@app.post("/upload_video/")
async def upload_video(file: UploadFile = File(...)):
    """上传视频文件"""
    # 检查文件类型
    if not is_video_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的视频格式。支持的格式: {', '.join(SUPPORTED_VIDEO_EXTENSIONS)}"
        )

    return await save_file(file, "video")


@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    """上传图片文件"""
    # 检查文件类型
    if not is_image_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式。支持的格式: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        )

    return await save_file(file, "image")

@app.post("/upload_file/")
async def upload_file(file: UploadFile = File(...)):
    """通用上传接口，自动识别文件类型"""
    filename = file.filename

    if is_video_file(filename):
        return await save_file(file, "video")
    elif is_image_file(filename):
        return await save_file(file, "image")
    else:
        # 如果无法识别类型，也允许上传（保持原有行为）
        return await save_file(file, "unknown")


@app.get("/")
async def root():
    """根路径，显示API信息"""
    return {
        "message": "文件上传服务",
        "endpoints": {
            "upload_video": "POST /upload_video/ - 上传视频文件",
            "upload_image": "POST /upload_image/ - 上传图片文件",
            "upload_file": "POST /upload_file/ - 通用上传接口（自动识别类型）"
        },
        "supported_video_formats": list(SUPPORTED_VIDEO_EXTENSIONS),
        "supported_image_formats": list(SUPPORTED_IMAGE_EXTENSIONS),
        "save_directory": SAVE_DIR
    }


if __name__ == "__main__":
    # 启动服务: python save_video_server.py
    uvicorn.run(app, host="0.0.0.0", port=10000)
