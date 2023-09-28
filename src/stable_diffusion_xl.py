from diffusers import DiffusionPipeline
import torch
import datetime

pipe = DiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipe.to("cuda")

# if using torch < 2.0
# pipe.enable_xformers_memory_efficient_attention()

prompt = "An astronaut riding a green horse"
negative_prompt = "nsfw,logo,text,badhandv4,EasyNegative,ng_deepnegative_v1_75t,rev2-badprompt,verybadimagenegative_v1.3,negative_hand-neg,mutated hands and fingers,poorly drawn face,extra limb,missing limb,disconnected limbs,malformed hands,ugly,FastNegativeV2,aid291,NegfeetV2"

images = pipe(prompt=prompt, negative_prompt=negative_prompt).images[0]
images
images.save("/data1/liuda/tmp/xl_{}_P0.png".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))
