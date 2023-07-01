import hashlib
from voicevox import synthesize
from pydub import AudioSegment
from PIL import Image, ImageFont, ImageDraw
from moviepy.editor import ImageClip, concatenate_videoclips
import math
import os


# moviepy に浮動小数バグがあるので 1/2^n 秒を時間の最小単位とする
# https://github.com/Zulko/moviepy/issues/646
SPK = 0.125  # Seconds Per Koma


def str_to_hash(s):
    return hashlib.md5(s.encode()).hexdigest()


def file_to_hash(file):
    with open(file, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()
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


def _add_text(img, text, text_settings):
    """ 背景画像に文字列を貼り付けます
    """
    font_size = text_settings['font_size']
    font_path = text_settings['font_path']
    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(img)
    coord = text_settings['coordinate']
    width = text_settings['width']
    if '<br/>' in text:
        text = text.split('<br/>')
        for row, text_ in enumerate(text):
            coord_ = (coord[0], coord[1] + row * int(font_size * 1.4))  # 行間 1.4
            draw.text(
                coord_, text_,
                tuple(text_settings['font_color']), font=font
            )
        return
    length = len(text)
    for row, i in enumerate(range(0, length, width)):
        coord_ = (coord[0], coord[1] + row * int(font_size * 1.4))  # 行間 1.4
        draw.text(
            coord_, text[i:(i + width)],
            tuple(text_settings['font_color']), font=font
        )


def _paste(img, chara_id, mode, character_images, mouse=0):
    """ 背景画像に立ち絵画像を貼り付けます
    """
    img_ = Image.open(character_images[chara_id][mode][mouse]).convert('RGBA')
    scale = character_images[chara_id]['scale']
    size_new = (int(scale * img_.width), int(scale * img_.height))
    img_ = img_.resize(size_new)
    w = character_images[chara_id]['coordinate'][0]
    h = character_images[chara_id]['coordinate'][1]
    img.paste(img_, character_images[chara_id]['coordinate'], img_)  #  (w, h)


def generate_image(out_dir, shot, character_images,
                   text_settings, regenerate=False):
    """ 必要な画像を合成します
    """
    back_img = shot['back_img']
    back_size = shot['back_size']
    back_color = shot['back_color']
    if back_img != '':
        hash = file_to_hash(back_img)
    else:
        hash = list_to_str(back_size + back_color)

    characters = shot['characters']
    text = shot['text']
    if text == '':
        text = shot['serifu']  # 暫定的にテキストがなければセリフを画像に記入する
    filebody = out_dir + hash + '_' + dict_to_str(characters)
    filebody += '_' + str_to_hash(text)

    speakers = [-1]
    if shot['speaker'] > -1:  # 話者がいれば口開き版も必要なため2枚合成する
        speakers.append(shot['speaker'])
    out_files = []
    for speaker in speakers:
        postfix = '' if (speaker == -1) else ('_' + str(speaker))
        out_file = filebody + postfix + '.png'
        if (not regenerate) and os.path.isfile(out_file):
            out_files.append(out_file)
            continue
        if back_img != '':
            img = Image.open(back_img).convert('RGBA')
        else:
            img = Image.new('RGBA', tuple(back_size), tuple(back_color))
        for chara_id, mode in characters.items():
            mouse = 1 if (chara_id == str(speaker)) else 0
            _paste(img, chara_id, mode, character_images, mouse)
        if text != '':
            _add_text(img, text, text_settings)
        img.save(out_file)
        out_files.append(out_file)
    return out_files


def generate_mp3(shot_default, shots, voice_settings, out_dir_intermediate):
    # 各場面の台詞を wav に出力し全体を通した mp3 音声ファイルを出力しておく
    komas = []  # 各場面の「有音コマ数、無音コマ数」を格納しておく
    audio_concat = None
    for shot_ in shots:
        shot = shot_default.copy()
        shot.update(shot_)
        komasu = 0
        silent_komasu = 0
        audio = None
        if shot['speaker'] > -1:  # 話者がいればセリフ音声を合成する
            out_file = out_dir_intermediate + str(shot['speaker'])
            out_file += '_' + shot['serifu'][:3] + '_'
            out_file += str_to_hash(shot['serifu']) + '.wav'
            if not os.path.isfile(out_file):
                synthesize(shot['serifu'], out_file, speaker=shot['speaker'],
                           options=voice_settings.get(str(shot['speaker'])))
            audio = AudioSegment.from_wav(out_file)
            komasu = math.ceil(audio.duration_seconds / SPK)
            minisilence_duration = komasu * SPK - audio.duration_seconds
            audio += AudioSegment.silent(duration=minisilence_duration * 1000)
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
    audio_concat.export(f'{out_dir_intermediate}concat.mp3', format='mp3')
    return komas
