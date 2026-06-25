_SEASONING_UNITS = {
    "大さじ",
    "小さじ",
    "少々",
    "適量",
    "適宜",
    "少量",
    "ひとつまみ",
    "一つまみ",
    "ひとふり",
    "ひとかけ",
}

_SEASONING_BLACKLIST = {
    "塩",
    "醤油",
    "しょうゆ",
    "砂糖",
    "みりん",
    "味醂",
    "酒",
    "料理酒",
    "酢",
    "米酢",
    "味噌",
    "みそ",
    "サラダ油",
    "油",
    "ごま油",
    "オリーブオイル",
    "オリーブ油",
    "バター",
    "マヨネーズ",
    "ケチャップ",
    "ウスターソース",
    "こしょう",
    "黒こしょう",
    "白こしょう",
    "胡椒",
    "片栗粉",
    "だし",
    "だし汁",
    "出汁",
    "水",
    "コンソメ",
    "鶏ガラスープの素",
    "めんつゆ",
    "豆板醤",
    "オイスターソース",
    "ナンプラー",
    "ポン酢",
    "甜麺醤",
    "中華スープの素",
    "小麦粉",
    "薄力粉",
    "強力粉",
}


def is_main_ingredient(name: str | None, unit: str | None) -> bool:
    if not name:
        return False
    if unit and unit.strip() in _SEASONING_UNITS:
        return False
    if name.strip() in _SEASONING_BLACKLIST:
        return False
    return True
