FROM ubuntu:22.04

WORKDIR /content

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=True
ENV PATH="/root/.local/bin:${PATH}"

RUN apt update -y && apt install -y software-properties-common build-essential \
    libgl1 libglib2.0-0 zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev && \
    add-apt-repository -y ppa:git-core/ppa && apt update -y && \
    apt install -y python-is-python3 python3-pip nano aria2 curl wget git git-lfs unzip unrar ffmpeg && \
    git clone https://github.com/aristocratos/btop /content/btop && cd /content/btop && make && make install && \
    chmod -R 777 /content

RUN \
    pip install torch==2.5.1+cu124 \
        torchvision==0.20.1+cu124 \
        torchaudio==2.5.1+cu124 \
        torchtext==0.18.0 torchdata==0.8.0 \
    --extra-index-url https://download.pytorch.org/whl/cu124 \
    && \
    pip install xformers==0.0.28.post3 && \
    pip install opencv-python imageio imageio-ffmpeg ffmpeg-python \
                torchsde diffusers accelerate peft timm scikit-image matplotlib && \
    pip install numpy==1.25.0 einops \
                transformers==4.28.1 \
                tokenizers==0.13.3 \
                sentencepiece aiohttp==3.11.8 \
                yarl==1.18.0 pyyaml Pillow scipy \
                tqdm psutil kornia==0.7.1 \
                spandrel soundfile av

WORKDIR /content/ComfyUI
CMD /bin/bash
