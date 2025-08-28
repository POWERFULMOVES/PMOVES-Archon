.PHONY: up down clean
up:
	docker compose --profile data up -d qdrant neo4j minio meilisearch
	docker compose --profile workers up -d hi-rag-gateway retrieval-eval

down:
	docker compose down

clean:
	docker compose down -v
