CARGO_CATEGORIES = {
    1: "冷冻食品",
    2: "冷藏生鲜",
    3: "疫苗医药",
    4: "化工制剂",
    5: "其他"
}

CARGO_CATEGORY_LIST = [
    {"value": 1, "label": "冷冻食品"},
    {"value": 2, "label": "冷藏生鲜"},
    {"value": 3, "label": "疫苗医药"},
    {"value": 4, "label": "化工制剂"},
    {"value": 5, "label": "其他"}
]

def get_cargo_category_label(code: int) -> str:
    return CARGO_CATEGORIES.get(code, "其他")

def get_cargo_category_code(label: str) -> int:
    for code, name in CARGO_CATEGORIES.items():
        if name == label:
            return code
    return 5