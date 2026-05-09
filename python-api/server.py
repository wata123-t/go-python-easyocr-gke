import grpc
from concurrent import futures
import pb.predict_pb2 as pb2
import pb.predict_pb2_grpc as pb2_grpc
import time
import json
import sys
import os
import psutil
import io
import numpy as np
import easyocr
from PIL import Image

# Pod名は起動時に一度だけ取得
POD_NAME = os.environ.get('HOSTNAME', 'unknown-pod')

# OCRエンジンのロード（起動時に1回だけ実行）
# GCPのCPU環境を想定し gpu=False としていますが、GPUがある場合は環境変数等で切り替えてください
print(f"[{POD_NAME}] Loading EasyOCR Reader...")
reader = easyocr.Reader(['en', 'ja'], gpu=False)

class Predictor(pb2_grpc.PredictorServicer):
    def Predict(self, request, context):
        # CPU計測リセット
        psutil.cpu_percent(interval=None) 
        start_time = time.time()
        
        # 1. gRPCメタデータからIDを抽出
        metadata = dict(context.invocation_metadata())
        request_id = metadata.get('x-correlation-id', 'unknown')

        result_text = ""
        is_success = False
        
        try:
            # 2. EasyOCRによる推論
            img = Image.open(io.BytesIO(request.image_data))
            img_np = np.array(img)
            
            # OCR実行
            ocr_results = reader.readtext(img_np, detail=1)
            
            # 結果の整形
            detected_texts = [res[1] for res in ocr_results]
            result_text = ", ".join(detected_texts) if detected_texts else "No text detected"
            is_success = True
            
        except Exception as e:
            result_text = f"Error: {str(e)}"
            print(f"[{POD_NAME}] OCR Error: {e}")

        # 3. クラウドロギング用の構造化ログ出力
        duration_ms = int((time.time() - start_time) * 1000)
        cpu_usage = psutil.cpu_percent(interval=None)

        log_entry = {
            "severity": "INFO" if is_success else "ERROR",
            "request_id": request_id,
            "step": "python-ocr-inference",
            "duration_ms": duration_ms,
            "is_success": is_success,
            "detected_count": len(ocr_results) if is_success else 0,
            "cpu_usage": cpu_usage,
            "pid": os.getpid(),
            "pod_name": POD_NAME,
            "message": f"OCR completed: {result_text[:50]}..." # ログが長くなりすぎないよう制限
        }
        print(json.dumps(log_entry))
        sys.stdout.flush()

        return pb2.PredictResponse(result=result_text)


def serve():
    # サイドカー構成に最適化した設定
    server_options = [
        # localhost間通信なので、接続寿命は長くしてパフォーマンスを優先
        ('grpc.max_connection_age_ms', 0), # 0は無制限（切らない）
        
        # 1つのコネクションで同時に受け付けるリクエスト数
        # 1コア制限なら、窓口は2〜3あれば十分（1つ処理中に次を受付可能にする）
        ('grpc.max_concurrent_streams', 5),
        
        # 通信の安定性を保つためのKeepalive設定
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.permit_keepalive_without_calls', True),
    ]
    
    server = grpc.server(
        # ワーカー数は「2〜3」程度がベスト。
        # 1コア制限下では、これ以上増やしてもCPUの奪い合いで遅くなるだけ。
        futures.ThreadPoolExecutor(max_workers=3),
        options=server_options
    )
    
    pb2_grpc.add_PredictorServicer_to_server(Predictor(), server)
    
    # サイドカーなので、localhost(127.0.0.1)からの接続のみ受け付ける設定でもOK
    # 汎用性を持たせるなら [::]:50051 のままでも問題ありません
    server.add_insecure_port('[::]:50051')
    
    server.start()
    print(f"[{POD_NAME}] Sidecar OCR Server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

