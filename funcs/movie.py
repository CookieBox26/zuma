from moviepy.editor import ImageClip, concatenate_videoclips, VideoFileClip
from funcs import get_image_filenames, SPK, format_duration


class MovieGenerator:
    def __init__(self, storyboard):
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        self.out_dir = storyboard['out_dir']
        self.serifu_text_settings = storyboard['serifu_text_settings']
        self.shots = storyboard['shots']

    def generate(self, komas, mp3_file):
        # 各場面のコマ数に応じて動画クリップを作成していく
        clips = []
        for (koma, shot) in zip(komas, self.shots):
            img_files = get_image_filenames(self.out_dir_intermediate, shot,
                self.serifu_text_settings['display'])
            if koma[0] > 0:
                for i_koma in range(koma[0]):
                    img_file = img_files[(i_koma+1) % 2][1]
                    clip = ImageClip(img_file).set_duration(format_duration(SPK))
                    clips.append(clip)
            if koma[1] > 0:
                duration = SPK * koma[1]
                clip = ImageClip(img_files[0][1]).set_duration(format_duration(duration))
                clips.append(clip)

        # mp4 に出力する
        video = concatenate_videoclips(clips)
        print(f'動画の解像度: {video.size}')
        print(f'動画の再生時間: {video.duration}')
        video.write_videofile(f'{self.out_dir}out.mp4', fps=24, audio=mp3_file)
