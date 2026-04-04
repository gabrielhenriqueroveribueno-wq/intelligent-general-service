# /debug-celery — Debugar Problema no Worker Celery

Investigue e resolva o problema: `$ARGUMENTS`

Checklist de debugging para o pipeline Celery do IGS:
1. Verificar logs do worker: `make logs` → filtrar pelo container `celery`
2. Verificar se a tarefa está na fila Redis: `redis-cli LLEN celery`
3. Verificar se o worker está rodando: `docker compose ps celery`
4. Verificar o traceback completo da tarefa falha
5. Verificar se o problema está no step de classificação ou de geração de resposta
6. Verificar se há timeout nas chamadas à IA (Groq/Anthropic)
7. Verificar se o tenant_id está sendo propagado corretamente
8. Verificar as métricas em Prometheus: http://localhost:9090

Use a skill `systematic-debugging` do Superpowers se o problema não for óbvio.
Documente a causa raiz encontrada antes de propor a solução.
