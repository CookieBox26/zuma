# zuma

台本から動画を生成する Python スクリプトです。  
以下を実行すると resources/sample1/out.mp4 が生成されます。
```
python run.py resources/sample1/storyboard.toml
```

### 環境準備

手元のマシンに [VOICEVOX](https://voicevox.hiroshiba.jp/) をインストールして起動しておき、手元の Python で requests, retry, PIL, pydub, moviepy, toml を利用できるようにしておく必要があります。

### 利用範囲

このコードによる生成物の利用範囲は VOICEVOX の利用規約、各キャラクターの利用規約にしたがってください。

materials/ 以下の二次イラストをそのまま利用・改変いただいても構いませんが著作権は放棄していません。

