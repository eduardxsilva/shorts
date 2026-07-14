# Contribuindo

1. Crie uma branch a partir de `main`.
2. Faça mudanças pequenas e testáveis.
3. Execute:

```bash
python -m compileall app.py shorts_factory tests
pytest -q
```

4. Não inclua vídeos, tokens, chaves ou credenciais no commit.
5. Abra um pull request descrevendo o problema, a solução e como testar.
