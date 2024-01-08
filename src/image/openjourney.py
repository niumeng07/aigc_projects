from diffusers import StableDiffusionPipeline
import torch
import datetime
from diffusers import LMSDiscreteScheduler

def test_model_openjourney():
    model_id = "prompthero/openjourney"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda")

    prompt = "8k, best quality, masterpiece, realistic, photo-realistic, ultra-detailed, 1girl,cute,beautiful detailed sky,outdoors,night,standing, dating,nose blush,smile,closed mouth, large breasts,beautiful detailed eyes, wet,rain,white lace, long hair,floating hair NovaFrogStyle, looking at viewer, full body, facing viewer, skirt, mix4, twintails, pale skin, red lips, hair flower,"
    negative_prompt = "paintings, sketches, worst quality,low quality, normal quality, lowres, normal quality,monochrom, grayscale, skin spots, acnes, skin blemishes, age spot, manboobs, backlight,ugly, duplicate, morbid, mutilated, tranny, mutated hands, poorly drawn hands, blurry, bad anatomy, bad proportions, extra limbs, disfigured, more than 2 nipples, missing arms, extra legs, fused fingers, too many fingers, unclear eyes, bad hands, missing fingers, extra digit, futa, bad body,pubic hair, glans, 1boy,"

    num_images_per_prompt = 3
    image = pipe(prompt, negative_prompt=negative_prompt, num_inference_steps=50,
                 height=512, width=512, num_images_per_prompt=num_images_per_prompt)

    for idx in range(num_images_per_prompt):
        image[0][idx].save("/data1/liuda/{}_P{}.png".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), idx))


def test_model_openjourney_v4():
    # error model id
    model_id = "prompthero/openjourney-v4"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda")

    prompt = "8k, best quality, blue background, 23 year old girl"
    negative_prompt = "girl full of image"

    num_images_per_prompt = 1
    image = pipe(prompt, negative_prompt=negative_prompt, num_inference_steps=50,
                 height=512, width=512, num_images_per_prompt=num_images_per_prompt)

    for idx in range(num_images_per_prompt):
        image[0][idx].save("/data1/liuda/tmp2/{}_P{}.png".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), idx))


# test_model_openjourney_v4()

def test_image2image():
    import torch
    import requests
    from PIL import Image
    from io import BytesIO
    from diffusers import StableDiffusionImg2ImgPipeline

    device = "cuda"
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained("nitrosocke/Ghibli-Diffusion", torch_dtype=torch.float16).to(
        device
    )

    url = "https://gitlab.ushareit.me/liuda/tmp/-/raw/master/762733bc437207d2c0e89a92c76cc017.png"

    # response = requests.get(url)
    print('open init image')
    init_image = Image.open("/data1/liuda/tmp2/762733bc437207d2c0e89a92c76cc017.png").convert("RGB")
    init_image.thumbnail((768, 768))
    init_image
    print('open init image success')

    lms = LMSDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.scheduler = lms
    generator = torch.Generator(device=device).manual_seed(1024)
    prompt = "rewrite the woman to chinese 25 year old, with gold rings, earrings, necklaces"
    image = pipe(prompt=prompt, image=init_image, strength=0.25, guidance_scale=7.5, generator=generator).images[0]
    image
    image.save("/data1/liuda/tmp2/{}_P0.png".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))


test_image2image()
