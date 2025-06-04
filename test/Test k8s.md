## 전체 삭제
kubectl delete all --all
kubectl delete pvc --all
kubectl delete secret --all




## 배포
kubectl create namespace matching-service

kubectl create secret generic fastapi-env-secret --from-file=.env -n matching-service

kubectl apply -f ./kubernets/


## 연결
kubectl cp ./config/postgres-connector-career.json connect-6966b79df8-bmsmv:/tmp/postgres-connector-career.json -n matching-service
kubectl exec -it <connect pod> -n matching-service -- /bin/bash
curl -X POST -H "Content-Type: application/json" --data @/tmp/postgres-connector-career.json http://connect:8083/connectors

