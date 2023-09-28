from diffusers import DiffusionPipeline
import torch
import datetime

pipe = DiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

# if using torch < 2.0
# pipe.enable_xformers_memory_efficient_attention()

prompt = "An astronaut riding a green horse"

images = pipe(prompt=prompt).images[0]
images
images.save("/data1/liuda/tmp/xl_{}_P0.png".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))
