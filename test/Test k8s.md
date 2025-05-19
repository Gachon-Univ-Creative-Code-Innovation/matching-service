## 전체 삭제
kubectl delete all --all
kubectl delete pvc --all
kubectl delete secret --all




## 배포
kubectl create secret generic fastapi-env-secret --from-file=.env
kubectl apply -f ./kubernetes/




## 디비 넣기
kubectl exec -it <postgreSQL pod> -- /bin/bash
psql -U user -d careerDB

CREATE TABLE "Career_Tag" (
  career_id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  tag_name TEXT NOT NULL
);

CREATE PUBLICATION debezium_pub_career FOR TABLE "Career_Tag";


## 연결
kubectl cp ./config/postgres-connector-career.json <connect pod>:/tmp/postgres-connector-career.json
kubectl exec -it <connect pod> -- /bin/bash
curl -X POST -H "Content-Type: application/json" --data @/tmp/postgres-connector-career.json http://connect:8083/connectors




## 포트 포워딩
kubectl port-forward svc/grafana 3000:3000
kubectl port-forward svc/qdrant 6333:6333
kubectl port-forward svc/fastapi-consumer-service 80:80