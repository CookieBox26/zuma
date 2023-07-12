from PIL import Image, ImageFont, ImageDraw
from funcs import get_image_filenames, prepare_serifu
from funcs.text import split_text
import os


class ImageGenerator:
    def __init__(self, storyboard):
        self.out_dir = storyboard['out_dir']
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        character_images = storyboard.get('character_images', [])
        self.character_images = {str(c['speaker']): c for c
                                 in storyboard['character_images']}
        self.serifu_text_settings = storyboard['serifu_text_settings']
        self.free_text_settings = storyboard.get('free_text_settings', {})
        self.shots = storyboard['shots']

    def _add_text(self, img, text, color, settings):
        font = ImageFont.truetype(settings['font_path'], settings['font_size'])
        draw = ImageDraw.Draw(img)
        if '\n' not in text:
            text = split_text(text, settings['width'],
                              settings.get('max_rows', 100))
        draw.multiline_text(
            settings['coordinate'], text, color,
            font=font, spacing=settings['spacing'],
            stroke_width=settings.get('stroke_width', 0),
            stroke_fill=settings.get('stroke_fill', 'black'))

    def _add_serifu_text(self, img, text, speaker):
        """ 背景画像にセリフテキスト (字幕) を貼り付けます
        """
        color = self.serifu_text_settings['font_color'].get(str(speaker))
        if color is None:
            color = self.serifu_text_settings['font_color_default']
        color = tuple(color)
        text_ = prepare_serifu(text, flag='s')
        self._add_text(img, text_, color, self.serifu_text_settings)

    def _add_free_text(self, img, text):
        """ 背景画像にフリーテキストを貼り付けます
        """
        color = tuple(self.free_text_settings['font_color'])
        self._add_text(img, text, color, self.free_text_settings)

    def _paste(self, img, additional_img_path, scale=1.0, coord=(0, 0)):
        img_ = Image.open(additional_img_path)
        img_ = img_.convert('RGBA')  # 念のため確実に RGBA にします
        size_new = (int(scale * img_.width), int(scale * img_.height))
        img_ = img_.resize(size_new)
        img.paste(img_, coord.copy(), img_)  # 座標はコピーしないと変更される

    def _paste_character(self, img, chara_id, mode, mouth=0):
        """ 背景画像に立ち絵を貼り付けます
        """
        character_image = self.character_images.get(chara_id)
        if character_image is None:
            print(f'[WARNING] ID:{chara_id} の立ち絵が設定されていません')
            return
        self._paste(img, character_image[mode][mouth],
                    character_image['scale'],
                    character_image['coordinate'])

    def _generate_back_image(self, shot):
        """ 背景画像を読み込むか生成します
        """
        if shot['back_img'] != '':
            return Image.open(shot['back_img']).convert('RGBA')
        else:
            return Image.new('RGBA', tuple(shot['back_size']),
                             tuple(shot['back_color']))

    def generate_shot(self, shot, regenerate=True):
        """ ある場面用の画像を合成します
        """
        # その場面で必要な画像ファイル名を取得します
        filenames = get_image_filenames(self.out_dir_intermediate, shot,
            self.serifu_text_settings['display'])
        for i_file, filename in enumerate(filenames):
            # 既にあればスキップします
            if (not regenerate) and os.path.isfile(filename):
                continue
            # 背景画像を読み込むか生成します
            img = self._generate_back_image(shot)
            # 前景画像があれば貼ります
            front_img = shot.get('front_img', '')
            if front_img != '':
                self._paste(img, front_img, coord=shot['front_img_coordinate'])
            # キャラクターがいれば立ち絵を貼ります
            for chara_id, mode in shot['characters'].items():
                mouth = 0
                if (i_file == 1) and (chara_id == str(shot['speaker'])):
                    mouth = 1
                self._paste_character(img, chara_id, mode, mouth)
            # セリフを表示する設定であってセリフがあれば貼ります
            if self.serifu_text_settings['display'] and shot['serifu'] != '':
                self._add_serifu_text(img, shot['serifu'], shot['speaker'])
            # フリーテキストがあれば貼ります
            if shot['free_text'] != '':
                self._add_free_text(img, shot['free_text'])
            img.save(filename)
        return filenames

    def generate(self, regenerate=True):
        """ 
        全場面用の画像を合成します
        ついでに便利用に合成した画像を一覧表示する images.html をかき出します
        """
        f = open(self.out_dir + 'images.html', mode='w')
        f.write(f'<html><head></head><body style="background: #ccc">\n')
        for i_shot, shot in enumerate(self.shots):
            filenames = self.generate_shot(shot, regenerate)
            f.write(f'<h4>{i_shot + 1}</h4>\n')
            filename = filenames[0].replace(self.out_dir_intermediate, '')
            f.write(f'<img src="intermediate/{filename}"/>\n')
        f.write(f'</br></br></br></body></html>\n')
        f.close()
