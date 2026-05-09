//////////////////////////////////////////////////////////////////////////////
// ●手順：コンテナのビルドと起動
//////////////////////////////////////////////////////////////////////////////

----------------
helm upgrade python-api-release .


----------------
> kubectl get deployments
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
python-api   1/1     1            1           8m29s


----------------
kubectl rollout restart deployment/python-api



----------------
kubectl get pods

----------------
helm uninstall python-api-release



//////////////////////////////////////////////////////////////////////////////
// ●手仕舞い
//////////////////////////////////////////////////////////////////////////////

# 現在インストールされているリリースを確認
helm list

# リリースを削除（例: python-api-release や multi-api-release）
helm uninstall [あなたのリリース名]

kubectl get all



kubectl delete pod python-api-5b748bf856-g8fsr


kubectl delete pod [Pod名] --force --grace-period=0


kubectl get pods --all-namespaces

# 使っていないイメージを全削除して掃除する
docker image prune -a

# もし「全部」消して強制的にリセットするなら（※全ビルドし直しになります）
docker rmi $(docker images -q)
