import argparse
import toml
import os
from funcs import generate_image, generate_mp3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='台本tomlファイルのパス')
    parser.add_argument('-s', '--adjust_screen', action='store_true', help='画面調整')
    args = parser.parse_args()

    # 台本読み込み
    with open(args.path, encoding='utf-8') as f:
        storyboard = toml.load(f)
    out_dir = storyboard['out_dir']
    out_dir_intermediate = out_dir + 'intermediate/'  # 中間生成物
    voice_settings = storyboard['voice_settings']
    character_images = {str(c['speaker']): c for c in storyboard['character_images']}
    text_settings = storyboard['text_settings']
    shot_default = storyboard['shot_default']
    shots = storyboard['shots']

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(out_dir_intermediate, exist_ok=True)

    # 画面調整のみする場合
    if args.adjust_screen:
        shot = shot_default.copy()
        shot['text'] = 'ああああああああああいいいいいいいいいい'
        shot['text'] += 'ううううううううううええええええええええ'
        generate_image(out_dir_intermediate, shot, character_images,
                       text_settings, regenerate=True)
        return

    # 各場面の台詞を wav に出力し全体を通した mp3 音声ファイルを出力しておく
    komas = generate_mp3(shot_default, shots, voice_settings, out_dir_intermediate)




if __name__ == '__main__':
    main()
