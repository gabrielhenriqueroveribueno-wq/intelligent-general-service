# /review-intent — Revisar um Intent do IGS

Revise a implementação completa do intent `$ARGUMENTS` no sistema IGS.

Verifique:
1. O classificador em `backend/app/services/intent_classifier.py`
2. O handler no `backend/app/tasks/message_tasks.py`
3. O data fetcher correspondente no serviço específico
4. O task_executor para intents de ação
5. Se o intent aparece nos 28 listados no CLAUDE.md
6. Se o RAG está funcionando (dados reais, não inventados)
7. Cobertura de testes em `backend/tests/`

Ao final, liste: o que está ok, o que falta, e o próximo passo recomendado.
