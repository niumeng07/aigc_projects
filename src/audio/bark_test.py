from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
from IPython.display import Audio

# download and load all models
preload_models()

# generate audio from text
text_prompt = open('/data1/liuda/tmp/input/庆余年.mini.txt').readlines()[0:3]
text_prompt = '。'.join(text_prompt)
# print(text_prompt)
# audio_array = generate_audio(text_prompt, history_prompt='v2/en_speaker_1')
audio_array = generate_audio(text_prompt, history_prompt='v2/zh_speaker_1')

# save audio to disk
write_wav("/data1/liuda/tmp/output/audio/qingyunian.mini.wav", SAMPLE_RATE, audio_array)
  
# play text in notebook
Audio(audio_array, rate=SAMPLE_RATE)
