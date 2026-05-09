//////////////////////////////////////////////////////////////////////////////
// ●Docker(python)
//////////////////////////////////////////////////////////////////////////////

---------------------------------------
▲1. ビルドのみ（Docker Compose）
---------------------------------------
>docker-compose build

---------------------------------------
▲2. ビルドと起動（Docker Compose）
---------------------------------------

>docker-compose up --build


docker-compose build --no-cache 

docker-compose build --no-cache go-api && docker-compose up -d go-api

個別実行だが、特に使用しないでよい、タグ名がつくので次のやり方が変わる
>docker-compose up --build python-api
>docker-compose up --build go-api


デフォルトだと以下のタグが付いている
[+] Building 2/2
 ✔ step_3_v3-go-api      Built                                                                                                                          0.0s 
 ✔ step_3_v3-python-api  Built                                                                                                                          0.0s 

---------------------------------------
▲2. タグを付ける
---------------------------------------
Go-API にタグを付ける, Python-API にタグを付ける

docker tag  step_3_v3-go-api  asia-northeast1-docker.pkg.dev/acquired-shape-470706-k0/ocr-images/go-api:latest
docker tag  step_3_v3-python-api asia-northeast1-docker.pkg.dev/acquired-shape-470706-k0/ocr-images/python-api:latest

----------------------------------------------------------
▲3. GCP へのプッシュ（アップロード）
----------------------------------------------------------
# 認証（まだの場合は実行してください。1回実行済みなら不要です）
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# Go-API をプッシュ
# Python-API をプッシュ

docker push asia-northeast1-docker.pkg.dev/acquired-shape-470706-k0/ocr-images/go-api:latest
docker push asia-northeast1-docker.pkg.dev/acquired-shape-470706-k0/ocr-images/python-api:latest

python 実行 ( 12:00 - 12:11 )終了

//////////////////////////////////////////////////////////////////////////////
// ●Helm
//////////////////////////////////////////////////////////////////////////////

------------------------------------------
▲1. push 後の初回は(もしくは uninstall あと)
------------------------------------------
>
GKEクラスター（クラウド上のサーバー群）を terraform で作成した直後の状態では、あなたのPCの helm や kubectl は以下のことを知りません。
どこに接続すればいいか？（クラスターのIPアドレス）
誰として接続するか？（あなたの認証トークンや証明書）
get-credentials を実行することで、Google Cloudからこれらの情報をダウンロードし、あなたのPC内の設定ファイル（~/.kube/config）に書き込みます。これにより、helm が「あ、この住所に、この鍵を使って命令を送ればいいんだな」と理解できるようになります。

>gcloud container clusters get-credentials ocr-cluster --zone asia-northeast1-a --project acquired-shape-470706-k0


------------------------------------------
▲2. その後は、以下を行う
------------------------------------------


helm install ocr-app ./chart

>helm upgrade --install ocr-app ./chart

>helm upgrade ocr-app ./chart

これが出来れば、以下で状況を確認

>kubectl get pods
>kubectl get svc

------------------------------------------
-- ▽変更後は、以下を行う
------------------------------------------
>helm upgrade --install ocr-app ./chart
>helm uninstall ocr-app

>kubectl get hpa ocr-service-hpa -w





kubectl get pods -l app=ocr-service

kubectl logs ocr-service-7f995bb46d-ns4rh -c python-api

kubectl describe hpa ocr-service-hpa

kubectl describe pod ocr-service-7f995bb46d-p7d7q

1. 特定のPodを「強制終了」して作り直させる
kubectl delete pod <ポッド名>

全てのPodを一斉に作り直させる（おすすめ）
kubectl rollout restart deployment ocr-service

2. Podの「数」を減らす（スケールダウン）
kubectl scale deployment ocr-service --replicas=1

今回のケースでの推奨手順
古いPodを掃除する
kubectl rollout restart deployment ocr-service

Podが1つ（または最小数）になるのを待つ
kubectl get pods


//////////////////////////////////////////////////////////////////////////////
// ●　k6
//////////////////////////////////////////////////////////////////////////////
--------------------------
0. 外部IPの確認
--------------------------
> kubectl get svc

----------
GKEの「ファイアウォール」でポート 8080 が閉じている（最有力）
GCPのデフォルト設定では、外部からの 8080 ポートへのアクセスはブロックされています。Terraform、またはコマンドでポートを開放する必要があります。
解決策（コマンドで開放する場合）:
以下のコマンドをターミナルで実行して、ポート8080への通信を許可してください。

gcloud compute firewall-rules create allow-go-api --allow tcp:8080 --target-tags=gke-inference-cluster-node
----------

--------------------------
2. 負荷テスト開始（別々のターミナルで実行）
--------------------------
2-1:ターミナル1（監視）: HPAの動きをじっと見守ります
OLD>kubectl get hpa python-api-hpa -w

>kubectl get hpa ocr-service-hpa -w


>k6 run --vus 1 --duration 10m script.js


2-2:ターミナル2（攻撃！）: k6を走らせます。0
>k6 run --vus 1 --duration 5m script.js

//////////////////////////////////////////////////////////////////////////////
// ●
//////////////////////////////////////////////////////////////////////////////

