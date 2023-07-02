from moviepy.editor import ImageClip, concatenate_videoclips
from funcs import SPK, format_duration


class MovieGenerator:
    def __init__(self, storyboard, ig, skip_mp4=False):
        self.out_dir = storyboard['out_dir']
        self.ig = ig
        self.skip_mp4 = skip_mp4

    def generate(self, komas, shots, mp3_file):
        # 各場面のコマ数に応じて動画クリップを作成していく
        clips = []
        for (koma, shot) in zip(komas, shots):
            img_files = self.ig.generate(shot)
            if koma[0] > 0:
                for i_koma in range(koma[0]):
                    img_file = img_files[(i_koma+1) % 2][1]
                    clip = ImageClip(img_file).set_duration(format_duration(SPK))
                    clips.append(clip)
            if koma[1] > 0:
                duration = SPK * koma[1]
                clip = ImageClip(img_files[0][1]).set_duration(format_duration(duration))
                clips.append(clip)

        if self.skip_mp4:
            return

        # mp4 に出力する
        video = concatenate_videoclips(clips)
        video.write_videofile(f'{self.out_dir}out.mp4', fps=24, audio=mp3_file)
