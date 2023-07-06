import argparse
import toml
import os
import glob
import shutil
from funcs.audio import AudioGenerator
from funcs.image import ImageGenerator
from funcs.movie import MovieGenerator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='台本tomlファイルのパス')
    parser.add_argument(
        '-m', '--mode', choices=['0', '1', '2', '3'], default='3',
        help='何を生成するか指定する: ' \
             + '0.何も生成しない, 1.画像のみ, 2.音声のみ, 3.動画(デフォルト)')
    parser.add_argument(
        '-r', '--refresh', choices=['0', '1', '2'], default='0',
        help='出力済み中間生成物を: 0.削除しない(デフォルト), ' \
             + '1.現在の台本上必要な合成音声のみ残す, 2.全削除する')
    args = parser.parse_args()
    mode = int(args.mode)
    refresh = int(args.refresh)

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

    # 各場面はデフォルトとの差分だけ指定してあるので完全にしておきます
    shots_ = []
    for shot in storyboard['shots']:
        shot_ = storyboard['shot_default'].copy()
        shot_.update(shot)
        shots_.append(shot_)
    storyboard['shots'] = shots_

    # 各ジェネレータを用意します
    ig = ImageGenerator(storyboard)
    ag = AudioGenerator(storyboard)
    mg = MovieGenerator(storyboard)

    if refresh == 1:  # 不要な中間生成物を削除する場合は削除します
        required_wav_files = ag.get_required_wav_files()
        intermediates = glob.glob(out_dir_intermediate + '*')
        for intermediate_ in intermediates:
            intermediate = intermediate_.replace('\\', '/')  # for win
            _, ext = os.path.splitext(intermediate)
            if intermediate in required_wav_files:
                continue
            if ext not in ['.png', '.wav', '.mp3']:
                continue
            os.remove(intermediate)
    elif refresh == 2:  # 中間生成物を全削除する場合は全削除します
        shutil.rmtree(out_dir_intermediate)
        os.makedirs(out_dir_intermediate, exist_ok=True)

    # 各場面で必要な画像を合成し出力します
    if mode in [1, 3]:
        ig.generate()

    # 各場面の台詞 wav を生成し全体を通した mp3 を出力します
    if mode in [2, 3]:
        mp3_file, durations = ag.generate()

    # 動画を生成します
    if mode == 3:
        mg.generate(durations, mp3_file)


if __name__ == '__main__':
    main()
