import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video

pipe = DiffusionPipeline.from_pretrained("cerspense/zeroscope_v2_576w", torch_dtype=torch.float16)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_model_cpu_offload()

prompt = "A lady is walking on the grasse."
video_frames = pipe(prompt, num_inference_steps=120, height=320, width=576, num_frames=24).frames
video_path = export_to_video(video_frames)
print(video_path)
