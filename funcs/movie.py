from moviepy.editor import ImageClip, concatenate_videoclips, VideoFileClip
from funcs import FPS, get_image_filenames, format_duration


class MovieGenerator:
    def __init__(self, storyboard):
        self.out_dir_intermediate = storyboard['out_dir_intermediate']
        self.out_dir = storyboard['out_dir']
        self.serifu_text_settings = storyboard['serifu_text_settings']
        self.shots = storyboard['shots']

    def generate(self, durations, audio_file):
        # 各場面のコマ数に応じて動画クリップを作成していく
        clips = []
        for (duration, shot) in zip(durations, self.shots):
            img_files = get_image_filenames(self.out_dir_intermediate, shot,
                self.serifu_text_settings['display'])
            if len(duration[0]) > 0:
                for d_ in duration[0]:
                    img_file = img_files[d_[0]]
                    clip = ImageClip(img_file).set_duration(format_duration(d_[1]))
                    clips.append(clip)
            if duration[1] > 0:
                clip = ImageClip(img_files[0]).set_duration(format_duration(duration[1]))
                clips.append(clip)

        # mp4 に出力する
        video = concatenate_videoclips(clips)
        print(f'動画の解像度: {video.size}')
        print(f'動画の再生時間: {video.duration}')
        video.write_videofile(
            f'{self.out_dir}out.mp4', codec='libx264', fps=FPS,
            audio=audio_file, audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True)
