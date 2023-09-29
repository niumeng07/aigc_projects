from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

output_dir = '/data1/liuda/tmp/output/'
text = '这是待合成文本范例'
text = open('qingyunian.txt').readlines()
text = '\n'.join(text)
model_id = 'damo/speech_sambert-hifigan_tts_zh-cn_16k'
sambert_hifigan_tts = pipeline(task=Tasks.text_to_speech, model=model_id)
output = sambert_hifigan_tts(input=text, voice='zhitian_emo')
wav = output[OutputKeys.OUTPUT_WAV]
with open('{}/audio/qingyunian2.wav'.format(output_dir), 'wb') as f:
    f.write(wav)
