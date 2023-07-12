import hashlib
import math
import re


FPS = 24  # Seconds Per Frame
SPF = 1.0 / float(FPS)  # 0.125  # Frames Per Second
# SPF は各場面をフレーム単位に切り上げるためにつかう
# フレーム単位で口を開閉するのでそれにもつかう
# 各場面を 1 / 2^n 秒単位にしないとバグると思っていたが
# 1 / 24 でも OK だったので思い込みだったかもしれない
# 動画出力時に IndexError: list index out of range が出たら SPF を戻してみること
# https://github.com/Zulko/moviepy/issues/646

# セリフ音声を SPF で区切ったコマのうち音量が大きい何割で口を開くか
MOUTH_OPEN_RATIO = 0.5


def str_to_hash(s):
    return hashlib.md5(s.encode()).hexdigest()[:16]  # 長いので


def file_to_hash(file):
    with open(file, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()[:16]  # 長いので
    return md5


def list_to_str(li):
    return '_'.join([str(x) for x in li])


def dict_to_str(d):
    keys = sorted(d.keys())
    s = ''
    for key in keys:
        s += str(key) + str(d[key])
    return s


def format_duration(duration):
    sec = math.floor(duration)
    msec = int(1000 * (duration - sec))
    return f'00:00:{sec:02}.{msec:03}'


def prepare_serifu(serifu, flag='s'):  # s:字幕用, v:音声用
    """
    字幕用の文章と音声用の文章を微妙に変えたいときがあるので、
    字幕専用箇所を <s></s> で囲み、
    音声専用箇所を <v></v> で囲み、
    この関数で前処理することにする。

    例．聴かせてやるよ、<s>論理</s><v>ロジック</v>の<s>律動</s><v>リズム</v>を…
    → [字幕] 聴かせてやるよ、論理の律動を…
    → [音声] 聴かせてやるよ、ロジックのリズムを…

    音声用の場合は空白と改行も除去する。
    """
    if flag == 's':
        return re.sub('<v>.*?</v>|<s>|</s>', '', serifu)  # 字幕用
    return re.sub('<s>.*?</s>|<v>|</v>|\s|\n', '', serifu)  # 音声用


def get_image_filenames(out_dir_intermediate, shot, display_serifu):
    if shot['back_img'] != '':
        hash = file_to_hash(shot['back_img'])
    else:
        hash = list_to_str(shot['back_size'] + shot['back_color'])
    filebody = out_dir_intermediate
    filebody += hash + '_' + dict_to_str(shot['characters'])
    if display_serifu and shot['serifu'] != '':
        filebody += '_' + str(shot['speaker'])
        filebody += str_to_hash(prepare_serifu(shot['serifu'], flag='s'))
    if shot['free_text'] != '':
        filebody += '_' + str_to_hash(shot['free_text'])
    front_img = shot.get('front_img', '')
    if front_img != '':
        filebody += '_' + file_to_hash(front_img)
        filebody += '_' + list_to_str(shot['front_img_coordinate'])
    filenames = [filebody + '.png']
    serifu_ = prepare_serifu(shot['serifu'], flag='v')
    if serifu_ != '':  # 有声セリフがある場面には口開き版画像も必要
        speaker = shot['speaker']
        filenames.append(filebody + f'_{speaker}.png')
    return filenames


def get_wav_filename(out_dir_intermediate, voice_settings, shot):
    voice_setting = voice_settings.get(str(shot['speaker']))
    out_file = out_dir_intermediate + str(shot['speaker'])
    if voice_setting is not None:
        s = dict_to_str(voice_setting)
        s = s.replace('.', 'p')
        out_file += '_' + s
    out_file += '_' + str_to_hash(prepare_serifu(shot['serifu'], flag='v')) + '.wav'
    return out_file
