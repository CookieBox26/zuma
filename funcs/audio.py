import requests
import json
from retry import retry
from pydub import AudioSegment
from funcs import SPF, MOUTH_OPEN_RATIO, \
    get_wav_filename, prepare_serifu, file_to_hash
import os
import math


@retry(tries=3, delay=1)
def get_audio_query(text, speaker):
    r = requests.post("http://localhost:50021/audio_query", 
                      params={"text": text, "speaker": speaker},
                      timeout=(10.0, 300.0))
    r.raise_for_status()
    return r.json()


@retry(tries=3, delay=1)
def audio_query_to_wav(query_data, speaker, filename):
    r = requests.post("http://localhost:50021/synthesis",
                      data=json.dumps(query_data),
                      params={"speaker": speaker},
                      timeout=(10.0, 300.0))
    r.raise_for_status()
    with open(filename, "wb") as fp:
                fp.write(r.content)


def synthesize(text, filename, speaker=1, options=None):
    query_data = get_audio_query(text, speaker)
    if options is not None:
        query_data.update(options)
    audio_query_to_wav(query_data, speaker, filename)


class AudioGenerator:
    def __init__(self, storyboard):
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        self.voice_settings = {}
        if 'voice_settings' in storyboard:
            self.voice_settings = storyboard['voice_settings']
        self.bgm_file = ''
        self.bgm_adjust = 0
        if 'bgm_settings' in storyboard:
            self.bgm_file = storyboard['bgm_settings']['mp3_path']
            self.bgm_adjust = storyboard['bgm_settings']['adjust']
        self.shots = storyboard['shots']

    def get_required_wav_files(self):
        wav_files = []
        for shot in self.shots:
            if shot['speaker'] == -1:
                continue
            wav_files.append(get_wav_filename(self.out_dir_intermediate,
                                              self.voice_settings, shot))
        return wav_files

    def generate(self):
        """各場面の台詞を wav に出力し全体を通した mp3 を出力しておきます
        """
        durations = []
        audio_concat = None
        for shot in self.shots:
            voice_durations = []
            silent_duration = 0
            audio = None
            serifu_ = prepare_serifu(shot['serifu'], flag='v')

            # セリフがあればセリフ音声を合成する
            # ※ 字幕と音声を変えることに対応したので、
            #    話者があり字幕があっても無声な場面がありうるので話者では判定しない
            if serifu_ != '':
                out_file = get_wav_filename(self.out_dir_intermediate,
                                            self.voice_settings, shot)
                if not os.path.isfile(out_file):
                    print('未生成なので音声合成します: ',
                          shot['speaker'], serifu_[:10])
                    synthesize(
                        serifu_, out_file, speaker=shot['speaker'],
                        options=self.voice_settings.get(str(shot['speaker'])))
                else:
                    print('音声合成済みです: ', shot['speaker'], shot['serifu'][:10])
                audio = AudioSegment.from_wav(out_file)
                komasu_ = math.ceil(audio.duration_seconds / SPF)
                adjust_duration = komasu_ * SPF - audio.duration_seconds
                audio += AudioSegment.silent(duration=adjust_duration * 1000)

                volumes = []
                for i_koma in range(komasu_):
                    seg = audio[(i_koma * SPF * 1000):((i_koma + 1) * SPF * 1000)]
                    volumes.append(seg.rms)
                threshold = list(reversed(sorted(volumes)))[int(MOUTH_OPEN_RATIO * komasu_)]
                last_mouth = -1
                for i_koma in range(komasu_):
                    mouth = 1 if (volumes[i_koma] > threshold) else 0
                    if mouth != last_mouth:
                        voice_durations.append((mouth, SPF))
                    else:
                        last = voice_durations.pop(-1)
                        voice_durations.append((mouth, last[1] + SPF))
                    last_mouth = mouth

            if shot['silence'] > 0:  # セリフ後無音秒数があれば無音を足す
                silent_komasu = math.ceil(float(shot['silence']) / SPF)
                silent_duration = silent_komasu * SPF
                if audio is None:
                    audio = AudioSegment.silent(duration=silent_duration * 1000)
                else:
                    audio += AudioSegment.silent(duration=silent_duration * 1000)
            durations.append((voice_durations, silent_duration))
            if audio_concat is None:
                audio_concat = audio
            else:
                audio_concat += audio

        mp3_file = f'{self.out_dir_intermediate}concat.mp3'
        audio_concat.export(mp3_file, format='mp3')

        if self.bgm_file != '':
            audio = AudioSegment.from_mp3(mp3_file)
            bgm = AudioSegment.from_mp3(self.bgm_file) + self.bgm_adjust
            audio = audio.overlay(bgm)
            mp3_file_with_bgm = f'{self.out_dir_intermediate}' \
                + f'concat_{file_to_hash(self.bgm_file)}' \
                + f'_{str(self.bgm_adjust)}.mp3'
            audio.export(mp3_file_with_bgm, format='mp3')
            mp3_file = mp3_file_with_bgm

        return mp3_file, durations
