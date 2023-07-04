import requests
import json
from retry import retry
from pydub import AudioSegment
from funcs import SPK, get_wav_filename, prepare_serifu, file_to_hash
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
        komas = []  # 各場面の「有音コマ数、無音コマ数」を格納しておく
        audio_concat = None
        for shot in self.shots:
            komasu = 0
            silent_komasu = 0
            audio = None
            if shot['speaker'] > -1:  # 話者がいればセリフ音声を合成する
                out_file = get_wav_filename(self.out_dir_intermediate,
                                            self.voice_settings, shot)
                if not os.path.isfile(out_file):
                    print('未生成なので音声合成します: ',
                          shot['speaker'], shot['serifu'][:10])
                    serifu = prepare_serifu(shot['serifu'], flag='v')
                    synthesize(
                        serifu, out_file, speaker=shot['speaker'],
                        options=self.voice_settings.get(str(shot['speaker'])))
                else:
                    print('音声合成済みです: ', shot['speaker'], shot['serifu'][:10])
                audio = AudioSegment.from_wav(out_file)
                komasu = math.ceil(audio.duration_seconds / SPK)
                adjust_duration = komasu * SPK - audio.duration_seconds
                audio += AudioSegment.silent(duration=adjust_duration * 1000)
            if shot['silence'] > 0:  # セリフ後無音秒数があれば無音を足す
                silent_komasu = math.ceil(float(shot['silence']) / SPK)
                if audio is None:
                    audio = AudioSegment.silent(duration=silent_komasu * SPK * 1000)
                else:
                    audio += AudioSegment.silent(duration=silent_komasu * SPK * 1000)
            komas.append((komasu, silent_komasu))
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

        return mp3_file, komas
