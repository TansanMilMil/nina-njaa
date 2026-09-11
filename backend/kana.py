from janome.tokenizer import Tokenizer

_tokenizer = Tokenizer()

# Janome（IPADIC）の読みが料理での慣用読みと異なる語の補正辞書。
# 例: 「鶏」は辞書上は音読み「ケイ」だが、料理では「とり」と読まれることがほとんど。
# 検索でヒットしない語が見つかったらここに追加する。
_READING_OVERRIDES: dict[str, str] = {
    "鶏": "とり",
}


def _apply_reading_overrides(text: str) -> str:
    for kanji, reading in sorted(_READING_OVERRIDES.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(kanji, reading)
    return text


def to_hiragana(text: str) -> str:
    """全角カタカナをひらがなに変換する（検索時の表記ゆれ吸収用）"""
    return "".join(
        chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c
        for c in text
    )


def to_reading(text: str) -> str:
    """漢字混じりのテキストをひらがな読みに変換する（検索時の表記ゆれ吸収用）"""
    if not text:
        return ""
    tokens = _tokenizer.tokenize(_apply_reading_overrides(text))
    parts = (
        token.reading if token.reading and token.reading != "*" else token.surface
        for token in tokens
    )
    return to_hiragana("".join(parts))
