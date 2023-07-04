# zuma

[VOICEVOX](https://voicevox.hiroshiba.jp/) を利用して台本から動画を生成する Python スクリプトです。ローカルの VOICEVOX を起動した状態で以下を実行すると resources/sample1/out.mp4 が生成されます。
```
python run.py resources/sample1/storyboard.toml
```

### 環境準備

手元のマシンに [VOICEVOX](https://voicevox.hiroshiba.jp/) をインストールしておき、手元の Python で requests, retry, PIL, pydub, moviepy, toml を利用できるようにしておく必要があります。

### 実行方法

`resources/sample1/storyboard.toml` を参考に TOML 形式で台本を記述してください。ローカルの VOICEVOX を起動した状態で、記述した台本を指定して以下のように実行すると resources/sample1/out.mp4 が生成されます。
```
python run.py resources/sample1/storyboard.toml
```

以下のオプションも指定できます。

```
python run.py resources/sample1/storyboard.toml -m 1
# -m 1  画像のみ生成
# -m 2  音声のみ生成
# -m 3  動画まで生成 (デフォルト)

python run.py resources/sample1/storyboard.toml -r 1
# -r 0  中間生成物を削除しない (デフォルト)
# -r 1  中間生成物を削除; 現在の台本上必要な合成音声は残す
# -r 2  中間生成物を削除; すべての中間生成物を削除する
```

| option | description |
| ---- | ---- |
| `-m` |何を生成するかのモードを指定します。音声も動画も生成に時間がかかるので、画面のレイアウト調整時に `-m 1` をご利用ください。|
| `-r` |中間生成物を削除するかを指定します。音声の話速やBGM音量や画像レイアウトを調整するとどんどん不要な中間生成物が溜まってしまうので削除したいときに指定してください。必要な合成音声まで削除すると再生成に時間がかかるので `-r 1` がよいです。ただし常に `-r 1` を指定すると「やはりさっきの話速に戻したい」「聞き比べたい」といったとき不便なので音声パラメータの fix 後に指定するのがよいです。|

### 利用範囲

このリポジトリのコード自体は MIT ライセンスですが、コードによって生成した動画の利用範囲は VOICEVOX の利用規約及び各キャラクターの利用規約にしたがってください。それ以外の素材も利用した場合はそれ以外の素材の利用規約にもしたがってください。

materials/ 以下にコミットしてある二次イラストは私が描いたものです。これを差し替えずに利用しても構いません (元のキャラクターのガイドラインに準じてご利用ください)。

### サンプル台本の補足

- **resources/sample1/storyboard.toml**
  - ~~コミットしてあるイラストしか参照していないのでこのまま動画生成できます~~ 画面に字幕とフリーテキストを入れるためにフォントファイルを参照しています。適当なフォントファイルを用意し台本内の .ttf ファイルパスを書き換えてください。
    - なお、コミットしてある台本と同じフォントを使用する場合は [M PLUS 2](https://fonts.google.com/specimen/M+PLUS+2) から利用規約を確認の上入手してください。
- **resources/sample2/storyboard.toml**
  - BGM のための mp3 ファイルも参照しています。適当な BGM を用意し台本内の mp3 ファイルパスを書き換えてください。
    - なお、コミットしてある台本と同じ BGM を使用する場合は [フリーBGM・音楽素材 MusMus](https://musmus.main.jp/music_img1_03.html) から利用規約を確認の上入手してください。
  - .mp3 ファイルパスを空文字列にすれば BGM なしになります。
  - BGM を変更か削除した場合は resources/sample2/credit.png のクレジット表記も変更する必要があります。

### このスクリプトについて

このスクリプトがしていることは以下です。

- 各場面で必要な png を合成する (話者がいない場面は1枚、いる場面は口を開くので2枚)。
- 各場面のセリフの wav を VOICEVOX で合成し、全場面で連結して mp3 にする。
- 各場面の png から動画クリップを作成し、全場面で連結して mp3 音声を付けて mp4 ファイルに出力する。

#### 中間生成物について

- 中間生成物である png, wav, mp3 を中間生成物フォルダにキャッシュしていますが、png, mp3 は生成に時間がかからなかったので結局常に再生成しています。合成音声 wav については同じ音声設定・セリフで合成済みであれば合成をスキップします。
  - 前景画像やセリフなどを変更するとキャッシュファイルがどんどん増えます。`-r` オプションを参照してください。

#### Tips

- 各場面には「セリフ後無音秒数」しか設定できません。セリフ前に無音時間を挿入したい場合は無セリフ場面を挿入してください。
- キャラクターは2人である必要はなく、任意の人数にできます。
- キャラクターの表示位置は全場面を通して固定になっていますが、キャラクターを全場面に登場させる必要はなく、この場面ではこちらのキャラクターは離席、ということはできます。
- サンプル台本にあるように VOICEVOX の音声のスタイル ID でキャラクターを管理していますが、ずんだもんのようにスタイル ID が複数 (ノーマル、ささやきなど) あるキャラクターもいます。場面によってキャラクターの声のスタイルを分けたい場合は、「ささやきのずんだもん」を別キャラクターとして同じ立ち絵・スケール・座標で設定し、ささやく場面だけ「ずんだもん」を「ささやきのずんだもん」にすげかえれば実現できます (おそらく)。

