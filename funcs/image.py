from PIL import Image, ImageFont, ImageDraw
from funcs import get_image_filenames
import os


class ImageGenerator:
    def __init__(self, storyboard):
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        self.character_images = {str(c['speaker']): c for c
                                 in storyboard['character_images']}
        self.serifu_text_settings = storyboard['serifu_text_settings']
        self.free_text_settings = storyboard['free_text_settings']

    def _add_text(self, img, text, coord, size, font_path, color, width):
        font = ImageFont.truetype(font_path, size)
        draw = ImageDraw.Draw(img)
        if '<br/>' in text:
            text = text.split('<br/>')
            for row, text_ in enumerate(text):
                coord_ = (coord[0], coord[1] + row * int(size * 1.4))
                draw.text(coord_, text_, color, font=font)
            return
        length = len(text)
        for row, i in enumerate(range(0, length, width)):
            coord_ = (coord[0], coord[1] + row * int(size * 1.4))
            draw.text(coord_, text[i:(i + width)], color, font=font)

    def _add_serifu_text(self, img, text, speaker):
        """ 背景画像にセリフテキスト (字幕) を貼り付けます
        """
        coord = self.serifu_text_settings['coordinate']
        size = self.serifu_text_settings['font_size']
        font_path = self.serifu_text_settings['font_path']
        color = tuple(self.serifu_text_settings['font_color'][str(speaker)])
        width = self.serifu_text_settings['width']
        self._add_text(img, text, coord, size, font_path, color, width)

    def _add_free_text(self, img, text):
        """ 背景画像にフリーテキストを貼り付けます
        """
        coord = self.free_text_settings['coordinate']
        size = self.free_text_settings['font_size']
        font_path = self.free_text_settings['font_path']
        color = tuple(self.free_text_settings['font_color'])
        width = self.free_text_settings['width']
        self._add_text(img, text, coord, size, font_path, color, width)

    def _paste(self, img, additional_img_path, scale=1.0, coord=(0, 0)):
        img_ = Image.open(additional_img_path)
        img_ = img_.convert('RGBA')  # 念のため確実に RGBA にします
        size_new = (int(scale * img_.width), int(scale * img_.height))
        img_ = img_.resize(size_new)
        img.paste(img_, coord, img_)

    def _paste_character(self, img, chara_id, mode, mouse=0):
        """ 背景画像に立ち絵を貼り付けます
        """
        self._paste(img, self.character_images[chara_id][mode][mouse],
                    self.character_images[chara_id]['scale'],
                    self.character_images[chara_id]['coordinate'])

    def _generate_back_image(self, shot):
        """ 背景画像を読み込むか生成します
        """
        if shot['back_img'] != '':
            return Image.open(shot['back_img']).convert('RGBA')
        else:
            return Image.new('RGBA', tuple(shot['back_size']),
                             tuple(shot['back_color']))

    def generate(self, shot, regenerate=False):
        """ ある場面用の画像を合成します
        """
        # その場面で必要な画像ファイル名を取得します
        filenames = get_image_filenames(self.out_dir_intermediate, shot,
            self.serifu_text_settings['display'])
        for speaker, filename in filenames:
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
                mouse = 1 if (chara_id == str(speaker)) else 0
                self._paste_character(img, chara_id, mode, mouse)
            # セリフを表示する設定であってセリフがあれば貼ります
            if self.serifu_text_settings['display'] and shot['serifu'] != '':
                self._add_serifu_text(img, shot['serifu'], shot['speaker'])
            # フリーテキストがあれば貼ります
            if shot['free_text'] != '':
                self._add_free_text(img, shot['free_text'])
            img.save(filename)
        return filenames
