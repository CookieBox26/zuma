import requests
import json
from pathlib import Path
from retry import retry
from pydub import AudioSegment
from zuma.utils import (
    SPF, MOUTH_OPEN_RATIO,
    str_to_hash, dict_to_str, file_to_hash,
)
import math
import toml


@retry(tries=3, delay=1)
def get_speakers(cache_file='speakers.json'):
    r = requests.get("http://localhost:50021/speakers")
    r.raise_for_status()
    return r.json()


@retry(tries=3, delay=1)
def get_audio_query(text, speaker_id):
    r = requests.post(
        "http://localhost:50021/audio_query",
        params={"text": text, "speaker": speaker_id},
        timeout=(10.0, 300.0),
    )
    r.raise_for_status()
    return r.json()


@retry(tries=3, delay=1)
def audio_query_to_wav(query_data, speaker_id, filename):
    r = requests.post(
        "http://localhost:50021/synthesis",
        data=json.dumps(query_data),
        params={"speaker": speaker_id},
        timeout=(10.0, 300.0),
    )
    r.raise_for_status()
    with open(filename, "wb") as fp:
        fp.write(r.content)


def synthesize(text, filename, speaker_id=3, options=None):
    query_data = get_audio_query(text, speaker_id)
    if options is not None:
        query_data.update(options)
    audio_query_to_wav(query_data, speaker_id, filename)


class AudioGenerator:
    def __init__(self, storyboard, speaker_ids_cache_file='speaker_ids.toml'):
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        self.shots = storyboard['shots']
        self.speaker_ids = {}
        speaker_ids_cache_path = Path(speaker_ids_cache_file)
        if speaker_ids_cache_path.is_file():
            self.speaker_ids = toml.loads(
                speaker_ids_cache_path.read_text(encoding='utf8'),
            )
        else:
            speakers = get_speakers()
            for speaker in speakers:
                speaker_name = speaker['name']
                for style in speaker['styles']:
                    style_name = style['name']
                    self.speaker_ids[f'{speaker_name}:{style_name}'] = style['id']
            speaker_ids_cache_path.write_text(
                toml.dumps(self.speaker_ids), newline='\n', encoding='utf8',
            )

        self.voice_settings = {}
        if 'voice_settings' in storyboard:
            self.voice_settings = {
                s['speaker_style']: s['options'] for s in storyboard['voice_settings']
            }
        self.bgm_file = ''
        self.bgm_adjust = 0
        if 'bgm_settings' in storyboard:
            self.bgm_file = storyboard['bgm_settings']['mp3_path']
            self.bgm_adjust = storyboard['bgm_settings']['adjust']

    def get_wav_filename(self, shot):
        speaker_style = shot['speaker'] + ':' + shot['style']
        speaker_id = self.speaker_ids[speaker_style]
        voice_setting = self.voice_settings.get(speaker_style)
        out_file = str(speaker_id)
        if voice_setting is not None:
            s = dict_to_str(voice_setting)
            s = s.replace('.', 'p')
            out_file += '_' + s
        out_file += '_' + str_to_hash(shot['serifu_voice']) + '.wav'
        return out_file

    def get_required_wav_files(self):
        wav_files = []
        for shot in self.shots:
            speaker = shot.get('speaker')
            if not speaker:
                continue
            wav_files.append(self.get_wav_filename(shot))
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
            serifu = shot['serifu_voice']
            speaker_style = shot['speaker'] + ':' + shot['style']
            speaker_id = self.speaker_ids.get(speaker_style, -1)

            # セリフがあればセリフ音声を合成する
            if serifu != '':
                wav_filename = self.get_wav_filename(shot)
                out_file = self.out_dir_intermediate / wav_filename
                if not out_file.is_file():
                    print('未生成なので音声合成します: ', speaker_id, serifu[:10])
                    synthesize(
                        serifu, out_file, speaker_id=speaker_id,
                        options=self.voice_settings.get(speaker_style),
                    )
                else:
                    print('音声合成済みです: ', speaker_id, shot['serifu'][:10])

                audio = AudioSegment.from_wav(out_file)
                n_frames = math.ceil(audio.duration_seconds / SPF)
                adjust_duration = n_frames * SPF - audio.duration_seconds
                audio += AudioSegment.silent(duration=adjust_duration * 1000)

                # 口の開閉指示
                fix = 4  # フレームごとに開閉すると細かいので 4 倍する (フレームレートによる)
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
                        duration = fix
                    else:
                        duration = n_frames - i_frame
                    mouth = 1 if (volumes[i_block] > threshold) else 0
                    if mouth != last_mouth:  # 開き (閉じ) が変化したとき
                        voice_durations.append([mouth, duration])
                    else:  # 開き (閉じ) が変化していないときは継続時間だけのばす
                        last = voice_durations.pop(-1)
                        voice_durations.append([mouth, last[1] + duration])
                    last_mouth = mouth

            if shot['silence'] > 0:  # セリフ後無音秒数があれば無音を足す
                silent_frames = math.ceil(float(shot['silence']) / SPF)
                silent_duration = silent_frames
                if audio is None:
                    audio = AudioSegment.silent(duration=silent_duration * SPF * 1000)
                else:
                    audio += AudioSegment.silent(duration=silent_duration * SPF * 1000)

            durations.append({
                'voice_durations': voice_durations,
                'silent_duration': silent_duration,
            })
            if audio_concat is None:
                audio_concat = audio
            else:
                audio_concat += audio
        (self.out_dir_intermediate / 'duration.toml').write_text(
            toml.dumps({'durations': durations}), newline='\n', encoding='utf8',
        )

        # 全場面の音声をエクスポートするが
        # 音声圧縮方式は mp3 (拡張子 m4a) ではなく aac (拡張子 m4a) にする
        # mp3 にエクスポートしても動画はできるが iPhone から再生できないためである
        audio_file = self.out_dir_intermediate / 'concat.m4a'
        audio_concat.export(audio_file, format='ipod', codec='aac')

        if self.bgm_file != '':
            audio = AudioSegment.from_file(audio_file, 'm4a')
            bgm = AudioSegment.from_mp3(self.bgm_file) + self.bgm_adjust
            audio = audio.overlay(bgm)
            audio.export(audio_file, format='ipod', codec='aac')
