def to_hiragana(text: str) -> str:
    """全角カタカナをひらがなに変換する（検索時の表記ゆれ吸収用）"""
    return "".join(
        chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c
        for c in text
    )
