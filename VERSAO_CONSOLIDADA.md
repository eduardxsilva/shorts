# Versão consolidada 1.1.0

Esta edição preserva a estrutura estável anterior do aplicativo e reúne as correções posteriores.

## Incluído

- inicialização local pelo `INICIAR_APP_WINDOWS.bat`;
- compatibilidade prevista com Python 3.12 e 3.13;
- tratamento do bloqueio 403 em downloads por URL;
- transcrição carregada somente quando necessária;
- upload opcional para o YouTube na execução local;
- arquivos com finais de linha protegidos por `.gitattributes`;
- legendas em no máximo duas linhas;
- redução automática de fonte para frases largas;
- posição e tamanho ajustáveis na tela de renderização;
- escala Lanczos e saída H.264 1080×1920;
- perfis de qualidade rápida, alta e máxima;
- aviso para fontes abaixo de 720p.
- reconstrução da pasta `shorts_factory`, ausente no pacote recebido;
- timeout entre 3 e 15 minutos por corte, impedindo FFmpeg órfão;
- exclusão automática de saída parcial após falha;
- download com poucas tentativas e timeout de rede;
- arquivo ASS temporário removido após a renderização.

## Validação executada

- compilação de todos os arquivos Python;
- testes automatizados do núcleo;
- compilação integral dos módulos;
- teste real de renderização quando FFmpeg estiver disponível.
