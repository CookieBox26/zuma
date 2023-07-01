from PIL import Image, ImageFont, ImageDraw
from funcs import get_image_filenames
import os


class ImageGenerator:
    def __init__(self, storyboard):
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        self.character_images = {str(c['speaker']): c for c
                                 in storyboard['character_images']}
        self.text_settings = storyboard['text_settings']

    def _add_text(self, img, text):
        """ 背景画像に文字列を貼り付けます
        """
        size = self.text_settings['font_size']
        font = ImageFont.truetype(self.text_settings['font_path'], size)
        color = tuple(self.text_settings['font_color'])
        draw = ImageDraw.Draw(img)
        coord = self.text_settings['coordinate']
        width = self.text_settings['width']
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

    def _paste(self, img, chara_id, mode, mouse=0):
        """ 背景画像に立ち絵を貼り付けます
        """
        img_ = Image.open(self.character_images[chara_id][mode][mouse])
        img_ = img_.convert('RGBA')  # 念のため確実に RGBA にします
        scale = self.character_images[chara_id]['scale']
        size_new = (int(scale * img_.width), int(scale * img_.height))
        img_ = img_.resize(size_new)
        img.paste(img_, self.character_images[chara_id]['coordinate'], img_)

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
        filenames = get_image_filenames(self.out_dir_intermediate, shot)
        for speaker, filename in filenames:
            # 既にあればスキップします
            if (not regenerate) and os.path.isfile(filename):
                continue
            # 背景画像を読み込むか生成します
            img = self._generate_back_image(shot)
            # キャラクターがいれば立ち絵を貼ります
            for chara_id, mode in shot['characters'].items():
                mouse = 1 if (chara_id == str(speaker)) else 0
                self._paste(img, chara_id, mode, mouse)
            # 文字列があれば貼ります
            if shot['text'] != '':
                self._add_text(img, shot['text'])
            img.save(filename)
        return filenames
