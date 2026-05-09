import os
import json
from PIL import Image, ImageDraw, ImageFont

# フォルダ作成
os.makedirs("./test_images", exist_ok=True)

# 100個の重複のない厳選英単語（3〜6文字）
words = [
    "apple", "bird", "cat", "dog", "fish", "frog", "jump", "blue", 
    "green", "book", "desk", "milk", "moon", "star", "tree", "rose", 
    "lion", "bear", "duck", "king", "queen", "lamp", "fire", "ice", 
    "snow", "rain", "wind", "ship", "boat", "car", "bus", "train",
    "gold", "iron", "wood", "road", "path", "city", "town", "home",
    "door", "wall", "room", "roof", "desk", "pen", "cup", "bowl",
    "rice", "corn", "bean", "soup", "meat", "pork", "beef", "salt",
    "leaf", "root", "stem", "seed", "lily", "pink", "red", "dark",
    "sky", "star", "sun", "cloud", "gray", "gold", "bear", "wolf",
    "deer", "fox", "owl", "hawk", "swan", "lake", "river", "sea",
    "sand", "rock", "clay", "dirt", "hill", "farm", "park", "yard",
    "shoe", "hat", "coat", "bag", "ball", "silver", "bell", "coin",
    "hand", "foot", "eye", "ear", "nose", "face", "hair", "skin"
]

# 単語数が足りない場合の保険（ユニークな100個を確実に取得）
words = list(set(words))[:100]

mapping = {}

# Windows標準のArialフォント（特大サイズ40）
try:
    font = ImageFont.truetype("arial.ttf", 40)
except IOError:
    font = ImageFont.load_default()

# 100枚生成
for i, target_text in enumerate(words, start=1):
    filename = f"{i:03d}.png"
    mapping[filename] = target_text
    
    # 黒背景の画像を作成 (横250px, 縦100px)
    img = Image.new('RGB', (250, 100), color='black')
    draw = ImageDraw.Draw(img)
    
    # 白文字でハッキリと描画
    draw.text((30, 25), target_text, fill='white', font=font)
    
    img.save(f"./test_images/{filename}")

# 正解リストをJSONで保存
with open('./test_images/mapping.json', 'w') as f:
    json.dump(mapping, f)

print(f"100枚の重複のない画像生成が完了しました。 (単語数: {len(words)})")
