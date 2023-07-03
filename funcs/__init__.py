import hashlib
import math


# moviepy に浮動小数バグがあるので 1/2^n 秒を時間の最小単位とする
# https://github.com/Zulko/moviepy/issues/646
SPK = 0.125  # Seconds Per Koma


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


def get_image_filenames(out_dir_intermediate, shot, display_serifu):
    if shot['back_img'] != '':
        hash = file_to_hash(shot['back_img'])
    else:
        hash = list_to_str(shot['back_size'] + shot['back_color'])
    filebody = out_dir_intermediate
    filebody += hash + '_' + dict_to_str(shot['characters'])
    if display_serifu and shot['serifu'] != '':
        filebody += '_' + str(shot['speaker'])
        filebody += str_to_hash(shot['serifu'])
    if shot['free_text'] != '':
        filebody += '_' + str_to_hash(shot['free_text'])
    front_img = shot.get('front_img', '')
    if front_img != '':
        filebody += '_' + file_to_hash(front_img)
        filebody += '_' + list_to_str(shot['front_img_coordinate'])
    filenames = [(-1, filebody + '.png')]
    speaker = shot['speaker']
    if speaker > -1:  # 話者がいる場面にいは口開き版画像も必要
        filenames.append((speaker, filebody + f'_{speaker}.png'))
    return filenames


def get_wav_filename(out_dir_intermediate, voice_settings, shot):
    voice_setting = voice_settings.get(str(shot['speaker']))
    out_file = out_dir_intermediate + str(shot['speaker'])
    if voice_setting is not None:
        s = dict_to_str(voice_setting)
        s = s.replace('.', 'p')
        out_file += '_' + s
    out_file += '_' + str_to_hash(shot['serifu']) + '.wav'
    return out_file
