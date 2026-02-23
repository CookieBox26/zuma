import hashlib
import math
import re


FPS = 32  # Seconds Per Frame
SPF = 1.0 / float(FPS)  # Frames Per Second
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
    return re.sub('<s>.*?</s>|<v>|</v>| |\n', '', serifu)  # 音声用
