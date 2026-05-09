FROM python:3.12-slim

# 1. システムライブラリのインストール
# psutilのビルドに必要な gcc/python3-dev と、EasyOCRに必要なライブラリを統合
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Pythonライブラリのインストール（キャッシュを活かすため先に実行）
COPY python-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. EasyOCRモデルの事前ダウンロード
# モデルの保存先を /root/.EasyOCR に固定してイメージに焼き込みます
RUN python -c "import easyocr; easyocr.Reader(['en', 'ja'], gpu=False)"

# 4. アプリケーションファイルのコピー
# server.py を修正しても、ここまでの重い処理（pipやモデル取得）は再利用されます
COPY pb ./pb
COPY python-api/server.py .

# gRPCポートの開放
EXPOSE 50051

CMD ["python", "server.py"]
