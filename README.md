# Shorts Coach Factory

## Início rápido no Windows

1. Extraia o ZIP inteiro.
2. Instale o FFmpeg com `winget install Gyan.FFmpeg`.
3. Execute `INICIAR_APP_WINDOWS.bat`.

Se um vídeo grande aparentar travamento, teste primeiro o perfil **Rápida** e um
único corte. Cada corte possui limite automático de execução; uma falha não
deixa o FFmpeg rodando indefinidamente.

O inicializador usa diretamente o Python do ambiente virtual e não depende de
`Activate.ps1`, portanto funciona mesmo quando scripts do PowerShell estão bloqueados.

Esta versão inclui legendas em até duas linhas, área segura para Shorts, escala
Lanczos, vídeo H.264 CRF 18 e áudio AAC a 192 kbps.

Aplicativo Streamlit para transformar vídeos próprios do YouTube ou arquivos locais em cortes verticais com:

- transcrição local por palavra com `faster-whisper`;
- seleção automática de trechos por heurística ou OpenAI;
- edição manual dos tempos, títulos e ganchos;
- vídeo vertical 1080×1920;
- centralização aproximada pelo rosto;
- opção de fundo desfocado;
- legendas dinâmicas com palavra destacada;
- normalização de áudio;
- download em MP4;
- upload opcional ao YouTube como privado, não listado ou público.

> Use somente vídeos próprios ou conteúdos para os quais você possua autorização. O sistema não garante viralização, alcance ou monetização.

## 1. Estrutura

```text
shorts-coach-factory/
├── app.py
├── shorts_factory/
│   ├── config.py
│   ├── downloader.py
│   ├── face_tracking.py
│   ├── io_utils.py
│   ├── media.py
│   ├── metadata.py
│   ├── renderer.py
│   ├── scoring.py
│   ├── subtitles.py
│   ├── transcription.py
│   └── youtube_upload.py
├── .streamlit/config.toml
├── .github/workflows/python.yml
├── Dockerfile
├── docker-compose.yml
├── packages.txt
├── requirements.txt
├── tests/
├── workspace/
└── outputs/
```

## 2. Requisitos

- Python 3.12 recomendado;
- FFmpeg e FFprobe disponíveis no `PATH`;
- 8 GB de RAM para modelos `tiny`, `base` ou `small`;
- GPU NVIDIA opcional para `medium` ou `large-v3`;
- conexão com a internet para baixar o modelo na primeira execução e para importar vídeos por URL.

### Instalar FFmpeg no Windows

Uma opção prática:

```powershell
winget install Gyan.FFmpeg
```

Feche e reabra o terminal. Confirme:

```powershell
ffmpeg -version
ffprobe -version
```

### Instalar FFmpeg no Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg fonts-dejavu-core
```

### Instalar FFmpeg no macOS

```bash
brew install ffmpeg
```

## 3. Executar localmente

### Windows

```powershell
git clone URL_DO_SEU_REPOSITORIO
cd shorts-coach-factory
.\INICIAR_APP_WINDOWS.bat
```

Também é possível executar:

```powershell
scripts\run_windows.bat
```

### Linux/macOS

```bash
git clone URL_DO_SEU_REPOSITORIO
cd shorts-coach-factory
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

O navegador deve abrir em `http://localhost:8501`.

## 4. Usar o aplicativo

1. Na aba **Fonte**, envie o arquivo original ou informe uma URL do seu próprio vídeo, playlist ou canal.
2. Na aba **Transcrever**, escolha `small`, idioma `pt` e processamento `auto`.
3. Na aba **Selecionar cortes**, gere candidatos pela heurística local.
4. Marque os trechos que serão renderizados e ajuste início/fim quando necessário.
5. Na aba **Renderizar**, escolha o estilo da legenda e o enquadramento.
6. Revise os MP4s e faça o download.
7. Opcionalmente, configure OAuth e envie ao YouTube como **private** para revisão.

## 5. Seleção por OpenAI — opcional

A heurística local não tem custo, mas entende menos o significado do conteúdo. Para usar análise semântica:

1. Copie `.env.example` para `.env`.
2. Preencha:

```env
OPENAI_API_KEY=sua_chave
OPENAI_MODEL=gpt-5-mini
```

O aplicativo também aceita a chave diretamente na interface. Ela não é gravada pelo código.

Não envie `.env` para o GitHub.

## 6. Upload ao YouTube — opcional

O upload usa OAuth 2.0 e funciona melhor na execução local.

1. Entre no Google Cloud Console.
2. Crie ou selecione um projeto.
3. Ative a **YouTube Data API v3**.
4. Configure a tela de consentimento OAuth.
5. Crie uma credencial OAuth do tipo **Desktop app**.
6. Baixe o arquivo JSON.
7. Na aba **Publicar**, envie esse JSON.
8. O navegador abrirá a autorização da sua conta.

O projeto grava o token somente dentro de `workspace/.../secrets/`, pasta ignorada pelo Git.

O envio padrão é privado. Revise título, legendas, direitos autorais, promessas comerciais e enquadramento no YouTube Studio antes de tornar público.

## 7. Executar com Docker

```bash
cp .env.example .env
docker compose up --build
```

Acesse `http://localhost:8501`.

## 8. Colocar no GitHub

Crie um repositório vazio no GitHub e execute:

```bash
git init
git add .
git commit -m "Initial Shorts Coach Factory"
git branch -M main
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

Para o seu repositório `eduardxsilva/shorts`, use:

```powershell
cd "$HOME\Downloads\shorts-corrigido"
git init
git add .
git commit -m "Corrige legendas e renderização"
git branch -M main
git remote remove origin 2>$null
git remote add origin https://github.com/eduardxsilva/shorts.git
git push -u origin main
```

Se ocorrer erro 403 no `git push`, o problema é autenticação/permissão do
GitHub, não o tamanho do vídeo. Arquivos MP4 estão ignorados pelo Git. Confirme
no Git Credential Manager que a conta conectada tem acesso de escrita ao
repositório.

O workflow em `.github/workflows/python.yml` verifica sintaxe e testes em cada push.

## 9. Publicar no Streamlit Community Cloud

1. Suba o projeto para o GitHub.
2. No Streamlit Community Cloud, crie um novo app.
3. Escolha o repositório e informe `app.py` como arquivo principal.
4. Adicione `OPENAI_API_KEY` em **Secrets** somente se usar a seleção por IA.

O arquivo `packages.txt` solicita FFmpeg e as fontes no ambiente Linux.


## 9.1 Corrigir `No module named shorts_factory`

Esse erro indica que o Streamlit não encontrou o pacote local do projeto. No GitHub, confirme que estes itens estão no mesmo nível:

```text
app.py
requirements.txt
pyproject.toml
shorts_factory/
    __init__.py
    config.py
    ...
```

Não envie somente o `app.py`. Envie a pasta `shorts_factory` inteira. Depois atualize o repositório:

```bash
git add app.py requirements.txt pyproject.toml shorts_factory
git commit -m "Fix Streamlit package imports"
git push
```

No Streamlit Community Cloud, abra **Manage app → Reboot app**. Se o ambiente estiver inconsistente, exclua o app e implante novamente escolhendo **Python 3.12** em **Advanced settings**.

O `app.py` também adiciona explicitamente a raiz do projeto ao `sys.path`.

### Limitações da nuvem

Processamento de vídeo e Whisper consomem muita memória, CPU e armazenamento temporário. Na nuvem:

- prefira vídeos curtos;
- use `tiny`, `base` ou `small`;
- renderize poucos cortes por vez;
- use upload de arquivo como alternativa quando o YouTube bloquear downloads automatizados;
- não espere a mesma estabilidade de uma máquina local ou servidor dedicado.

Para produção contínua, use Docker em VPS, Railway, Render, Fly.io, Google Cloud Run com disco externo ou uma máquina própria. Confirme limites e preços atuais antes de escolher uma plataforma.

## 10. Configuração de legendas

Os estilos ficam em `shorts_factory/subtitles.py`:

- `Impacto amarelo`;
- `Minimalista branco`;
- `Energia verde`.

Cada bloco contém poucas palavras. A palavra falada recebe destaque e um leve aumento de escala.

## 11. Estratégia de operação

Não publique todos os resultados automaticamente. Use este processo:

```text
vídeo longo
→ 6 a 10 candidatos
→ revisão humana
→ 2 ou 3 cortes diferentes
→ upload privado
→ revisão no YouTube Studio
→ agendamento
→ análise de retenção e inscritos
```

Evite produzir dezenas de Shorts praticamente iguais. Isso prejudica a experiência do público e pode criar aparência de conteúdo repetitivo ou produzido em massa.

## 12. Problemas comuns

### `FFmpeg não encontrado`

Instale o FFmpeg, reinicie o terminal e confirme `ffmpeg -version`.

### O modelo demora na primeira execução

O faster-whisper baixa o modelo escolhido. Depois ele fica no cache local.

### Falta de memória

Use `tiny`, `base` ou `small`, feche outros programas e processe vídeos menores.

### Download do YouTube falhou

O YouTube pode exigir autenticação, bloquear o IP ou alterar a página. Use o arquivo original do vídeo ou baixe seu próprio conteúdo pelo YouTube Studio/Google Takeout e envie ao app.

### Legenda não aparece

Confirme se sua instalação do FFmpeg inclui o filtro `subtitles`/libass:

```bash
ffmpeg -filters | findstr subtitles
```

No Linux/macOS:

```bash
ffmpeg -filters | grep subtitles
```

### OAuth não abre na nuvem

O fluxo de aplicativo instalado abre um navegador local. Execute o app no computador para autenticar e publicar, ou faça o upload manual no YouTube Studio.

## 13. Segurança

Nunca envie ao GitHub:

- `.env`;
- chaves de API;
- `client_secret.json`;
- `token.json`;
- vídeos brutos;
- dados pessoais de clientes.

Esses itens já estão cobertos pelo `.gitignore`, mas revise sempre antes do commit:

```bash
git status
```

## 14. Referências técnicas

- Streamlit: https://docs.streamlit.io/
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- FFmpeg: https://ffmpeg.org/ffmpeg-filters.html
- YouTube Data API: https://developers.google.com/youtube/v3/
- OpenAI API: https://developers.openai.com/api/docs/

## Limitação do download por URL no Streamlit Cloud

O YouTube pode responder com `HTTP Error 403: Forbidden` quando o download é
feito a partir de IPs compartilhados de datacenter. Isso não significa que o
vídeo esteja inválido e não é um erro do FFmpeg.

Para uso confiável em produção:

1. use o arquivo original da gravação; ou
2. baixe o seu próprio vídeo pelo YouTube Studio no computador;
3. envie o MP4 pela opção **Arquivo local** do aplicativo.

O modo por URL possui tentativas alternativas de formato, mas permanece
experimental porque os requisitos de reprodução do YouTube mudam e podem
exigir PO Tokens vinculados à sessão/IP.

## Melhorias desta versão consolidada

- Base estável anterior preservada.
- Legendas limitadas a duas linhas com quebra manual e tamanho adaptativo.
- Margens laterais e inferiores seguras para a interface do YouTube Shorts.
- Controle de tamanho e posição das legendas no aplicativo.
- Escala Lanczos e perfis de qualidade H.264: rápida, alta e máxima.
- Sem conversão forçada para 30 fps; o ritmo do vídeo de origem é preservado.
- Aviso quando o vídeo original possui resolução inferior a 720p.
- Download por URL continua experimental; upload do arquivo original é o método recomendado.
