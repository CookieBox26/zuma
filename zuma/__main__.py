from pathlib import Path
import argparse
import toml
import shutil
import copy
from zuma.audio import AudioGenerator
from zuma.image import ImageGenerator
from zuma.movie import MovieGenerator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='台本ファイル (があるディレクトリ) のパス')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--image', action='store_true', help='画像のみ生成')
    group.add_argument('--audio', action='store_true', help='音声のみ生成')
    group.add_argument('--dryrun', action='store_true', help='何も生成しない')
    parser.add_argument('-r', '--refresh', choices=['0', '1', '2'], default='0', help=(
        '出力済み中間生成物を: 0.削除しない(デフォルト), '
        '1.現在の台本上必要な合成音声のみ残す, 2.全削除する',
    ))
    parser.add_argument('-n', '--n_shots', type=int, default=0, help='n 場面目までのみ生成')
    args = parser.parse_args()
    refresh = int(args.refresh)
    gen_image, gen_audio, gen_movie = True, True, True
    if args.image:
        gen_audio, gen_movie = False, False
    if args.audio:
        gen_image, gen_movie = False, False
    if args.dryrun:
        gen_image, gen_audio, gen_movie = False, False, False
    n_shots = args.n_shots

    # 台本tomlファイルを読み込みます
    p = Path(args.path)
    if p.is_dir():
        p = p / 'storyboard.toml'
    storyboard = toml.loads(p.read_text(encoding='utf8'))

    # 最終生成物、中間生成物用フォルダを作成します
    out_dir = storyboard.get('out_dir', '')
    storyboard['out_dir'] = Path(out_dir) if out_dir else p.parent
    storyboard['out_dir'].mkdir(exist_ok=True, parents=True)
    storyboard['out_dir_intermediate'] = storyboard['out_dir'] / 'intermediate'
    storyboard['out_dir_intermediate'].mkdir(exist_ok=True)

    # 立ち絵画像設定をスタイル ID をキーにした辞書にしておきます
    storyboard['character_images'] = {
        str(c['speaker']): c for c in storyboard['character_images']
    }

    # 各場面はデフォルトとの差分だけ指定してあるので完全にしておきます
    shots_ = []
    for i_shot, shot in enumerate(storyboard['shots']):
        shot_ = copy.deepcopy(storyboard['shot_default'].copy())
        shot_.update(shot)
        # 後方互換性のための処理
        if ('front_img_paths' not in shot_) and ('front_img' in shot_):
            shot_['front_img_paths'] = [shot_['front_img']]
            shot_['front_img_coordinates'] = [shot_['front_img_coordinate']]
            del shot_['front_img'], shot_['front_img_coordinate']
        shots_.append(shot_)
        if i_shot + 1 == n_shots:
            break
    storyboard['shots'] = shots_

    # 各ジェネレータを用意します
    ig = ImageGenerator(storyboard)
    ag = AudioGenerator(storyboard)
    mg = MovieGenerator(storyboard)

    if refresh == 1:  # 不要な中間生成物を削除します
        print('中間生成物を削除します (現在の台本上必要な合成音声は保持)')
        required_wav_files = ag.get_required_wav_files()
        for intermediate in storyboard['out_dir_intermediate'].glob('*'):
            if intermediate.suffix not in ['.png', '.wav', '.m4a', '.toml']:
                continue
            if intermediate.name in required_wav_files:
                continue
            intermediate.unlink()
    elif refresh == 2:  # 中間生成物を全削除します
        print('中間生成物を全削除します')
        shutil.rmtree(storyboard['out_dir_intermediate'])
        storyboard['out_dir_intermediate'].mkdir(exist_ok=True)

    # 各場面で必要な画像を合成し出力します
    if gen_image:
        ig.generate()

    # 各場面の台詞 wav を生成し全体を通した音声ファイルを出力します
    if gen_audio:
        ag.generate()

    # 動画を生成します
    if gen_movie:
        mg.generate()


if __name__ == '__main__':
    main()
