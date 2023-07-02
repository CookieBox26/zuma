# zuma

台本から動画を生成する Python スクリプトです。  
以下を実行すると resources/sample1/out.mp4 が生成されます。
```
python run.py resources/sample1/storyboard.toml
```

### 環境準備

手元のマシンに [VOICEVOX](https://voicevox.hiroshiba.jp/) をインストールして起動しておき、手元の Python で requests, retry, PIL, pydub, moviepy, toml を利用できるようにしておく必要があります。

### 利用範囲

このリポジトリのコード自体はMITライセンスですが、コードによって生成した動画の利用範囲は VOICEVOX の利用規約及び各キャラクターの利用規約にしたがってください。それ以外の素材も利用した場合はそれ以外の素材の利用規約にもしたがってください。

materials/ 以下にコミットしてある私が描いた二次イラストを差し替えずに利用しても構いません (元のキャラクターのガイドラインに準じて利用ください)。

### サンプル台本ファイルの補足

- **resources/sample1/storyboard.toml** ： ~~コミットしてあるイラストしか参照していないのでこのまま動画生成できます~~ 画面にフリーテキストを入れているためフォントファイルを参照しています。.ttf ファイルパスをお持ちのフォントファイルへのパスに書き換えてください。生成した動画を公開される場合は参照したフォントの利用規約をご確認ください。
- **resources/sample2/storyboard.toml** ： さらに BGM のための mp3 ファイルを参照しています。なお、同じ BGM で動画生成したい場合は以下から入手できます。
  - https://musmus.main.jp/music_img1_03.html

