import argparse
import toml
import os
import shutil
from funcs.audio import AudioGenerator
from funcs.image import ImageGenerator
from funcs.movie import MovieGenerator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='台本tomlファイルのパス')
    parser.add_argument('-s', '--adjust_screen', action='store_true', help='画面調整のみ')
    parser.add_argument('-r', '--refresh', action='store_true', help='中間生成物削除のみ')
    args = parser.parse_args()

    # 台本tomlファイルを読み込みます
    with open(args.path, encoding='utf-8') as f:
        storyboard = toml.load(f)
    out_dir = storyboard['out_dir']
    if out_dir == '':  # 出力パスが空文字列の場合台本ファイルがあるパスにする
        out_dir = os.path.dirname(args.path) + '/'
        storyboard['out_dir'] = out_dir
    out_dir_intermediate = out_dir + 'intermediate/'  # 中間生成物用
    storyboard['out_dir_intermediate'] = out_dir_intermediate

    # 最終生成物、中間生成物用フォルダを作成します
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(out_dir_intermediate, exist_ok=True)

    # 各ジェネレータを用意します
    ag = AudioGenerator(storyboard)
    ig = ImageGenerator(storyboard)
    mg = MovieGenerator(storyboard, ig)

    # 中間生成物削除のみする場合
    if args.refresh:
        shutil.rmtree(out_dir_intermediate)
        return

    # 画面調整のみする場合
    if args.adjust_screen:
        # デフォルト場面に長い文字列を入れて横に何文字入るか調整する
        shot = storyboard['shot_default'].copy()
        shot['text'] = 'ああああああああああいいいいいいいいいい'
        shot['text'] += 'ううううううううううええええええええええ'
        ig.generate(shot, regenerate=True)
        return

    shots_ = []
    for shot in storyboard['shots']:
        shot_ = storyboard['shot_default'].copy()
        shot_.update(shot)
        shots_.append(shot_)
    storyboard['shots'] = shots_

    # 各場面の台詞 wav を生成し全体を通した mp3 を出力しておきます
    mp3_file, komas = ag.generate(storyboard['shots'])

    # 動画を生成します
    mg.generate(komas, storyboard['shots'], mp3_file)


if __name__ == '__main__':
    main()
