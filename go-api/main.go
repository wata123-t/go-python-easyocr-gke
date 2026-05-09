package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/shirou/gopsutil/v4/cpu"
	"github.com/google/uuid"
	
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/metadata"

	"go-api/pb"
)

// Cloud Logging用の構造化ログ
type CloudLog struct {
	Severity   string  `json:"severity"`
	RequestID  string  `json:"request_id"`
	Step       string  `json:"step"`
	LatencyMs  int64   `json:"duration_ms"`
	IsSuccess  bool    `json:"is_success"`
	CPUUsage   float64 `json:"cpu_usage"`
	PodName    string  `json:"pod_name"`
	Message    string  `json:"message"`
	Expected   string  `json:"expected"`
	IsMatch    bool    `json:"is_match"`
	K6SendTime int64   `json:"k6_send_time"` // ★追加: k6の送信時刻
}

func main() {
	// ホスト名を取得
	podName, _ := os.Hostname()
	if podName == "" {
		podName = "unknown-go-pod"
	}

	// 環境変数からタイムアウト時間を取得(失敗時は15sec)
	timeoutStr := os.Getenv("TIMEOUT_SECONDS")
	timeoutSec, err := strconv.Atoi(timeoutStr)
	if err != nil {
		timeoutSec = 15
	}

	// gRPC 接続設定 : ロードバランシング設定(round_robin)
	//serviceConfig := `{"loadBalancingConfig": [{"round_robin":{}}]}`
	targetAddr := os.Getenv("PYTHON_RPC_ADDR")
	if targetAddr == "" {
		targetAddr = "localhost:50051"
	}

	conn, err := grpc.Dial(
		targetAddr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		//grpc.WithDefaultServiceConfig(serviceConfig),
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Time:                60 * time.Second,
			Timeout:           20 * time.Second,
			PermitWithoutStream: true,
		}),
	)
	if err != nil {
		log.Fatalf("gRPC接続失敗: %v", err)
	}
	defer conn.Close()
	client := pb.NewPredictorClient(conn)

	r := gin.Default()

	r.POST("/predict", func(c *gin.Context) {
		startTime := time.Now()

		// 1. リクエストIDの取得
		requestID := c.GetHeader("X-Correlation-ID")
		
		// もしヘッダーになければ、UUID v4 を新しく生成する
		if requestID == "" {
			// uuid.NewRandom() は高度な乱数生成器を使用するため、衝突の確率は天文学的に低いです
			newID, err := uuid.NewRandom()
			if err != nil {
				// 万が一生成に失敗した際のフォールバック（極めて稀）
				requestID = fmt.Sprintf("gen-%d", startTime.UnixNano())
			} else {
			 	requestID = newID.String()
			}
		}


		// ★追加: k6送信時刻ヘッダーの取得とパース
		k6SendTimeStr := c.GetHeader("X-K6-Send-Time")
		k6SendTime, _ := strconv.ParseInt(k6SendTimeStr, 10, 64)

		expectedText := c.GetHeader("X-Expected-Text")

		// 2. 画像データの読み込み
		file, header, err := c.Request.FormFile("image")
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "ファイル取得エラー"})
			return
		}
		defer file.Close()

		imageData, _ := io.ReadAll(file)
		log.Printf("[%s] 受信: %s (%d bytes)", requestID, header.Filename, len(imageData))

		// 3. gRPCコンテキストの準備
		ctx := metadata.AppendToOutgoingContext(context.Background(), "x-correlation-id", requestID)
		ctx, cancel := context.WithTimeout(ctx, time.Duration(timeoutSec)*time.Second)
		defer cancel()

		// 4. Python OCRエンジンへリクエスト送信
		res, err := client.Predict(ctx, &pb.ImageRequest{ImageData: imageData})

		// 5. メトリクス収集とログ出力
		percent, _ := cpu.Percent(0, false)
		var cpuVal float64
		if len(percent) > 0 {
			cpuVal = percent[0]
		}

		isSuccess := (err == nil)
		duration := time.Since(startTime).Milliseconds()

		isMatch := false
		if isSuccess && expectedText != "" {
			isMatch = strings.Contains(res.Result, expectedText)
		}

		logEntry := CloudLog{
			Severity:   "INFO",
			RequestID:  requestID,
			Step:       "go-api-complete",
			LatencyMs:  duration,
			IsSuccess:  isSuccess,
			CPUUsage:   cpuVal,
			PodName:    podName,
			Expected:   expectedText,
			IsMatch:    isMatch,
			K6SendTime: k6SendTime, // ★追加
			Message:    fmt.Sprintf("OCR Processed by %s", podName),
		}

		if isSuccess {
			logEntry.Message = fmt.Sprintf("Expected: %s, Got: %s", expectedText, res.Result)
		} else {
			logEntry.Severity = "ERROR"
			logEntry.Message = fmt.Sprintf("Predict error: %v", err)
		}

		logJSON, _ := json.Marshal(logEntry)
		fmt.Println(string(logJSON))

		// 6. レスポンス返却
		if !isSuccess {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "OCR処理エラーまたはタイムアウト", "id": requestID})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "推論完了",
			"result":  res.Result,
			"id":      requestID,
		})
	})

	log.Printf("Go API Server started on :8080 (Timeout: %ds)", timeoutSec)
	r.Run(":8080")
}
