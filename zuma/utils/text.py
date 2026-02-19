import re
import math
import unicodedata
from itertools import accumulate


def _to_width(c):  # その文字の幅を返す
    if c == ' ':  # 空白は幅 0.25 扱い (実際はフォントによる)
        return 0.25
    alias = unicodedata.east_asian_width(c)
    if alias == 'Na':  # 半角は幅 0.5 扱い
        return 0.5
    return 1.0  # そうでなければ幅 1.0 扱い


def _breakable(s):  # 文章内のその文字を行頭にしてよいかのリストを返す
    last_alphabet = False
    li = []
    for c in s:
        alphabet = re.match(r'[a-zA-Z]', c)
        if last_alphabet and alphabet:  # 英単語中の2文字目以降だったら禁止
            li.append(False)
        elif c in ['、', '。', '?']:  # 句読点であったら禁止
            li.append(False)
        else:  # そうでなければ許可
            li.append(True)
        last_alphabet = alphabet
    return li


def split_text(s, width=24, max_rows=100):
    """
    文章 s に対して width 文字ごとに改行を挿入して返す
    行頭と行末の空白は strip() で削除される
    max_rows を指定したときは max_rows 行を超えた分を max_rows 行目に突っ込む
    英単語の途中や句読点を行頭にしないようにはするが width をはみ出させるので注意
    はみ出しがひどいときは本当に改行してほしい位置に空白をたくさん挿入して対処すること
    """
    li_w = [_to_width(c) for c in s]  # 字幅の取得
    li_b = _breakable(s)  # 行頭可能位置の取得

    max_loop = 20
    for i_loop in range(max_loop):
        li_rows = li_w.copy()
        li_rows = list(accumulate(li_rows))
        li_rows = [min(math.ceil(w / float(width)) - 1, max_rows - 1) for w in li_rows]
        n_rows = max(li_rows) + 1
        prohibited = False
        for i_row in range(1, n_rows):
            index_ = li_rows.index(i_row)  # i_row + 1 行目の行頭
            if not li_b[index_]:
                # 行頭に行頭禁止がきたときその字幅をゼロにして前行末に移動する
                prohibited = True
                li_w[index_] = 0.0
                break
        if not prohibited:
            break
        if i_loop == max_loop - 1:
            print('最大ループ回数でも禁則処理が終了しませんでした')

    n_rows = max(li_rows) + 1
    li_rows.append(max(li_rows) + 1)
    last_n = 0
    s_ = []
    for i_row in range(n_rows):
        n = li_rows.index(i_row + 1)
        s_.append(s[last_n:n].strip())
        last_n = n
    return '\n'.join(s_)


if __name__ == '__main__':
    print('１２３４５６７８９０１２３４５６７８９０')
    s = 'あいうえおかきくけこ。あい。えおかきくけこ。'
    print(split_text(s, 5))
    s = 'あいう apple かきくけこ。あい。えおかきくけこ。'
    print(split_text(s, 5))
    s = 'あいう appleapple かきくけこ。あい。えおかきくけこ。'
    print(split_text(s, 5))
