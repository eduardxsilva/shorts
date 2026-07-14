# Configurar publicação no YouTube

O upload OAuth desta versão foi feito para execução **local no Windows**.

1. No Google Cloud Console, crie um projeto.
2. Ative **YouTube Data API v3**.
3. Configure o Google Auth Platform como **External / Testing**.
4. Adicione como usuário de teste a conta Google que administra o canal.
5. Adicione o escopo `https://www.googleapis.com/auth/youtube.upload`.
6. Crie um cliente OAuth do tipo **Desktop app**.
7. Baixe o arquivo JSON. Não publique esse arquivo no GitHub.
8. Execute o aplicativo localmente e abra a aba **5. Publicar**.
9. Envie o JSON, selecione o corte, preencha os dados e escolha **private**.
10. Autorize a conta no navegador e revise o vídeo no YouTube Studio.

O token local fica em `workspace/<sessao>/secrets/token.json`. As pastas de
trabalho e segredos estão ignoradas pelo Git.
