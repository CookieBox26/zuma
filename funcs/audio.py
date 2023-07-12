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
        """各場面の台詞を wav に出力し全体を通した音声ファイルを出力しておきます
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
                n_frames = math.ceil(audio.duration_seconds / SPF)
                adjust_duration = n_frames * SPF - audio.duration_seconds
                audio += AudioSegment.silent(duration=adjust_duration * 1000)

                # 口の開閉指示
                fix = 2  # フレームごとに開閉すると細かいので 2 倍する (フレームレートによる)
                volumes = []  # セグメントごとの平均音量を記録する
                for i_frame in range(0, n_frames, fix):
                    seg = audio[(i_frame * SPF * 1000):((i_frame + fix) * SPF * 1000)]
                    volumes.append(seg.rms)
                # Xパーセンタイル点を閾値として口を開くか閉じるかにする
                n = len(volumes)
                threshold = list(reversed(sorted(volumes)))[int(MOUTH_OPEN_RATIO * n)]
                last_mouth = -1
                for i_block, i_frame in enumerate(range(0, n_frames, fix)):
                    if i_frame + fix - 1 < n_frames:
                        duration = fix * SPF
                    else:
                        duration = (n_frames - i_frame) * SPF
                    mouth = 1 if (volumes[i_block] > threshold) else 0
                    if mouth != last_mouth:  # 開き (閉じ) が変化したとき
                        voice_durations.append((mouth, duration))
                    else:  # 開き (閉じ) が変化していないときは継続時間だけのばす
                        last = voice_durations.pop(-1)
                        voice_durations.append((mouth, last[1] + duration))
                    last_mouth = mouth

            if shot['silence'] > 0:  # セリフ後無音秒数があれば無音を足す
                silent_frames = math.ceil(float(shot['silence']) / SPF)
                silent_duration = silent_frames * SPF
                if audio is None:
                    audio = AudioSegment.silent(duration=silent_duration * 1000)
                else:
                    audio += AudioSegment.silent(duration=silent_duration * 1000)
            durations.append((voice_durations, silent_duration))
            if audio_concat is None:
                audio_concat = audio
            else:
                audio_concat += audio

        # 全場面の音声をエクスポートするが
        # 音声圧縮方式は mp3 (拡張子 m4a) ではなく aac (拡張子 m4a) にする
        # mp3 にエクスポートしても動画はできるが iPhone から再生できないためである
        audio_file = f'{self.out_dir_intermediate}concat.m4a'
        audio_concat.export(audio_file, format='ipod', codec='aac')

        if self.bgm_file != '':
            audio = AudioSegment.from_file(audio_file, 'm4a')
            bgm = AudioSegment.from_mp3(self.bgm_file) + self.bgm_adjust
            audio = audio.overlay(bgm)
            audio_file_with_bgm = f'{self.out_dir_intermediate}' \
                + f'concat_{file_to_hash(self.bgm_file)}' \
                + f'_{str(self.bgm_adjust)}.m4a'
            audio.export(audio_file_with_bgm, format='ipod', codec='aac')
            audio_file = audio_file_with_bgm

        return audio_file, durations
