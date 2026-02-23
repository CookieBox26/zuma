from PIL import Image, ImageFont, ImageDraw
from zuma.utils.text import split_text


class ImageGenerator:
    def __init__(self, storyboard):
        self.out_dir = storyboard['out_dir']
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        self.character_images = storyboard['character_images']
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
            settings['coord'], text, color,
            font=font, spacing=settings['spacing'],
            stroke_width=settings.get('stroke_width', 0),
            stroke_fill=settings.get('stroke_fill', 'black'))

    def _add_serifu_text(self, img, text, speaker):
        """ 背景画像にセリフテキスト (字幕) を貼り付けます
        """
        color = self.serifu_text_settings['font_color'].get(speaker)
        if color is None:
            color = self.serifu_text_settings['font_color_default']
        color = tuple(color)
        self._add_text(img, text, color, self.serifu_text_settings)

    def _add_free_text(self, img, text):
        """ 背景画像にフリーテキストを貼り付けます
        """
        color = tuple(self.free_text_settings['font_color'])
        self._add_text(img, text, color, self.free_text_settings)

    def _paste(self, img, path, coord=(0, 0), scale=1.0):
        img_ = Image.open(path)
        img_ = img_.convert('RGBA')  # 念のため確実に RGBA にします
        size_new = (int(scale * img_.width), int(scale * img_.height))
        img_ = img_.resize(size_new)
        img.paste(img_, coord.copy(), img_)  # 座標はコピーしないと変更される

    def _generate_back_image(self, shot):
        """ 背景画像を読み込むか生成します
        """
        if shot['back_img'] != '':
            return Image.open(shot['back_img']).convert('RGBA')
        return Image.new('RGBA', tuple(shot['back_size']), tuple(shot['back_color']))

    def generate_shot(self, shot):
        """ ある場面用の画像を合成します
        """
        # 背景画像を読み込むか生成します
        img = self._generate_back_image(shot)
        # 前景画像があれば貼ります
        for front_img in shot['front_imgs']:
            self._paste(img, **front_img)
        # フリーテキストがあれば貼ります
        if ('free_text' in shot) and (shot['free_text'] != ''):
            self._add_free_text(img, shot['free_text'])

        imgs = [img]
        if len(shot['image_files']) == 2:
            imgs = [img, img.copy()]
        for d, img_ in zip(shot['image_files'], imgs):
            filepath = self.out_dir_intermediate / d['filename']
            # キャラクターがいれば立ち絵を貼ります
            for chara_img in d['chara_imgs'].values():
                self._paste(img_, **chara_img)
            # セリフを表示する設定であってセリフがあれば貼ります
            if self.serifu_text_settings['display'] and shot['serifu_show'] != '':
                self._add_serifu_text(img_, shot['serifu_show'], shot['speaker'])
            img_.save(filepath)

    def generate(self, regenerate=True):
        """ 
        全場面の画像を合成します
        合成した画像を一覧表示する images.html も生成します
        """
        f = open(self.out_dir / 'images.html', mode='w')
        f.write(f'<html><head></head><body style="background: #ccc">\n')
        for shot in self.shots:
            self.generate_shot(shot)
            f.write(f'<h4>{shot["shot_id"]}</h4>\n')
            filename = shot['image_files'][-1]['filename']
            f.write(f'<img src="intermediate/{filename}"/>\n')
        f.write(f'</br></br></br></body></html>\n')
        f.close()
        print('画像一覧 HTML を生成しました')
        print((self.out_dir / 'images.html').as_posix())
