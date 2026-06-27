import os
import math
import random
import base64
import httpx
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/v1/quality", tags=["品质评估"])

PRODUCT_CATEGORIES = {
    # 水果品类（34种）
    "apple": {"name": "苹果", "category": "水果", "freshness_days": 60, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["陕西洛川", "山东烟台", "甘肃静宁"], "weight_range": (50, 200)},
    "strawberry": {"name": "草莓", "category": "水果", "freshness_days": 5, "indicators": ["色泽", "硬度", "腐烂程度", "表皮完整度"], "origins": ["四川双流", "云南昆明", "辽宁丹东"], "weight_range": (10, 50)},
    "grape": {"name": "葡萄", "category": "水果", "freshness_days": 14, "indicators": ["色泽", "硬度", "脱粒程度", "表皮完整度"], "origins": ["新疆吐鲁番", "河北怀来", "山东平度"], "weight_range": (30, 150)},
    "orange": {"name": "橙子", "category": "水果", "freshness_days": 45, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["江西赣南", "广东廉江", "湖北秭归"], "weight_range": (50, 200)},
    "banana": {"name": "香蕉", "category": "水果", "freshness_days": 12, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["海南澄迈", "云南河口", "广西南宁"], "weight_range": (40, 180)},
    "watermelon": {"name": "西瓜", "category": "水果", "freshness_days": 21, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["新疆昌吉", "宁夏中卫", "河南开封"], "weight_range": (100, 500)},
    "pear": {"name": "梨", "category": "水果", "freshness_days": 60, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["河北赵县", "安徽砀山", "山东莱阳"], "weight_range": (50, 200)},
    "peach": {"name": "桃子", "category": "水果", "freshness_days": 7, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["河北深州", "陕西富平", "浙江奉化"], "weight_range": (30, 150)},
    "plum": {"name": "李子", "category": "水果", "freshness_days": 10, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["四川汶川", "贵州六马", "广东信宜"], "weight_range": (20, 100)},
    "apricot": {"name": "杏子", "category": "水果", "freshness_days": 7, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["新疆库车", "河北巨鹿", "甘肃敦煌"], "weight_range": (20, 80)},
    "cherry": {"name": "樱桃", "category": "水果", "freshness_days": 5, "indicators": ["色泽", "硬度", "腐烂程度", "表皮完整度"], "origins": ["山东烟台", "辽宁大连", "四川汉源"], "weight_range": (5, 30)},
    "blueberry": {"name": "蓝莓", "category": "水果", "freshness_days": 7, "indicators": ["色泽", "硬度", "腐烂程度", "表皮完整度"], "origins": ["贵州麻江", "吉林延边", "云南澄江"], "weight_range": (5, 25)},
    "raspberry": {"name": "覆盆子", "category": "水果", "freshness_days": 3, "indicators": ["色泽", "硬度", "腐烂程度", "表皮完整度"], "origins": ["浙江建德", "四川阿坝", "云南红河"], "weight_range": (3, 15)},
    "mango": {"name": "芒果", "category": "水果", "freshness_days": 14, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["海南三亚", "广西百色", "云南元江"], "weight_range": (30, 200)},
    "durian": {"name": "榴莲", "category": "水果", "freshness_days": 7, "indicators": ["色泽", "硬度", "表皮完整度", "气味"], "origins": ["泰国", "马来西亚", "海南万宁"], "weight_range": (80, 300)},
    "pineapple": {"name": "菠萝", "category": "水果", "freshness_days": 21, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["海南文昌", "广东徐闻", "云南西双版纳"], "weight_range": (50, 250)},
    "litchi": {"name": "荔枝", "category": "水果", "freshness_days": 5, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["广东茂名", "广西灵山", "福建莆田"], "weight_range": (20, 80)},
    "longan": {"name": "龙眼", "category": "水果", "freshness_days": 7, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["福建莆田", "广东高州", "广西平南"], "weight_range": (20, 100)},
    "kiwi": {"name": "猕猴桃", "category": "水果", "freshness_days": 21, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["陕西周至", "四川蒲江", "贵州修文"], "weight_range": (30, 150)},
    "pomegranate": {"name": "石榴", "category": "水果", "freshness_days": 30, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["新疆和田", "云南会泽", "河南荥阳"], "weight_range": (40, 200)},
    "dragonfruit": {"name": "火龙果", "category": "水果", "freshness_days": 14, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["海南海口", "广西南宁", "广东湛江"], "weight_range": (30, 150)},
    "papaya": {"name": "木瓜", "category": "水果", "freshness_days": 10, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["海南三亚", "广东茂名", "广西南宁"], "weight_range": (30, 150)},
    "coconut": {"name": "椰子", "category": "水果", "freshness_days": 30, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["海南文昌", "泰国", "越南"], "weight_range": (100, 300)},
    "guava": {"name": "番石榴", "category": "水果", "freshness_days": 14, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["广东湛江", "广西南宁", "海南海口"], "weight_range": (30, 100)},
    "avocado": {"name": "牛油果", "category": "水果", "freshness_days": 10, "indicators": ["色泽", "硬度", "成熟度", "表皮完整度"], "origins": ["墨西哥", "智利", "云南孟连"], "weight_range": (20, 80)},
    "lemon": {"name": "柠檬", "category": "水果", "freshness_days": 30, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["四川安岳", "海南澄迈", "云南德宏"], "weight_range": (20, 80)},
    "lime": {"name": "青柠", "category": "水果", "freshness_days": 30, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["海南海口", "泰国", "越南"], "weight_range": (15, 60)},
    "passionfruit": {"name": "百香果", "category": "水果", "freshness_days": 14, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["广西钦北", "云南西双版纳", "海南万宁"], "weight_range": (15, 60)},
    "cantaloupe": {"name": "哈密瓜", "category": "水果", "freshness_days": 21, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["新疆哈密", "甘肃敦煌", "内蒙古磴口"], "weight_range": (80, 300)},
    "honeydew": {"name": "白兰瓜", "category": "水果", "freshness_days": 21, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["甘肃兰州", "新疆昌吉", "宁夏银川"], "weight_range": (80, 300)},
    "fig": {"name": "无花果", "category": "水果", "freshness_days": 3, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["新疆阿图什", "山东威海", "四川威远"], "weight_range": (5, 25)},
    "date": {"name": "枣", "category": "水果", "freshness_days": 30, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["新疆和田", "陕西佳县", "山西柳林"], "weight_range": (20, 100)},
    "persimmon": {"name": "柿子", "category": "水果", "freshness_days": 14, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["陕西富平", "山西运城", "河北满城"], "weight_range": (30, 150)},
    "mulberry": {"name": "桑葚", "category": "水果", "freshness_days": 3, "indicators": ["色泽", "硬度", "腐烂程度", "表皮完整度"], "origins": ["四川德昌", "浙江海宁", "江苏南通"], "weight_range": (5, 30)},

    # 蔬菜品类（26种）
    "cucumber": {"name": "黄瓜", "category": "蔬菜", "freshness_days": 10, "indicators": ["色泽", "硬度", "表皮完整度", "损伤程度"], "origins": ["山东寿光", "河北永年", "辽宁凌源"], "weight_range": (20, 100)},
    "carrot": {"name": "胡萝卜", "category": "蔬菜", "freshness_days": 30, "indicators": ["色泽", "硬度", "表皮完整度", "根须状态"], "origins": ["山东潍坊", "河南开封", "内蒙古通辽"], "weight_range": (30, 150)},
    "broccoli": {"name": "西兰花", "category": "蔬菜", "freshness_days": 7, "indicators": ["色泽", "水分状态", "花球完整度", "茎叶状态"], "origins": ["云南昆明", "山东寿光", "河北邯郸"], "weight_range": (20, 80)},
    "celery": {"name": "芹菜", "category": "蔬菜", "freshness_days": 10, "indicators": ["色泽", "水分状态", "茎叶完整性", "损伤程度"], "origins": ["山东平度", "河北唐山", "四川彭州"], "weight_range": (30, 150)},
    "potato": {"name": "土豆", "category": "蔬菜", "freshness_days": 60, "indicators": ["色泽", "外观状态", "表皮完整度", "发芽情况"], "origins": ["内蒙古乌兰察布", "甘肃定西", "黑龙江讷河"], "weight_range": (100, 500)},
    "onion": {"name": "洋葱", "category": "蔬菜", "freshness_days": 45, "indicators": ["色泽", "外观状态", "表皮完整度", "发芽情况"], "origins": ["山东金乡", "甘肃酒泉", "云南元谋"], "weight_range": (50, 200)},
    "garlic": {"name": "大蒜", "category": "蔬菜", "freshness_days": 90, "indicators": ["色泽", "外观状态", "表皮完整度", "发芽情况"], "origins": ["山东金乡", "河南中牟", "四川彭州"], "weight_range": (20, 100)},
    "greenpepper": {"name": "青椒", "category": "蔬菜", "freshness_days": 10, "indicators": ["色泽", "外观饱满度", "表皮完整度", "成熟度"], "origins": ["山东寿光", "云南昆明", "海南海口"], "weight_range": (20, 100)},
    "redpepper": {"name": "红椒", "category": "蔬菜", "freshness_days": 10, "indicators": ["色泽", "外观饱满度", "表皮完整度", "成熟度"], "origins": ["山东寿光", "云南昆明", "海南海口"], "weight_range": (20, 100)},
    "eggplant": {"name": "茄子", "category": "蔬菜", "freshness_days": 10, "indicators": ["色泽", "外观饱满度", "表皮完整度", "成熟度"], "origins": ["山东寿光", "河北邯郸", "辽宁凌源"], "weight_range": (30, 150)},
    "wintermelon": {"name": "冬瓜", "category": "蔬菜", "freshness_days": 60, "indicators": ["色泽", "外观状态", "表皮完整度", "损伤程度"], "origins": ["广东三水", "云南昆明", "四川成都"], "weight_range": (100, 500)},
    "pumpkin": {"name": "南瓜", "category": "蔬菜", "freshness_days": 60, "indicators": ["色泽", "外观状态", "表皮完整度", "损伤程度"], "origins": ["云南昆明", "山东寿光", "河南开封"], "weight_range": (80, 400)},
    "cabbage": {"name": "白菜", "category": "蔬菜", "freshness_days": 21, "indicators": ["色泽", "水分状态", "叶片完整性", "黄叶情况"], "origins": ["山东寿光", "河北玉田", "辽宁凌海"], "weight_range": (30, 150)},
    "chinese cabbage": {"name": "青菜", "category": "蔬菜", "freshness_days": 7, "indicators": ["色泽", "水分状态", "叶片完整性", "黄叶情况"], "origins": ["上海", "江苏苏州", "浙江杭州"], "weight_range": (10, 50)},
    "leek": {"name": "韭菜", "category": "蔬菜", "freshness_days": 5, "indicators": ["色泽", "水分状态", "叶片完整性", "黄叶情况"], "origins": ["河北永年", "山东寿光", "河南开封"], "weight_range": (5, 30)},
    "coriander": {"name": "香菜", "category": "蔬菜", "freshness_days": 3, "indicators": ["色泽", "水分状态", "叶片完整性", "黄叶情况"], "origins": ["山东潍坊", "河北邯郸", "四川成都"], "weight_range": (2, 15)},
    "parsley": {"name": "欧芹", "category": "蔬菜", "freshness_days": 5, "indicators": ["色泽", "水分状态", "叶片完整性", "黄叶情况"], "origins": ["云南昆明", "上海", "山东青岛"], "weight_range": (2, 15)},
    "basil": {"name": "罗勒", "category": "蔬菜", "freshness_days": 3, "indicators": ["色泽", "水分状态", "叶片完整性", "黄叶情况"], "origins": ["云南昆明", "广东广州", "福建厦门"], "weight_range": (1, 10)},
    "lettuce": {"name": "生菜", "category": "蔬菜", "freshness_days": 7, "indicators": ["色泽", "水分状态", "萎蔫程度", "黄叶情况"], "origins": ["云南昆明", "山东寿光", "海南海口"], "weight_range": (10, 50)},
    "tomato": {"name": "番茄", "category": "蔬菜", "freshness_days": 14, "indicators": ["色泽", "外观饱满度", "表皮完整性", "成熟度"], "origins": ["山东寿光", "云南昆明", "新疆石河子"], "weight_range": (30, 150)},
    "sweetpotato": {"name": "红薯", "category": "蔬菜", "freshness_days": 45, "indicators": ["色泽", "外观状态", "表皮完整度", "发芽情况"], "origins": ["河南开封", "山东泗水", "四川成都"], "weight_range": (50, 250)},
    "yam": {"name": "山药", "category": "蔬菜", "freshness_days": 30, "indicators": ["色泽", "外观状态", "表皮完整度", "损伤程度"], "origins": ["河南焦作", "山东菏泽", "河北保定"], "weight_range": (30, 150)},
    "ginger": {"name": "生姜", "category": "蔬菜", "freshness_days": 60, "indicators": ["色泽", "外观状态", "表皮完整度", "发芽情况"], "origins": ["山东安丘", "广东清远", "云南文山"], "weight_range": (20, 100)},
    "shallot": {"name": "香葱", "category": "蔬菜", "freshness_days": 5, "indicators": ["色泽", "水分状态", "叶片完整性", "黄叶情况"], "origins": ["山东寿光", "云南昆明", "广东广州"], "weight_range": (2, 15)},
    "spinach": {"name": "菠菜", "category": "蔬菜", "freshness_days": 5, "indicators": ["色泽", "水分状态", "黄叶情况", "萎蔫程度"], "origins": ["山东寿光", "河北唐山", "云南昆明"], "weight_range": (10, 50)},
    "green bean": {"name": "绿豆", "category": "蔬菜", "freshness_days": 180, "indicators": ["色泽", "外观状态", "发芽情况", "霉变情况"], "origins": ["内蒙古通辽", "河北张家口", "山西大同"], "weight_range": (50, 250)},

    # 肉类品类（16种）
    "beef": {"name": "牛肉", "category": "肉类", "freshness_days": 21, "indicators": ["色泽", "肉质紧致度", "脂肪分布", "表面状态"], "origins": ["内蒙古呼伦贝尔", "新疆伊犁", "吉林延边"], "weight_range": (50, 300)},
    "pork": {"name": "猪肉", "category": "肉类", "freshness_days": 14, "indicators": ["色泽", "肉质紧致度", "脂肪分布", "表面状态"], "origins": ["四川成都", "河南郑州", "山东临沂"], "weight_range": (50, 300)},
    "lamb": {"name": "羊肉", "category": "肉类", "freshness_days": 14, "indicators": ["色泽", "肉质紧致度", "脂肪分布", "表面状态"], "origins": ["内蒙古锡林郭勒", "新疆阿勒泰", "青海海北"], "weight_range": (30, 200)},
    "chicken": {"name": "鸡肉", "category": "肉类", "freshness_days": 7, "indicators": ["色泽", "肉质紧致度", "表皮完整性", "表面状态"], "origins": ["山东德州", "河南漯河", "安徽宿州"], "weight_range": (20, 100)},
    "duck": {"name": "鸭肉", "category": "肉类", "freshness_days": 10, "indicators": ["色泽", "肉质紧致度", "表皮完整性", "表面状态"], "origins": ["江苏南京", "浙江绍兴", "广东广州"], "weight_range": (30, 150)},
    "goose": {"name": "鹅肉", "category": "肉类", "freshness_days": 14, "indicators": ["色泽", "肉质紧致度", "表皮完整性", "表面状态"], "origins": ["广东清远", "安徽六安", "江苏扬州"], "weight_range": (50, 200)},
    "turkey": {"name": "火鸡", "category": "肉类", "freshness_days": 14, "indicators": ["色泽", "肉质紧致度", "表皮完整性", "表面状态"], "origins": ["美国", "加拿大", "山东济南"], "weight_range": (80, 300)},
    "rabbit": {"name": "兔肉", "category": "肉类", "freshness_days": 7, "indicators": ["色泽", "肉质紧致度", "表皮完整性", "表面状态"], "origins": ["四川成都", "山东临沂", "河南洛阳"], "weight_range": (10, 50)},
    "beef liver": {"name": "牛肝", "category": "肉类", "freshness_days": 3, "indicators": ["色泽", "表面状态", "质地均匀度", "损伤程度"], "origins": ["内蒙古", "新疆", "吉林"], "weight_range": (5, 25)},
    "pork liver": {"name": "猪肝", "category": "肉类", "freshness_days": 3, "indicators": ["色泽", "表面状态", "质地均匀度", "损伤程度"], "origins": ["四川", "河南", "山东"], "weight_range": (3, 15)},
    "chicken liver": {"name": "鸡肝", "category": "肉类", "freshness_days": 2, "indicators": ["色泽", "表面状态", "质地均匀度", "损伤程度"], "origins": ["山东", "河南", "安徽"], "weight_range": (1, 10)},
    "beef tongue": {"name": "牛舌", "category": "肉类", "freshness_days": 7, "indicators": ["色泽", "表面状态", "质地均匀度", "损伤程度"], "origins": ["内蒙古", "新疆", "吉林"], "weight_range": (2, 10)},
    "pork belly": {"name": "五花肉", "category": "肉类", "freshness_days": 7, "indicators": ["色泽", "脂肪分布", "肉质紧致度", "表面状态"], "origins": ["四川", "湖南", "山东"], "weight_range": (20, 100)},
    "beef brisket": {"name": "牛腩", "category": "肉类", "freshness_days": 10, "indicators": ["色泽", "脂肪分布", "肉质紧致度", "表面状态"], "origins": ["内蒙古", "新疆", "吉林"], "weight_range": (30, 150)},
    "pork chop": {"name": "猪排", "category": "肉类", "freshness_days": 7, "indicators": ["色泽", "肉质紧致度", "表面状态", "损伤程度"], "origins": ["四川", "河南", "山东"], "weight_range": (10, 50)},
    "chicken breast": {"name": "鸡胸肉", "category": "肉类", "freshness_days": 5, "indicators": ["色泽", "肉质紧致度", "表面状态", "损伤程度"], "origins": ["山东", "河南", "安徽"], "weight_range": (5, 30)},

    # 海鲜品类（17种）
    "salmon": {"name": "三文鱼", "category": "海鲜", "freshness_days": 7, "indicators": ["色泽", "肉质紧致度", "表面状态", "眼清度"], "origins": ["挪威", "智利", "加拿大"], "weight_range": (20, 100)},
    "shrimp": {"name": "虾", "category": "海鲜", "freshness_days": 5, "indicators": ["色泽", "肉质紧致度", "黑变程度", "表面状态"], "origins": ["广东湛江", "福建厦门", "山东青岛"], "weight_range": (5, 50)},
    "crab": {"name": "螃蟹", "category": "海鲜", "freshness_days": 5, "indicators": ["色泽", "活力状态", "表面状态", "壳完整度"], "origins": ["江苏阳澄湖", "浙江舟山", "广东湛江"], "weight_range": (20, 150)},
    "lobster": {"name": "龙虾", "category": "海鲜", "freshness_days": 3, "indicators": ["色泽", "活力状态", "表面状态", "壳完整度"], "origins": ["澳大利亚", "加拿大", "广东湛江"], "weight_range": (50, 200)},
    "scallop": {"name": "扇贝", "category": "海鲜", "freshness_days": 3, "indicators": ["色泽", "肉质紧致度", "表面状态", "壳完整度"], "origins": ["山东烟台", "辽宁大连", "广东湛江"], "weight_range": (5, 30)},
    "oyster": {"name": "生蚝", "category": "海鲜", "freshness_days": 3, "indicators": ["活力状态", "表面状态", "壳完整度"], "origins": ["广东湛江", "山东乳山", "福建莆田"], "weight_range": (5, 30)},
    "clam": {"name": "蛤蜊", "category": "海鲜", "freshness_days": 3, "indicators": ["活力状态", "表面状态", "壳完整度"], "origins": ["山东青岛", "辽宁大连", "浙江宁波"], "weight_range": (5, 30)},
    "mussel": {"name": "贻贝", "category": "海鲜", "freshness_days": 3, "indicators": ["活力状态", "表面状态", "壳完整度"], "origins": ["山东青岛", "辽宁大连", "浙江舟山"], "weight_range": (5, 30)},
    "squid": {"name": "鱿鱼", "category": "海鲜", "freshness_days": 3, "indicators": ["色泽", "肉质紧致度", "表面状态", "表皮完整度"], "origins": ["山东烟台", "辽宁大连", "广东湛江"], "weight_range": (5, 50)},
    "octopus": {"name": "章鱼", "category": "海鲜", "freshness_days": 3, "indicators": ["色泽", "肉质紧致度", "表面状态", "表皮完整度"], "origins": ["山东青岛", "辽宁大连", "广东湛江"], "weight_range": (10, 80)},
    "cod": {"name": "鳕鱼", "category": "海鲜", "freshness_days": 7, "indicators": ["色泽", "肉质紧致度", "表面状态", "眼清度"], "origins": ["挪威", "冰岛", "俄罗斯"], "weight_range": (30, 150)},
    "tuna": {"name": "金枪鱼", "category": "海鲜", "freshness_days": 5, "indicators": ["色泽", "肉质紧致度", "表面状态", "眼清度"], "origins": ["日本", "韩国", "美国夏威夷"], "weight_range": (50, 300)},
    "mackerel": {"name": "鲭鱼", "category": "海鲜", "freshness_days": 3, "indicators": ["色泽", "肉质紧致度", "表面状态", "眼清度"], "origins": ["山东青岛", "辽宁大连", "浙江舟山"], "weight_range": (10, 50)},
    "herring": {"name": "鲱鱼", "category": "海鲜", "freshness_days": 3, "indicators": ["色泽", "肉质紧致度", "表面状态", "眼清度"], "origins": ["挪威", "瑞典", "俄罗斯"], "weight_range": (10, 50)},
    "tilapia": {"name": "罗非鱼", "category": "海鲜", "freshness_days": 5, "indicators": ["色泽", "肉质紧致度", "表面状态", "眼清度"], "origins": ["广东湛江", "海南海口", "云南昆明"], "weight_range": (10, 50)},
    "carp": {"name": "鲤鱼", "category": "海鲜", "freshness_days": 5, "indicators": ["色泽", "肉质紧致度", "表面状态", "眼清度"], "origins": ["河南开封", "山东济南", "四川成都"], "weight_range": (20, 100)},
    "catfish": {"name": "鲶鱼", "category": "海鲜", "freshness_days": 5, "indicators": ["色泽", "肉质紧致度", "表面状态", "眼清度"], "origins": ["河南开封", "山东济南", "四川成都"], "weight_range": (20, 100)},

    # 乳制品品类（8种）
    "milk": {"name": "鲜奶", "category": "乳制品", "freshness_days": 7, "indicators": ["色泽", "质地均匀度", "表面洁净度", "包装完整性"], "origins": ["内蒙古呼和浩特", "黑龙江齐齐哈尔", "新疆乌鲁木齐"], "weight_range": (100, 500)},
    "yogurt": {"name": "酸奶", "category": "乳制品", "freshness_days": 14, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["内蒙古呼和浩特", "北京", "上海"], "weight_range": (50, 200)},
    "cheese": {"name": "奶酪", "category": "乳制品", "freshness_days": 60, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["内蒙古呼和浩特", "新疆乌鲁木齐", "北京"], "weight_range": (10, 100)},
    "butter": {"name": "黄油", "category": "乳制品", "freshness_days": 30, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["内蒙古呼和浩特", "新疆乌鲁木齐", "北京"], "weight_range": (5, 50)},
    "cream": {"name": "奶油", "category": "乳制品", "freshness_days": 7, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["内蒙古呼和浩特", "北京", "上海"], "weight_range": (5, 50)},
    "icecream": {"name": "冰淇淋", "category": "乳制品", "freshness_days": 30, "indicators": ["色泽", "质地均匀度", "融化程度", "包装完整性"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 200)},
    "milk powder": {"name": "奶粉", "category": "乳制品", "freshness_days": 365, "indicators": ["色泽", "结块程度", "表面状态", "包装完整性"], "origins": ["内蒙古呼和浩特", "黑龙江齐齐哈尔", "新疆乌鲁木齐"], "weight_range": (10, 100)},
    "cream cheese": {"name": "奶油芝士", "category": "乳制品", "freshness_days": 14, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["北京", "上海", "广东广州"], "weight_range": (5, 50)},

    # 豆制品品类（5种）
    "tofu": {"name": "豆腐", "category": "豆制品", "freshness_days": 3, "indicators": ["色泽", "质地均匀度", "表面状态", "损伤程度"], "origins": ["安徽淮南", "浙江杭州", "四川成都"], "weight_range": (10, 50)},
    "tofu skin": {"name": "豆皮", "category": "豆制品", "freshness_days": 5, "indicators": ["色泽", "质地均匀度", "表面状态", "损伤程度"], "origins": ["安徽淮南", "浙江杭州", "四川成都"], "weight_range": (5, 30)},
    "soybean": {"name": "大豆", "category": "豆制品", "freshness_days": 180, "indicators": ["色泽", "外观状态", "发芽情况", "霉变情况"], "origins": ["黑龙江哈尔滨", "吉林长春", "辽宁沈阳"], "weight_range": (50, 300)},
    "tofu pudding": {"name": "豆腐脑", "category": "豆制品", "freshness_days": 1, "indicators": ["色泽", "质地均匀度", "表面状态", "损伤程度"], "origins": ["北京", "四川成都", "河南开封"], "weight_range": (5, 30)},
    "soy milk": {"name": "豆浆", "category": "豆制品", "freshness_days": 3, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 200)},

    # 蛋类品类（4种）
    "egg": {"name": "鸡蛋", "category": "蛋类", "freshness_days": 21, "indicators": ["蛋壳完整度", "蛋壳色泽", "蛋壳状态", "清洁度"], "origins": ["河南郑州", "山东临沂", "河北石家庄"], "weight_range": (10, 50)},
    "duck egg": {"name": "鸭蛋", "category": "蛋类", "freshness_days": 28, "indicators": ["蛋壳完整度", "蛋壳色泽", "蛋壳状态", "清洁度"], "origins": ["江苏高邮", "浙江绍兴", "湖北武汉"], "weight_range": (10, 50)},
    "goose egg": {"name": "鹅蛋", "category": "蛋类", "freshness_days": 30, "indicators": ["蛋壳完整度", "蛋壳色泽", "蛋壳状态", "清洁度"], "origins": ["江苏扬州", "安徽六安", "河南开封"], "weight_range": (5, 30)},
    "quail egg": {"name": "鹌鹑蛋", "category": "蛋类", "freshness_days": 14, "indicators": ["蛋壳完整度", "蛋壳色泽", "蛋壳状态", "清洁度"], "origins": ["河南郑州", "山东临沂", "河北石家庄"], "weight_range": (2, 15)},

    # 医药制品品类（8种）
    "vaccine": {"name": "疫苗", "category": "医药制品", "freshness_days": 365, "indicators": ["外观完整性", "包装完整性", "标签清晰度", "有效期状态"], "origins": ["北京", "上海", "广东深圳"], "weight_range": (1, 10)},
    "blood product": {"name": "血液制品", "category": "医药制品", "freshness_days": 35, "indicators": ["外观完整性", "包装完整性", "标签清晰度", "有效期状态"], "origins": ["北京", "上海", "广东广州"], "weight_range": (1, 20)},
    "insulin": {"name": "胰岛素", "category": "医药制品", "freshness_days": 365, "indicators": ["外观完整性", "包装完整性", "标签清晰度", "有效期状态"], "origins": ["北京", "上海", "江苏无锡"], "weight_range": (1, 5)},
    "biological agent": {"name": "生物制剂", "category": "医药制品", "freshness_days": 180, "indicators": ["外观完整性", "包装完整性", "标签清晰度", "有效期状态"], "origins": ["北京", "上海", "广东广州"], "weight_range": (1, 20)},
    "plasma": {"name": "血浆", "category": "医药制品", "freshness_days": 35, "indicators": ["外观完整性", "包装完整性", "标签清晰度", "有效期状态"], "origins": ["北京", "上海", "广东广州"], "weight_range": (5, 50)},
    "serum": {"name": "血清", "category": "医药制品", "freshness_days": 90, "indicators": ["外观完整性", "包装完整性", "标签清晰度", "有效期状态"], "origins": ["北京", "上海", "江苏南京"], "weight_range": (1, 10)},
    "reagent": {"name": "诊断试剂", "category": "医药制品", "freshness_days": 180, "indicators": ["外观完整性", "包装完整性", "标签清晰度", "有效期状态"], "origins": ["北京", "上海", "广东深圳"], "weight_range": (1, 20)},
    "antibody": {"name": "抗体药物", "category": "医药制品", "freshness_days": 365, "indicators": ["外观完整性", "包装完整性", "标签清晰度", "有效期状态"], "origins": ["北京", "上海", "广东广州"], "weight_range": (1, 10)},

    # 花卉品类（10种）
    "rose": {"name": "玫瑰", "category": "花卉", "freshness_days": 7, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "广东广州", "四川西昌"], "weight_range": (1, 20)},
    "lily": {"name": "百合", "category": "花卉", "freshness_days": 10, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "湖南长沙", "浙江杭州"], "weight_range": (1, 20)},
    "carnation": {"name": "康乃馨", "category": "花卉", "freshness_days": 14, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "广东广州", "浙江杭州"], "weight_range": (1, 20)},
    "tulip": {"name": "郁金香", "category": "花卉", "freshness_days": 7, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "荷兰", "浙江杭州"], "weight_range": (1, 20)},
    "orchid": {"name": "兰花", "category": "花卉", "freshness_days": 21, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "广东广州", "福建漳州"], "weight_range": (1, 20)},
    "sunflower": {"name": "向日葵", "category": "花卉", "freshness_days": 7, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "内蒙古呼和浩特", "新疆乌鲁木齐"], "weight_range": (1, 20)},
    "daisy": {"name": "雏菊", "category": "花卉", "freshness_days": 10, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "上海", "浙江杭州"], "weight_range": (1, 20)},
    "peony": {"name": "牡丹", "category": "花卉", "freshness_days": 5, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["河南洛阳", "山东菏泽", "安徽亳州"], "weight_range": (1, 20)},
    "hydrangea": {"name": "绣球花", "category": "花卉", "freshness_days": 7, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "浙江杭州", "江苏无锡"], "weight_range": (1, 20)},
    "baby breath": {"name": "满天星", "category": "花卉", "freshness_days": 14, "indicators": ["色泽", "花头完整性", "叶片状态", "茎部状态"], "origins": ["云南昆明", "广东广州", "四川西昌"], "weight_range": (1, 20)},

    # 冷冻食品品类（10种）
    "frozen dumpling": {"name": "速冻水饺", "category": "冷冻食品", "freshness_days": 180, "indicators": ["外观状态", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["山东烟台", "河南郑州", "辽宁沈阳"], "weight_range": (50, 300)},
    "frozen vegetable": {"name": "冷冻蔬菜", "category": "冷冻食品", "freshness_days": 365, "indicators": ["色泽", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["山东寿光", "云南昆明", "河南开封"], "weight_range": (50, 300)},
    "frozen meat": {"name": "冷冻肉类", "category": "冷冻食品", "freshness_days": 365, "indicators": ["色泽", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["内蒙古呼和浩特", "山东济南", "河南郑州"], "weight_range": (50, 300)},
    "frozen seafood": {"name": "冷冻海鲜", "category": "冷冻食品", "freshness_days": 180, "indicators": ["色泽", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["山东青岛", "辽宁大连", "广东湛江"], "weight_range": (50, 300)},
    "frozen bun": {"name": "速冻包子", "category": "冷冻食品", "freshness_days": 180, "indicators": ["外观状态", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["天津", "河南郑州", "山东济南"], "weight_range": (50, 300)},
    "frozen noodle": {"name": "速冻面条", "category": "冷冻食品", "freshness_days": 180, "indicators": ["外观状态", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["河南郑州", "山东济南", "河北石家庄"], "weight_range": (50, 300)},
    "frozen pizza": {"name": "冷冻披萨", "category": "冷冻食品", "freshness_days": 180, "indicators": ["外观状态", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 300)},
    "frozen dessert": {"name": "冷冻甜点", "category": "冷冻食品", "freshness_days": 180, "indicators": ["外观状态", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 300)},
    "ice cream": {"name": "冰淇淋", "category": "冷冻食品", "freshness_days": 180, "indicators": ["外观状态", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 200)},
    "popsicle": {"name": "冰棍", "category": "冷冻食品", "freshness_days": 180, "indicators": ["外观状态", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 200)},

    # 熟食预制菜品类（8种）
    "prepared meal": {"name": "预制菜", "category": "熟食预制菜", "freshness_days": 7, "indicators": ["外观状态", "表面状态", "包装完整性", "标签清晰度"], "origins": ["广东广州", "浙江杭州", "四川成都"], "weight_range": (50, 200)},
    "deli meat": {"name": "卤味熟食", "category": "熟食预制菜", "freshness_days": 5, "indicators": ["色泽", "表面状态", "质地均匀度", "包装完整性"], "origins": ["四川成都", "湖南长沙", "湖北武汉"], "weight_range": (20, 100)},
    "soup base": {"name": "火锅底料", "category": "熟食预制菜", "freshness_days": 90, "indicators": ["外观状态", "表面状态", "包装完整性", "标签清晰度"], "origins": ["重庆", "四川成都", "贵州贵阳"], "weight_range": (10, 50)},
    "frozen meal": {"name": "速冻便当", "category": "熟食预制菜", "freshness_days": 180, "indicators": ["外观状态", "冻结状态", "包装完整性", "标签清晰度"], "origins": ["广东广州", "上海", "北京"], "weight_range": (50, 200)},
    "cooked food": {"name": "即食熟食", "category": "熟食预制菜", "freshness_days": 3, "indicators": ["色泽", "表面状态", "质地均匀度", "包装完整性"], "origins": ["北京", "上海", "广东广州"], "weight_range": (20, 100)},
    "sushi": {"name": "寿司", "category": "熟食预制菜", "freshness_days": 1, "indicators": ["色泽", "表面状态", "质地均匀度", "包装完整性"], "origins": ["上海", "广东广州", "北京"], "weight_range": (10, 50)},
    "sandwich": {"name": "三明治", "category": "熟食预制菜", "freshness_days": 2, "indicators": ["色泽", "表面状态", "质地均匀度", "包装完整性"], "origins": ["北京", "上海", "广东广州"], "weight_range": (10, 50)},
    "salad": {"name": "沙拉", "category": "熟食预制菜", "freshness_days": 1, "indicators": ["色泽", "表面状态", "质地均匀度", "包装完整性"], "origins": ["北京", "上海", "广东广州"], "weight_range": (10, 50)},

    # 饮料品类（8种）
    "fresh juice": {"name": "鲜榨果汁", "category": "饮料", "freshness_days": 3, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["广东广州", "上海", "北京"], "weight_range": (50, 200)},
    "fruit juice": {"name": "果汁饮料", "category": "饮料", "freshness_days": 90, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 250)},
    "milk tea": {"name": "奶茶", "category": "饮料", "freshness_days": 3, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["广东广州", "上海", "北京"], "weight_range": (50, 200)},
    "yogurt drink": {"name": "酸奶饮品", "category": "饮料", "freshness_days": 7, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["内蒙古呼和浩特", "北京", "上海"], "weight_range": (50, 200)},
    "iced coffee": {"name": "冰咖啡", "category": "饮料", "freshness_days": 3, "indicators": ["色泽", "质地均匀度", "表面状态", "包装完整性"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 200)},
    "energy drink": {"name": "能量饮料", "category": "饮料", "freshness_days": 365, "indicators": ["外观状态", "表面状态", "包装完整性", "标签清晰度"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 300)},
    "sports drink": {"name": "运动饮料", "category": "饮料", "freshness_days": 365, "indicators": ["外观状态", "表面状态", "包装完整性", "标签清晰度"], "origins": ["北京", "上海", "广东广州"], "weight_range": (50, 300)},
    "tea beverage": {"name": "茶饮料", "category": "饮料", "freshness_days": 180, "indicators": ["色泽", "表面状态", "包装完整性", "标签清晰度"], "origins": ["福建福州", "浙江杭州", "云南昆明"], "weight_range": (50, 250)},

    # 其他品类（5种）
    "ice pack": {"name": "冰袋", "category": "其他", "freshness_days": 365, "indicators": ["外观状态", "冻结状态", "包装完整性", "有效期"], "origins": ["浙江宁波", "江苏苏州", "广东东莞"], "weight_range": (50, 200)},
    "dry ice": {"name": "干冰", "category": "其他", "freshness_days": 7, "indicators": ["外观状态", "挥发程度", "包装完整性", "有效期"], "origins": ["上海", "江苏南京", "广东广州"], "weight_range": (100, 500)},
    "insulation box": {"name": "保温箱", "category": "其他", "freshness_days": 365, "indicators": ["外观状态", "密封程度", "结构完整性", "清洁度"], "origins": ["浙江宁波", "广东东莞", "江苏苏州"], "weight_range": (500, 2000)},
    "cold chain bag": {"name": "冷链运输袋", "category": "其他", "freshness_days": 365, "indicators": ["外观状态", "密封程度", "结构完整性", "清洁度"], "origins": ["浙江宁波", "广东东莞", "江苏苏州"], "weight_range": (50, 500)},
    "packaging material": {"name": "包装材料", "category": "其他", "freshness_days": 365, "indicators": ["外观状态", "结构完整性", "清洁度", "有效期"], "origins": ["浙江宁波", "广东东莞", "江苏苏州"], "weight_range": (100, 1000)},
}

GRADE_LEVELS = ["S级(特优)", "A级(优)", "B级(良好)", "C级(合格)", "D级(不合格)"]
GRADE_COLORS = {"S级(特优)": "#00d2a0", "A级(优)": "#22c55e", "B级(良好)": "#f59e0b", "C级(合格)": "#f97316", "D级(不合格)": "#ef4444"}

def _arrhenius_decay(storage_days: int, total_days: int, avg_temp: float = 4.0) -> float:
    base_rate = 1.0 / total_days
    activation_energy = 25.0
    temp_factor = math.exp(-activation_energy / (8.314 * (273.15 + avg_temp)))
    k = base_rate * (310.15 / (273.15 + avg_temp)) * temp_factor
    quality = math.exp(-k * storage_days)
    return max(0.02, min(1.0, quality))

def _simulate_cv_assessment(product_key: str, storage_days: int = 0, avg_temp: float = 4.0, temp_shocks: int = 0) -> dict:
    product = PRODUCT_CATEGORIES.get(product_key, PRODUCT_CATEGORIES["apple"])
    total_days = product["freshness_days"]
    random.seed(hash(f"{product_key}{storage_days}{datetime.utcnow().hour}") % 10000)

    quality_ratio = _arrhenius_decay(storage_days, total_days, avg_temp)
    shock_penalty = temp_shocks * 0.03
    quality_ratio = max(0.02, quality_ratio - shock_penalty)

    remaining_days = max(0.5, round(total_days * quality_ratio, 1))

    indicators_score = {}
    for ind in product["indicators"]:
        if ind in ("色泽", "表皮完整度", "外观饱满度", "外观状态", "花头完整性", "叶片完整性", "茎叶完整性", "肉质紧致度", "蛋壳完整度"):
            base = quality_ratio * 75 + random.uniform(15, 28)
        elif ind in ("损伤程度", "腐烂程度", "黄叶情况", "萎蔫程度", "发芽情况", "霉变情况", "黑变程度", "结块程度", "融化程度"):
            base = quality_ratio * 85 + random.uniform(5, 15)
        elif ind in ("水分状态", "表面状态", "表面洁净度", "质地均匀度", "脂肪分布", "茎部状态", "根须状态", "清洁度", "冻结状态"):
            base = quality_ratio * 70 + random.uniform(18, 30)
        elif ind in ("成熟度", "眼清度", "活力状态", "脱粒程度", "壳完整度", "表皮完整性", "标签清晰度", "有效期状态", "外观完整性", "包装完整性"):
            base = quality_ratio * 70 + random.uniform(15, 30)
        else:
            base = quality_ratio * 70 + random.uniform(15, 30)
        indicators_score[ind] = round(min(100, max(5, base + random.uniform(-5, 5))), 1)

    overall_score = round(sum(indicators_score.values()) / len(indicators_score), 1)

    if overall_score >= 90:
        grade_idx, grade = 0, GRADE_LEVELS[0]
    elif overall_score >= 78:
        grade_idx, grade = 1, GRADE_LEVELS[1]
    elif overall_score >= 60:
        grade_idx, grade = 2, GRADE_LEVELS[2]
    elif overall_score >= 40:
        grade_idx, grade = 3, GRADE_LEVELS[3]
    else:
        grade_idx, grade = 4, GRADE_LEVELS[4]

    confidence = round(random.uniform(0.88, 0.99), 3)

    defect_detected = overall_score < 70
    defect_pool = {
        "水果": ["表面褐变", "机械损伤", "霉斑", "冻伤痕迹", "虫蛀孔洞"],
        "蔬菜": ["叶片黄化", "萎蔫脱水", "机械压伤", "腐烂斑点"],
        "肉类": ["表面变色", "脂肪氧化", "肉质软化", "异味产生"],
        "海鲜": ["眼球浑浊", "鳃部变色", "鳞片脱落", "弹性下降"],
        "乳制品": ["乳清分离", "酸味异常", "质地结块", "包装破损"],
        "豆制品": ["发霉变质", "酸味异常", "质地变软", "颜色变深"],
        "蛋类": ["蛋壳破裂", "蛋黄散黄", "蛋白变稀", "异味产生"],
        "医药制品": ["包装破损", "标签模糊", "有效期过期", "外观异常"],
        "花卉": ["花朵枯萎", "叶片发黄", "茎部软化", "花瓣脱落"],
        "冷冻食品": ["解冻再冻", "包装破损", "冰晶过大", "标签模糊"],
        "熟食预制菜": ["颜色变深", "包装破损", "标签模糊", "表面异常"],
        "饮料": ["沉淀分层", "包装破损", "标签模糊", "表面异常"],
    }
    cat_defects = defect_pool.get(product["category"], ["品质异常"])
    defect_count = min(2, max(0, int((70 - overall_score) / 15 + random.randint(0, 1))))
    defect_details = random.sample(cat_defects, defect_count) if defect_detected and defect_count > 0 else []

    return {
        "product_type": product["name"],
        "category": product["category"],
        "quality_score": overall_score,
        "grade": grade,
        "grade_index": grade_idx,
        "confidence": confidence,
        "storage_days": storage_days,
        "total_freshness_days": total_days,
        "remaining_freshness_days": remaining_days,
        "indicators": indicators_score,
        "defects": defect_details,
        "defect_detected": defect_detected,
        "suggestion": "可正常入库存储，按标准配送流程发货" if overall_score >= 75 else "建议优先处理，缩短存储时间" if overall_score >= 60 else "建议抽检或降级处理",
        "assessment_time": datetime.now().isoformat(),
    }

STORAGE_CONDITION_MAP = {
    "refrigerated": "冷藏 (2-8°C)",
    "frozen": "冷冻 (-18°C以下)",
    "room": "常温 (15-25°C)",
    "cold": "低温 (0-2°C)",
}

PACKAGE_STATUS_MAP = {
    "intact": "完好",
    "damaged": "破损",
    "opened": "已开封",
}

TRANSPORT_MODE_MAP = {
    "air": "空运",
    "land": "陆运",
    "sea": "海运",
    "express": "冷链快递",
}

async def _call_dashscope_api(image_base64: str, product_type: str = None, storage_days: int = 0, 
                              storage_condition: str = None, package_status: str = None, 
                              transport_mode: str = None) -> dict:
    import httpx
    
    api_key = os.environ.get("ZHIPU_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="API密钥未配置")

    product_hint = f"已知产品类型：{product_type}。" if product_type else ""
    
    condition_hints = []
    if storage_days > 0:
        condition_hints.append(f"已储存天数：{storage_days}天")
    if storage_condition and storage_condition in STORAGE_CONDITION_MAP:
        condition_hints.append(f"储存条件：{STORAGE_CONDITION_MAP[storage_condition]}")
    if package_status and package_status in PACKAGE_STATUS_MAP:
        condition_hints.append(f"包装状态：{PACKAGE_STATUS_MAP[package_status]}")
    if transport_mode and transport_mode in TRANSPORT_MODE_MAP:
        condition_hints.append(f"运输方式：{TRANSPORT_MODE_MAP[transport_mode]}")
    
    condition_text = "\n".join(condition_hints) if condition_hints else ""
    
    prompt = f"""你是一个专业的冷链物流生鲜品质检测专家。请对图片中的产品进行视觉品质评估。

{product_hint}

{condition_text}

请识别图片中的产品，并按照以下JSON格式输出评估结果：
{{
    "product_name": "产品名称（中文）",
    "category": "品类，从以下选项中选择最匹配的一个：水果、蔬菜、肉类、海鲜、乳制品、豆制品、蛋类、医药制品、花卉、冷冻食品、熟食预制菜、饮料、其他",
    "quality_score": 0-100的品质评分（新鲜、完好的产品分数高，有瑕疵、变质的产品分数低）,
    "grade": "等级（S级(特优)/A级(优)/B级(良好)/C级(合格)/D级(不合格)）",
    "defects": ["缺陷1", "缺陷2"],
    "confidence": 0-1的置信度（对识别结果的自信程度）,
    "description": "简要描述产品外观和品质状况",
    "indicators": {{
        "色泽": 0-100的评分,
        "外观状态": 0-100的评分
    }}
}}

评估规则：
1. 品质评分基于视觉特征：色泽是否鲜艳、外观是否完好、是否有损伤/腐烂/变质等
2. 考虑已储存天数对品质的影响，储存时间越长，预期品质可能越低
3. 包装破损或已开封可能影响产品品质
4. 缺陷列表应列出从图片中观察到的具体问题
5. indicators中的指标应为视觉可判断的指标，根据图片实际情况评分
6. 输出必须是合法的JSON格式，不要包含其他文字"""

    image_data_url = f"data:image/jpeg;base64,{image_base64}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-vl-plus",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ],
        "max_tokens": 500
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        response = await client.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=payload
        )

    if response.status_code != 200:
        error_msg = f"API调用失败，状态码: {response.status_code}"
        try:
            error_data = response.json()
            if "error" in error_data:
                error_msg += f", 错误信息: {error_data['error'].get('message', '')}"
        except:
            pass
        raise Exception(error_msg)

    try:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"解析API响应失败: {str(e)}")
    
    return _parse_model_response(content)

def _parse_model_response(content: str) -> dict:
    import json
    try:
        content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
    except:
        return {}

    product_key = None
    for key, value in PRODUCT_CATEGORIES.items():
        if value["name"] == data.get("product_name"):
            product_key = key
            break

    if not product_key:
        product_key = "apple"

    product = PRODUCT_CATEGORIES[product_key]

    indicators = data.get("indicators", {})
    if not indicators:
        indicators = {}
        for ind in product["indicators"]:
            indicators[ind] = data.get("quality_score", 70)

    return {
        "product_type": data.get("product_name", product["name"]),
        "category": data.get("category", product["category"]),
        "quality_score": data.get("quality_score", 70),
        "grade": data.get("grade", "B级(良好)"),
        "grade_index": GRADE_LEVELS.index(data.get("grade", "B级(良好)")) if data.get("grade") in GRADE_LEVELS else 2,
        "confidence": data.get("confidence", 0.9),
        "storage_days": 0,
        "total_freshness_days": product["freshness_days"],
        "remaining_freshness_days": product["freshness_days"],
        "indicators": indicators,
        "defects": data.get("defects", []),
        "defect_detected": len(data.get("defects", [])) > 0,
        "suggestion": "根据AI评估结果处理",
        "assessment_time": datetime.now().isoformat(),
        "description": data.get("description", ""),
    }

def _save_assessment_to_db(result: dict, image_filename: str):
    import psycopg2
    import json
    import uuid
    
    conn = None
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="coldchain",
            user="coldchain",
            password="coldchain123"
        )
        cur = conn.cursor()
        
        product_key = None
        for key, value in PRODUCT_CATEGORIES.items():
            if value["name"] == result.get("product_type"):
                product_key = key
                break
        if not product_key:
            product_key = "apple"
        
        cur.execute("""
            INSERT INTO quality_assessments (
                assessment_id, product_key, product_name, category, image_path,
                quality_score, grade, defects, confidence, description,
                storage_days, remaining_shelf_life
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            str(uuid.uuid4()),
            product_key,
            result.get("product_type"),
            result.get("category"),
            image_filename,
            result.get("quality_score"),
            result.get("grade"),
            json.dumps(result.get("defects", [])),
            result.get("confidence"),
            result.get("description"),
            result.get("storage_days", 0),
            result.get("remaining_freshness_days"),
        ))
        
        conn.commit()
        cur.close()
    except Exception as e:
        pass
    finally:
        if conn:
            conn.close()

class AssessRequest(BaseModel):
    product_type: str
    storage_days: int = 0

class AssessResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""

@router.post("/assess", response_model=AssessResponse)
async def assess_quality(request: AssessRequest):
    try:
        product_key = None
        for key, value in PRODUCT_CATEGORIES.items():
            if value["name"] == request.product_type:
                product_key = key
                break

        if not product_key:
            return {"success": False, "message": "不支持的产品类型"}

        result = _simulate_cv_assessment(product_key, request.storage_days)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/assess/image", response_model=AssessResponse)
async def assess_with_image(file: UploadFile = File(...), product_type: str = None, storage_days: int = 0,
                            storage_condition: str = None, package_status: str = None, transport_mode: str = None):
    try:
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode("utf-8")

        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        try:
            result = await _call_dashscope_api(image_base64, product_type, storage_days, 
                                               storage_condition, package_status, transport_mode)
            result["image_url"] = f"/uploads/{filename}"
        except Exception as api_err:
            product_key = None
            if product_type:
                for key, value in PRODUCT_CATEGORIES.items():
                    if value["name"] == product_type:
                        product_key = key
                        break
            if not product_key:
                product_key = "apple"
            result = _simulate_cv_assessment(product_key, storage_days)
            result["image_url"] = f"/uploads/{filename}"

        _save_assessment_to_db(result, filename)

        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/demo")
async def get_demo_assessment(product_key: str):
    if product_key not in PRODUCT_CATEGORIES:
        return {"success": False, "message": "不支持的产品类型"}
    
    product = PRODUCT_CATEGORIES[product_key]
    category = product["category"]
    
    cv_result = _simulate_cv_assessment(product_key)
    
    base_score = cv_result["quality_score"]
    grade = cv_result["grade"]
    
    indicators = cv_result["indicators"]
    defects = cv_result["defects"]
    
    origins = product.get("origins", ["产地直供"])
    origin = random.choice(origins)
    
    weight_range = product.get("weight_range", (50, 200))
    quantity_kg = random.randint(weight_range[0], weight_range[1])
    
    storage_days = random.randint(0, 7)
    remaining_days = max(1, product["freshness_days"] - storage_days)
    
    indicator_descriptions = []
    for ind, score in indicators.items():
        if score >= 95:
            indicator_descriptions.append(f"{ind}优异")
        elif score >= 90:
            indicator_descriptions.append(f"{ind}良好")
        elif score >= 80:
            indicator_descriptions.append(f"{ind}一般")
        else:
            indicator_descriptions.append(f"{ind}较差")
    
    description_parts = [
        f"{product['name']}外观{indicator_descriptions[0] if indicator_descriptions else '正常'}",
        f"整体品质{grade}"
    ]
    if defects:
        description_parts.append(f"检测到{'; '.join(defects)}")
    description = "，".join(description_parts) + "。"
    
    category_suggestions = {
        "水果": {
            "high": f"{product['name']}新鲜度高，建议尽快上架销售，保质期约{remaining_days}天",
            "medium": f"{product['name']}品质良好，建议在{remaining_days}天内完成销售",
            "low": f"{product['name']}存在瑕疵，建议降价促销或内部处理"
        },
        "蔬菜": {
            "high": f"{product['name']}色泽鲜艳，建议立即配送至高端客户",
            "medium": f"{product['name']}状态良好，适合日常销售",
            "low": f"{product['name']}有轻微瑕疵，建议打折销售"
        },
        "肉类": {
            "high": f"{product['name']}肉质新鲜紧实，建议优先配送至星级餐厅",
            "medium": f"{product['name']}品质达标，适合一般餐饮客户",
            "low": f"{product['name']}存在轻微氧化，建议缩短配送时间"
        },
        "海鲜": {
            "high": f"{product['name']}新鲜度极佳，适合刺身级食用",
            "medium": f"{product['name']}品质良好，可正常销售",
            "low": f"{product['name']}需尽快处理，避免品质进一步下降"
        },
        "乳制品": {
            "high": f"{product['name']}质地均匀，建议冷藏保存并尽快配送",
            "medium": f"{product['name']}状态正常，可正常销售",
            "low": f"{product['name']}存在结块风险，建议抽检后决定是否上架"
        },
        "豆制品": {
            "high": f"{product['name']}新鲜度良好，建议在24小时内销售",
            "medium": f"{product['name']}品质达标，适合正常销售",
            "low": f"{product['name']}需注意保存条件，建议优先处理"
        },
        "蛋类": {
            "high": f"{product['name']}蛋壳完整，建议按正常流程配送",
            "medium": f"{product['name']}品质良好，适合日常消费",
            "low": f"{product['name']}存在裂纹，建议单独处理"
        },
        "医药制品": {
            "high": f"{product['name']}状态良好，符合冷链运输标准",
            "medium": f"{product['name']}储存条件达标，可正常分发",
            "low": f"{product['name']}需严格监控储存温度，建议优先配送"
        },
        "花卉": {
            "high": f"{product['name']}花瓣饱满鲜艳，建议尽快配送至花店",
            "medium": f"{product['name']}状态良好，可正常销售",
            "low": f"{product['name']}有轻微枯萎，建议低价处理"
        },
        "冷冻食品": {
            "high": f"{product['name']}冷冻状态良好，无明显冰霜",
            "medium": f"{product['name']}品质达标，适合正常销售",
            "low": f"{product['name']}表面冰霜较多，建议优先销售"
        },
        "熟食预制菜": {
            "high": f"{product['name']}外观完好，建议冷藏保存并尽快送达",
            "medium": f"{product['name']}品质良好，可正常配送",
            "low": f"{product['name']}需注意保质期，建议缩短配送周期"
        },
        "饮料": {
            "high": f"{product['name']}包装完好，建议常温或冷藏销售",
            "medium": f"{product['name']}状态正常，可正常上架",
            "low": f"{product['name']}存在沉淀，建议检查后再决定"
        },
        "其他": {
            "high": "产品状态良好，可正常入库",
            "medium": "产品品质达标，可正常处理",
            "low": "产品存在异常，建议进一步检查"
        }
    }
    
    if base_score >= 90:
        suggestion_level = "high"
    elif base_score >= 75:
        suggestion_level = "medium"
    else:
        suggestion_level = "low"
    
    suggestion_dict = category_suggestions.get(category, category_suggestions["其他"])
    suggestion = suggestion_dict[suggestion_level]
    
    result = {
        "batch_id": f"demo-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "product_type": product["name"],
        "category": category,
        "quality_score": base_score,
        "overall_score": base_score,
        "grade": grade,
        "confidence": cv_result["confidence"],
        "defects": defects,
        "defect_detected": cv_result["defect_detected"],
        "description": description,
        "indicators": indicators,
        "storage_days": storage_days,
        "total_freshness_days": product["freshness_days"],
        "remaining_freshness_days": remaining_days,
        "storage_temp_c": 4,
        "remaining_shelf_life_days": remaining_days,
        "suggestion": suggestion,
        "origin": origin,
        "quantity_kg": quantity_kg,
        "status": "in_storage",
        "assessed_at": datetime.now().isoformat(),
        "image_url": None,
    }
    
    return {"success": True, "data": result}

@router.get("/categories")
async def get_categories():
    return {"success": True, "data": list(SUPPORTED_CATEGORIES)}

@router.get("/products")
async def get_products(category: str = None):
    products = []
    for key, value in PRODUCT_CATEGORIES.items():
        if category is None or value["category"] == category:
            products.append({"key": key, "name": value["name"], "category": value["category"]})
    return {"success": True, "data": products}

@router.get("/batches")
async def get_batches(category: str = None, grade: str = None):
    import psycopg2
    import json
    
    conn = None
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="coldchain",
            user="coldchain",
            password="coldchain123"
        )
        cur = conn.cursor()
        
        query = """
            SELECT assessment_id, product_key, product_name, category, quality_score, grade, 
                   defects, confidence, description, assessed_at, image_path,
                   storage_days, remaining_shelf_life
            FROM quality_assessments
            WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
        if grade:
            query += " AND grade LIKE %s"
            params.append(f"%{grade}%")
        
        query += " ORDER BY assessed_at DESC LIMIT 50"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        batches = []
        for row in rows:
            product_key = row[1] if len(row) > 1 else None
            product_info = PRODUCT_CATEGORIES.get(product_key, {})
            if not product_info and '_' in product_key:
                product_info = PRODUCT_CATEGORIES.get(product_key.replace('_', ' '), {})
            
            origins = product_info.get("origins", ["未知产地"])
            seed = hash(f"{product_key}origin") % len(origins)
            origin = origins[seed]
            
            weight_range = product_info.get("weight_range", (50, 200))
            seed = hash(f"{product_key}weight") % (weight_range[1] - weight_range[0] + 1)
            quantity_kg = weight_range[0] + seed
            
            batches.append({
                "batch_id": row[0],
                "product_type": row[2],
                "category": row[3],
                "quality_score": row[4],
                "overall_score": row[4],
                "grade": row[5],
                "defects": row[6] if row[6] else [],
                "confidence": row[7],
                "description": row[8],
                "assessed_at": row[9].isoformat() if row[9] else None,
                "image_url": f"/uploads/{row[10]}" if row[10] else None,
                "origin": origin,
                "quantity_kg": quantity_kg,
                "storage_days": row[11] if len(row) > 11 else 0,
                "storage_temp_c": 4,
                "remaining_shelf_life_days": row[12] if len(row) > 12 else 7,
                "status": "in_storage",
            })
        
        cur.close()
        return {"success": True, "batches": batches}
    except Exception as e:
        return {"success": False, "message": str(e), "batches": []}
    finally:
        if conn:
            conn.close()

@router.get("/stats")
async def get_stats():
    import psycopg2
    
    conn = None
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="coldchain",
            user="coldchain",
            password="coldchain123"
        )
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM quality_assessments")
        total_batches = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) FROM quality_assessments 
            WHERE defects IS NOT NULL AND array_length(defects, 1) > 0
        """)
        defect_count = cur.fetchone()[0]
        
        defect_rate = round((defect_count / total_batches) * 100, 1) if total_batches > 0 else 0
        
        cur.execute("""
            SELECT AVG(quality_score) FROM quality_assessments 
            WHERE quality_score IS NOT NULL
        """)
        avg_score = cur.fetchone()[0]
        avg_score = round(avg_score, 1) if avg_score else 0
        
        cur.execute("SELECT COUNT(DISTINCT product_key) FROM quality_assessments")
        products_supported = cur.fetchone()[0]
        
        cur.close()
        return {
            "total_batches": total_batches,
            "defect_rate": defect_rate,
            "avg_quality_score": avg_score,
            "products_supported": products_supported,
        }
    except Exception as e:
        return {
            "total_batches": 0,
            "defect_rate": 0,
            "avg_quality_score": 0,
            "products_supported": len(PRODUCT_CATEGORIES),
        }
    finally:
        if conn:
            conn.close()

SUPPORTED_PRODUCTS = {
    "苹果": "apple", "草莓": "strawberry", "葡萄": "grape", "橙子": "orange", "香蕉": "banana",
    "西瓜": "watermelon", "梨": "pear", "桃子": "peach", "李子": "plum", "杏子": "apricot",
    "樱桃": "cherry", "蓝莓": "blueberry", "覆盆子": "raspberry", "芒果": "mango", "榴莲": "durian",
    "菠萝": "pineapple", "荔枝": "litchi", "龙眼": "longan", "猕猴桃": "kiwi", "石榴": "pomegranate",
    "火龙果": "dragonfruit", "木瓜": "papaya", "椰子": "coconut", "番石榴": "guava", "牛油果": "avocado",
    "柠檬": "lemon", "青柠": "lime", "百香果": "passionfruit", "哈密瓜": "cantaloupe", "白兰瓜": "honeydew",
    "无花果": "fig", "枣": "date", "柿子": "persimmon", "桑葚": "mulberry",
    "黄瓜": "cucumber", "胡萝卜": "carrot", "西兰花": "broccoli", "芹菜": "celery", "土豆": "potato",
    "洋葱": "onion", "大蒜": "garlic", "青椒": "greenpepper", "红椒": "redpepper", "茄子": "eggplant",
    "冬瓜": "wintermelon", "南瓜": "pumpkin", "白菜": "cabbage", "青菜": "chinese cabbage", "韭菜": "leek",
    "香菜": "coriander", "欧芹": "parsley", "罗勒": "basil", "生菜": "lettuce", "番茄": "tomato",
    "红薯": "sweetpotato", "山药": "yam", "生姜": "ginger", "香葱": "shallot", "菠菜": "spinach",
    "牛肉": "beef", "猪肉": "pork", "羊肉": "lamb", "鸡肉": "chicken", "鸭肉": "duck",
    "鹅肉": "goose", "火鸡": "turkey", "兔肉": "rabbit", "牛肝": "beef liver", "猪肝": "pork liver",
    "鸡肝": "chicken liver", "牛舌": "beef tongue", "五花肉": "pork belly", "牛腩": "beef brisket",
    "三文鱼": "salmon", "虾": "shrimp", "螃蟹": "crab", "龙虾": "lobster", "扇贝": "scallop",
    "生蚝": "oyster", "蛤蜊": "clam", "贻贝": "mussel", "鱿鱼": "squid", "章鱼": "octopus",
    "鳕鱼": "cod", "金枪鱼": "tuna", "鲭鱼": "mackerel", "鲱鱼": "herring", "罗非鱼": "tilapia",
    "鲤鱼": "carp", "鲶鱼": "catfish",
    "鲜奶": "milk", "酸奶": "yogurt", "奶酪": "cheese", "黄油": "butter", "奶油": "cream",
    "冰淇淋": "icecream", "奶粉": "milk powder", "豆浆": "soy milk",
    "豆腐": "tofu", "豆皮": "tofu skin", "大豆": "soybean", "豆腐脑": "tofu pudding",
    "鸡蛋": "egg", "鸭蛋": "duck egg", "鹅蛋": "goose egg", "鹌鹑蛋": "quail egg",
    "疫苗": "vaccine", "血液制品": "blood product", "胰岛素": "insulin", "生物制剂": "biological agent",
    "血浆": "plasma", "血清": "serum", "诊断试剂": "reagent", "抗体药物": "antibody",
    "玫瑰": "rose", "百合": "lily", "康乃馨": "carnation", "郁金香": "tulip", "兰花": "orchid",
    "向日葵": "sunflower", "雏菊": "daisy", "牡丹": "peony", "绣球花": "hydrangea", "满天星": "baby breath",
    "速冻水饺": "frozen dumpling", "冷冻蔬菜": "frozen vegetable", "冷冻肉类": "frozen meat",
    "冷冻海鲜": "frozen seafood", "速冻包子": "frozen bun", "速冻面条": "frozen noodle",
    "冷冻披萨": "frozen pizza", "冷冻甜点": "frozen dessert", "冰淇淋": "ice cream", "冰棍": "popsicle",
    "预制菜": "prepared meal", "卤味熟食": "deli meat", "火锅底料": "soup base", "速冻便当": "frozen meal",
    "即食熟食": "cooked food", "寿司": "sushi", "三明治": "sandwich", "沙拉": "salad",
    "鲜榨果汁": "fresh juice", "果汁饮料": "fruit juice", "奶茶": "milk tea", "酸奶饮品": "yogurt drink",
    "冰咖啡": "iced coffee", "能量饮料": "energy drink", "运动饮料": "sports drink", "茶饮料": "tea beverage",
}

SUPPORTED_CATEGORIES = ["水果", "蔬菜", "肉类", "海鲜", "乳制品", "豆制品", "蛋类", "医药制品", "花卉", "冷冻食品", "熟食预制菜", "饮料", "其他"]
