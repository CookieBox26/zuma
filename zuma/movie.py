from moviepy.editor import ImageClip, concatenate_videoclips, VideoFileClip
from zuma.utils import FPS, get_image_filenames, format_duration
import toml
import warnings


warnings.filterwarnings(  # moviepy 実装由来の警告の抑制
    'ignore', message='invalid escape sequence',
    category=SyntaxWarning, module='moviepy'
)


class MovieGenerator:
    def __init__(self, storyboard):
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        self.out_dir = storyboard['out_dir']
        self.serifu_text_settings = storyboard['serifu_text_settings']
        self.shots = storyboard['shots']

    def generate(self):
        # 各場面のコマ数に応じて動画クリップを作成していく
        durations = toml.loads(
            (self.out_dir_intermediate / 'duration.toml').read_text(encoding='utf8'),
        )['durations']
        audio_file = self.out_dir_intermediate / 'concat.m4a'

        clips = []
        for (duration, shot) in zip(durations, self.shots):
            img_files = get_image_filenames(shot, self.serifu_text_settings['display'])
            if len(duration['voice_durations']) > 0:
                for d_ in duration['voice_durations']:
                    img_file = (self.out_dir_intermediate / img_files[d_['mouth']]).as_posix()
                    clip = ImageClip(img_file).set_duration(format_duration(d_['duration']))
                    clips.append(clip)
            if duration['silent_duration'] > 0:
                clip = ImageClip(
                    (self.out_dir_intermediate / img_files[0]).as_posix()
                ).set_duration(format_duration(duration['silent_duration']))
                clips.append(clip)

        # mp4 に出力する
        video = concatenate_videoclips(clips)
        print(f'動画の解像度: {video.size}')
        print(f'動画の再生時間: {video.duration}')
        video.write_videofile(
            (self.out_dir / 'out.mp4').as_posix(), codec='libx264', fps=FPS,
            audio=audio_file.as_posix(), audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True)
