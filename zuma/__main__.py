from pathlib import Path
import argparse
import toml
import shutil
import copy
from zuma.utils import prepare_serifu
from zuma.audio import AudioGenerator
from zuma.image import ImageGenerator
from zuma.movie import MovieGenerator


def _resolve(path_str, out_dir):
    # もしファイルパスにファイルがないなら最終生成物以下のファイルとみなします
    # (背景画像, 前景画像, BGM 用)
    if not path_str:
        return path_str
    if Path(path_str).is_file():
        return path_str
    return out_dir / path_str


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='台本ファイル (があるディレクトリ) のパス')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-i', '--image', action='store_true', help='画像のみ生成')
    group.add_argument('-a', '--audio', action='store_true', help='音声のみ生成')
    group.add_argument('-d', '--dryrun', action='store_true', help='何も生成しない')
    parser.add_argument('-r', '--refresh', choices=['0', '1', '2'], default='0', help=(
        '出力済み中間生成物を: 0.削除しない(デフォルト), '
        '1.現在の台本上必要な合成音声のみ残す, 2.全削除する',
    ))
    parser.add_argument('-n', '--n_shots', type=int, default=0, help='n 場面目まで生成')
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
    assert 'shot_default' in storyboard
    assert 'shots' in storyboard

    # 最終生成物、中間生成物用フォルダを作成します
    out_dir = storyboard.get('out_dir', '')
    storyboard['out_dir'] = Path(out_dir) if out_dir else p.parent
    storyboard['out_dir'].mkdir(exist_ok=True, parents=True)
    storyboard['out_dir_intermediate'] = storyboard['out_dir'] / 'intermediate'
    storyboard['out_dir_intermediate'].mkdir(exist_ok=True)

    # 立ち絵画像設定をキャラクター名をキーにした辞書にしておきます
    character_images = storyboard.get('character_images', [])
    storyboard['character_images'] = {c['name']: c for c in character_images}

    # (あれば) BGM のパスを解決しておきます
    if 'bgm_settings' in storyboard:
        mp3_path = storyboard['bgm_settings']['mp3_path']
        storyboard['bgm_settings']['mp3_path'] = _resolve(mp3_path, storyboard['out_dir'])

    # デフォルト場面に以下のキーがなければ設定しておきます
    storyboard['shot_default'].setdefault('front_imgs', [])
    storyboard['shot_default'].setdefault('characters', {})
    storyboard['shot_default'].setdefault('speaker', '')
    storyboard['shot_default'].setdefault('style', 'ノーマル')
    storyboard['shot_default'].setdefault('serifu', '')
    storyboard['shot_default'].setdefault('silence', 0)

    # (あれば) 前景画像のパスを解決しておきます
    storyboard.setdefault('front_images', {})
    for k, v in storyboard['front_images'].items():
        storyboard['front_images'][k]['path'] = _resolve(v['path'], storyboard['out_dir'])

    # 各場面はデフォルト場面との差分だけ指定してあるので完全にしておきます
    shots_ = []
    for i_shot, shot in enumerate(storyboard['shots']):
        shot_ = copy.deepcopy(storyboard['shot_default'].copy())
        shot_.update(shot)

        shot_['shot_id'] = f'{i_shot:04d}'
        # 背景画像のパスを解決しておきます
        shot_['back'] = _resolve(shot_['back'], storyboard['out_dir'])
        shot_['serifu_show'] = prepare_serifu(shot_['serifu'], flag='s')
        shot_['serifu_voice'] = prepare_serifu(shot_['serifu'], flag='v')
        shot_['image_files'] = [{
            'filename': shot_['shot_id'] + '_0.png', 'chara_imgs': {},
        }]
        for chara_name, face in shot_['characters'].items():
            character_image = storyboard['character_images'].get(chara_name)
            if (
                (not character_image)
                or (len(character_image['faces']) < face + 1)
                or (len(character_image['faces'][face]) == 0)
            ):
                print(f'[WARNING] 登場人物の立ち絵がないです (場面 {i_shot})')
                continue
            shot_['image_files'][0]['chara_imgs'][chara_name] = {
                'path': character_image['faces'][face][0],
                'coord': character_image['coord'],
                'scale': character_image['scale'],
            }
        if (shot_['serifu_voice'] != '') and (shot_['speaker'] in shot_['characters']):
            character_image = storyboard['character_images'].get(shot_['speaker'])
            face = shot_['characters'][shot_['speaker']]
            if len(character_image['faces'][face]) <= 1:
                print(f'[WARNING] 話者の開口画像がないです (場面 {i_shot})')
            else:
                shot_['image_files'].append({'filename': shot_['shot_id'] + '_1.png'})
                chara_imgs = copy.deepcopy(shot_['image_files'][0]['chara_imgs'])
                chara_imgs[shot_['speaker']]['path'] = character_image['faces'][face][1]
                shot_['image_files'][1]['chara_imgs'] = chara_imgs

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
