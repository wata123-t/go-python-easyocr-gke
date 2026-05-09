# 1. ビルドステージ
# 現在、golang:1.26 はまだリリースされていないため、安定版の 1.22 または 1.23 を推奨します
FROM golang:1.26-alpine AS builder

# ビルドに必要な OS パッケージ（gitなど）を追加
RUN apk add --no-cache git

WORKDIR /app

# 先にモジュールファイルをコピーしてキャッシュを効かせる
COPY go-api/go.mod go-api/go.sum ./
RUN go mod download

# プロトタイプ定義とソースコードをコピー
COPY pb ./pb
COPY go-api/ .

# ビルド実行
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# 2. 実行ステージ
FROM alpine:latest
# alpine で https 通信やタイムゾーンを扱うためのパッケージを追加
RUN apk add --no-cache ca-certificates tzdata

WORKDIR /root/

# ビルダーからバイナリのみコピー
COPY --from=builder /app/main .

# ポート開放
EXPOSE 8080

# 実行
CMD ["./main"]
