# /add-intent — Adicionar Novo Intent ao IGS

Adicione o intent `$ARGUMENTS` ao sistema IGS seguindo o padrão existente.

Passos obrigatórios (NÃO pule nenhum):
1. Adicionar ao enum/lista de intents em `intent_classifier.py`
2. Criar o prompt de classificação para o novo intent
3. Criar o data fetcher no serviço apropriado (student, employee, etc.)
4. Registrar o handler em `message_tasks.py`
5. Se for intent de ação, adicionar ao `task_executor.py`
6. Criar testes em `backend/tests/`
7. Atualizar o CLAUDE.md com o novo intent na lista dos 28

Antes de começar, leia o código existente de um intent similar para manter o padrão.
