from __future__ import annotations

import os
import sys
import traceback
import uuid
from pathlib import Path

# Garante que o pacote local seja encontrado no Streamlit Cloud,
# mesmo quando o processo é iniciado com outro diretório de trabalho.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

st.set_page_config(
    page_title="Shorts Coach Factory",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# As bibliotecas nativas usadas por Whisper/OpenCV não são confiáveis no
# Python 3.14 deste projeto. O app mostra o diagnóstico em vez de cair na tela
# genérica "Error running app".
if sys.version_info >= (3, 14):
    st.error("Ambiente incompatível: este projeto precisa do Python 3.12 ou 3.13.")
    st.code(f"Python em execução: {sys.version.split()[0]}")
    st.markdown(
        "Exclua o app no Streamlit Community Cloud e faça o deploy novamente. "
        "Em **Advanced settings → Python version**, selecione **3.12**. "
        "Apenas reiniciar o app não altera a versão do Python."
    )
    st.stop()

try:
    import pandas as pd
    from dotenv import load_dotenv

    from shorts_factory.config import AppConfig, ensure_directories, ffmpeg_available
    from shorts_factory.downloader import DownloadError, download_video, list_entries
    from shorts_factory.io_utils import read_json, save_uploaded_file, slugify, write_json
    from shorts_factory.media import MediaError, probe_media
    from shorts_factory.metadata import build_description, normalize_title
    from shorts_factory.renderer import QUALITY_PROFILES, RenderError, render_short
    from shorts_factory.scoring import select_candidates_heuristic, select_candidates_openai
    from shorts_factory.subtitles import STYLE_PRESETS
    from shorts_factory.transcription import TranscriptionError, transcribe_video
    from shorts_factory.youtube_upload import YouTubeUploadError, upload_video

    load_dotenv()
    ensure_directories()
    CONFIG = AppConfig()
except Exception as exc:
    st.error("Falha ao carregar uma dependência do projeto.")
    st.code(f"{type(exc).__name__}: {exc}")
    with st.expander("Detalhes técnicos"):
        st.code(traceback.format_exc())
    st.stop()


def initialize_state() -> None:
    defaults = {
        "session_id": uuid.uuid4().hex[:12],
        "video_path": None,
        "source_url": None,
        "video_entries": [],
        "transcript_path": None,
        "candidates_df": None,
        "rendered_files": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()
project_dir = CONFIG.workspace_dir / st.session_state.session_id
project_dir.mkdir(parents=True, exist_ok=True)


@st.cache_data(show_spinner=False)
def cached_list_entries(url: str, limit: int) -> list[dict]:
    return list_entries(url, limit)


def current_video() -> Path | None:
    value = st.session_state.get("video_path")
    return Path(value) if value else None


def current_transcript() -> dict | None:
    value = st.session_state.get("transcript_path")
    path = Path(value) if value else None
    if path and path.exists():
        return read_json(path)
    return None


def register_video(path: Path, source_url: str | None = None) -> None:
    st.session_state.video_path = str(path)
    st.session_state.source_url = source_url
    st.session_state.transcript_path = None
    st.session_state.candidates_df = None
    st.session_state.rendered_files = []


st.title("🎬 Shorts Coach Factory")
st.caption("Transforme vídeos próprios em Shorts verticais com transcrição, seleção de trechos e legendas dinâmicas.")

with st.sidebar:
    st.header("Projeto")
    st.code(st.session_state.session_id)
    st.write("**Fluxo:** fonte → transcrição → cortes → renderização → publicação")
    st.divider()
    if ffmpeg_available():
        st.success("FFmpeg detectado")
    else:
        st.error("FFmpeg não encontrado. Instale antes de processar vídeos.")
    st.info("Use apenas vídeos próprios ou conteúdos para os quais você tenha autorização.")
    if st.button("Novo projeto", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

source_tab, transcript_tab, cuts_tab, render_tab, publish_tab = st.tabs(
    ["1. Fonte", "2. Transcrever", "3. Selecionar cortes", "4. Renderizar", "5. Publicar"]
)

with source_tab:
    st.subheader("Escolha o vídeo de origem")
    upload_col, youtube_col = st.columns(2)

    with upload_col:
        st.markdown("#### Arquivo local")
        uploaded = st.file_uploader(
            "Envie MP4, MOV, MKV ou WEBM",
            type=["mp4", "mov", "mkv", "webm"],
            help="Para melhor qualidade, use o arquivo original da gravação.",
        )
        if uploaded and st.button("Usar arquivo enviado", type="primary", use_container_width=True):
            suffix = Path(uploaded.name).suffix.lower() or ".mp4"
            destination = project_dir / "source" / f"{slugify(Path(uploaded.name).stem)}{suffix}"
            uploaded.seek(0)
            save_uploaded_file(uploaded, destination)
            register_video(destination)
            st.success("Arquivo salvo no projeto.")

    with youtube_col:
        st.markdown("#### YouTube próprio — experimental")
        st.caption(
            "O YouTube pode bloquear downloads feitos por IPs de datacenter. "
            "Para produção, prefira o arquivo original ou o download feito no YouTube Studio."
        )
        youtube_url = st.text_input(
            "URL do vídeo, playlist ou canal",
            placeholder="https://www.youtube.com/watch?v=...",
        )
        limit = st.slider("Quantidade máxima para listar", 1, 50, 20)
        if st.button("Listar vídeos", use_container_width=True, disabled=not youtube_url):
            try:
                st.session_state.video_entries = cached_list_entries(youtube_url.strip(), limit)
                if not st.session_state.video_entries:
                    st.warning("Nenhum vídeo foi encontrado.")
            except Exception as exc:
                st.error(f"Falha ao listar: {exc}")

        entries = st.session_state.get("video_entries", [])
        if entries:
            labels = [f"{item['title']} — {item.get('duration') or '?'} s" for item in entries]
            selected_index = st.selectbox("Selecione um vídeo", range(len(labels)), format_func=lambda i: labels[i])
            selected_entry = entries[selected_index]
            if st.button("Baixar vídeo selecionado", type="primary", use_container_width=True):
                try:
                    with st.spinner("Baixando e preparando o vídeo..."):
                        path = download_video(
                            selected_entry["url"],
                            project_dir / "source",
                            selected_entry.get("title"),
                        )
                    register_video(path, selected_entry["url"])
                    st.success("Vídeo adicionado ao projeto.")
                except DownloadError as exc:
                    st.error(f"Falha no download: {exc}")
                    if exc.blocked_by_youtube:
                        st.info(
                            "No Streamlit Cloud, o método mais confiável é baixar o seu próprio "
                            "vídeo pelo YouTube Studio no computador e enviá-lo no campo "
                            "‘Arquivo local’. Não é necessário alterar as outras etapas do app."
                        )

    video_path = current_video()
    if video_path and video_path.exists():
        st.divider()
        st.markdown("#### Vídeo atual")
        try:
            info = probe_media(video_path)
            c1, c2, c3 = st.columns(3)
            c1.metric("Duração", f"{info['duration'] / 60:.1f} min")
            c2.metric("Resolução", f"{info['width']}×{info['height']}")
            c3.metric("Arquivo", video_path.name)
            short_side = min(int(info["width"]), int(info["height"]))
            long_side = max(int(info["width"]), int(info["height"]))
            if short_side < 720 or long_side < 1280:
                st.warning(
                    "A origem está abaixo de 720p. O aplicativo exportará em 1080×1920, "
                    "mas não consegue recuperar detalhes inexistentes no arquivo original."
                )
        except MediaError as exc:
            st.warning(str(exc))
        st.video(str(video_path))

with transcript_tab:
    st.subheader("Transcrição com timestamps por palavra")
    video_path = current_video()
    if not video_path or not video_path.exists():
        st.warning("Selecione um vídeo na primeira aba.")
    else:
        settings_col, action_col = st.columns([2, 1])
        with settings_col:
            model_size = st.selectbox(
                "Modelo Whisper",
                ["tiny", "base", "small", "medium", "large-v3"],
                index=2,
                help="small oferece bom equilíbrio. medium e large-v3 exigem mais memória.",
            )
            language = st.selectbox("Idioma", ["pt", "auto", "en", "es"], index=0)
            device = st.selectbox("Processamento", ["auto", "cpu", "cuda"], index=0)
        with action_col:
            st.write("")
            st.write("")
            transcribe_clicked = st.button("Transcrever vídeo", type="primary", use_container_width=True)

        if transcribe_clicked:
            transcript_path = project_dir / "transcript" / "transcript.json"
            try:
                with st.spinner("Transcrevendo. O primeiro uso também baixa o modelo..."):
                    result = transcribe_video(
                        video_path,
                        transcript_path,
                        model_size=model_size,
                        language=None if language == "auto" else language,
                        device_choice=device,
                    )
                st.session_state.transcript_path = str(transcript_path)
                st.session_state.candidates_df = None
                st.success(f"Transcrição concluída: {len(result['words'])} palavras.")
            except TranscriptionError as exc:
                st.error(f"Falha na transcrição: {exc}")

        transcript = current_transcript()
        if transcript:
            st.success(
                f"Idioma detectado: {transcript.get('language', '?')} · "
                f"{len(transcript.get('segments', []))} segmentos · "
                f"{len(transcript.get('words', []))} palavras"
            )
            with st.expander("Ver transcrição"):
                st.text_area("Texto", transcript.get("text", ""), height=320, disabled=True)
            transcript_bytes = Path(st.session_state.transcript_path).read_bytes()
            st.download_button(
                "Baixar transcrição JSON",
                transcript_bytes,
                file_name="transcript.json",
                mime="application/json",
            )

with cuts_tab:
    st.subheader("Encontre e revise os melhores trechos")
    transcript = current_transcript()
    if not transcript:
        st.warning("Transcreva o vídeo antes de selecionar cortes.")
    else:
        c1, c2, c3 = st.columns(3)
        min_seconds = c1.slider("Duração mínima", 10, 60, 20)
        max_seconds = c2.slider("Duração máxima", min_seconds + 5, 120, 55)
        top_n = c3.slider("Quantidade de candidatos", 3, 15, 8)

        method = st.radio(
            "Método de seleção",
            ["Heurística local (gratuita)", "OpenAI (melhor análise semântica)"],
            horizontal=True,
        )
        api_key = None
        model_name = CONFIG.openai_model
        if method.startswith("OpenAI"):
            api_key = st.text_input(
                "OPENAI_API_KEY",
                value=os.getenv("OPENAI_API_KEY", ""),
                type="password",
                help="A chave não é salva pelo projeto.",
            )
            model_name = st.text_input("Modelo", value=CONFIG.openai_model)

        if st.button("Gerar candidatos", type="primary"):
            try:
                with st.spinner("Analisando a transcrição..."):
                    if method.startswith("OpenAI"):
                        candidates = select_candidates_openai(
                            transcript,
                            min_seconds,
                            max_seconds,
                            top_n,
                            api_key=api_key,
                            model=model_name,
                        )
                    else:
                        candidates = select_candidates_heuristic(
                            transcript,
                            min_seconds,
                            max_seconds,
                            top_n,
                        )
                if not candidates:
                    st.warning("Não foram encontrados trechos. Reduza a duração mínima ou revise a transcrição.")
                else:
                    st.session_state.candidates_df = pd.DataFrame(candidates)
                    write_json(project_dir / "candidates" / "candidates.json", candidates)
                    st.success(f"{len(candidates)} candidatos gerados.")
            except Exception as exc:
                st.error(f"Falha na seleção: {exc}")

        if isinstance(st.session_state.candidates_df, pd.DataFrame) and not st.session_state.candidates_df.empty:
            editable_columns = [
                "selected", "id", "start", "end", "duration", "score", "title", "hook", "risk", "text"
            ]
            source_df = st.session_state.candidates_df.copy()
            for column in editable_columns:
                if column not in source_df.columns:
                    source_df[column] = ""
            edited = st.data_editor(
                source_df[editable_columns],
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                column_config={
                    "selected": st.column_config.CheckboxColumn("Renderizar"),
                    "start": st.column_config.NumberColumn("Início (s)", min_value=0.0, format="%.3f"),
                    "end": st.column_config.NumberColumn("Fim (s)", min_value=0.1, format="%.3f"),
                    "duration": st.column_config.NumberColumn("Duração", disabled=True, format="%.1f s"),
                    "score": st.column_config.ProgressColumn("Nota", min_value=0, max_value=100),
                    "text": st.column_config.TextColumn("Transcrição", width="large"),
                },
                disabled=["id", "duration", "score", "text"],
                key="candidate_editor",
            )
            edited["duration"] = edited["end"].astype(float) - edited["start"].astype(float)
            st.session_state.candidates_df = edited
            csv_data = edited.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Baixar candidatos CSV", csv_data, "candidatos.csv", "text/csv")

with render_tab:
    st.subheader("Renderize em 1080×1920 com legendas")
    video_path = current_video()
    transcript = current_transcript()
    candidates_df = st.session_state.get("candidates_df")
    if not video_path or not transcript or not isinstance(candidates_df, pd.DataFrame) or candidates_df.empty:
        st.warning("Selecione um vídeo, transcreva e gere candidatos primeiro.")
    else:
        selected_df = candidates_df[candidates_df["selected"].fillna(False).astype(bool)].copy()
        st.write(f"Cortes marcados: **{len(selected_df)}**")
        s1, s2, s3 = st.columns(3)
        subtitle_preset = s1.selectbox("Estilo da legenda", list(STYLE_PRESETS.keys()))
        layout = s2.selectbox("Enquadramento", ["Corte com rosto", "Fundo desfocado"])
        quality_profile = s3.selectbox("Qualidade", list(QUALITY_PROFILES.keys()))

        a1, a2, a3 = st.columns(3)
        face_tracking_enabled = a1.checkbox(
            "Centralizar pelo rosto",
            value=True,
            disabled=layout != "Corte com rosto",
        )
        subtitle_size_percent = a2.slider(
            "Tamanho da legenda (%)",
            min_value=80,
            max_value=110,
            value=100,
            step=5,
        )
        subtitle_vertical_margin = a3.slider(
            "Distância da legenda da borda inferior",
            min_value=240,
            max_value=460,
            value=310,
            step=10,
            help="Aumente para subir a legenda. O valor padrão evita os controles do Shorts.",
        )
        st.caption(
            "As legendas são limitadas a duas linhas, têm tamanho automático e margem lateral segura. "
            "Use ‘Máxima’ apenas quando puder esperar mais pela renderização."
        )

        if st.button("Renderizar cortes marcados", type="primary", disabled=selected_df.empty):
            rendered_files: list[str] = []
            progress = st.progress(0.0)
            status = st.empty()
            for position, (_, row) in enumerate(selected_df.iterrows(), start=1):
                title = normalize_title(str(row.get("title", f"corte-{position}")))
                filename = f"{position:02d}-{slugify(title)}.mp4"
                output_path = CONFIG.output_dir / st.session_state.session_id / filename
                status.write(f"Renderizando {position}/{len(selected_df)}: {title}")
                try:
                    render_short(
                        video_path,
                        transcript,
                        float(row["start"]),
                        float(row["end"]),
                        output_path,
                        subtitle_preset=subtitle_preset,
                        layout=layout,
                        face_tracking=face_tracking_enabled,
                        quality_profile=quality_profile,
                        subtitle_size_percent=subtitle_size_percent,
                        subtitle_vertical_margin=subtitle_vertical_margin,
                    )
                    rendered_files.append(str(output_path))
                except RenderError as exc:
                    st.error(f"Falha em {title}: {exc}")
                progress.progress(position / max(len(selected_df), 1))
            st.session_state.rendered_files = rendered_files
            status.empty()
            if rendered_files:
                st.success(f"{len(rendered_files)} cortes concluídos.")

        rendered_paths = [Path(path) for path in st.session_state.get("rendered_files", []) if Path(path).exists()]
        for index, path in enumerate(rendered_paths, start=1):
            st.markdown(f"#### Corte {index}: {path.stem}")
            st.video(str(path))
            st.download_button(
                "Baixar MP4",
                path.read_bytes(),
                file_name=path.name,
                mime="video/mp4",
                key=f"download-{path}",
            )

with publish_tab:
    st.subheader("Envio opcional ao YouTube")
    st.warning(
        "O login OAuth pelo navegador funciona melhor na execução local. "
        "Por segurança, o padrão é enviar como privado para revisão no YouTube Studio."
    )
    rendered_paths = [Path(path) for path in st.session_state.get("rendered_files", []) if Path(path).exists()]
    if not rendered_paths:
        st.info("Renderize pelo menos um corte.")
    else:
        selected_path = st.selectbox(
            "Vídeo",
            rendered_paths,
            format_func=lambda path: path.name,
        )
        client_secret = st.file_uploader(
            "client_secret.json do Google Cloud",
            type=["json"],
            key="client-secret-uploader",
        )
        default_title = normalize_title(selected_path.stem.replace("-", " ").title())
        title = st.text_input("Título", value=default_title)
        description = st.text_area(
            "Descrição",
            value=build_description(title, st.session_state.get("source_url")),
            height=180,
        )
        tags_text = st.text_input("Tags separadas por vírgula", value="shorts, disciplina, desenvolvimento pessoal")
        privacy = st.selectbox("Privacidade", ["private", "unlisted", "public"], index=0)

        if st.button("Enviar ao YouTube", type="primary", disabled=client_secret is None):
            secrets_path = project_dir / "secrets" / "client_secret.json"
            token_path = project_dir / "secrets" / "token.json"
            client_secret.seek(0)
            save_uploaded_file(client_secret, secrets_path)
            try:
                with st.spinner("Autorizando e enviando..."):
                    response = upload_video(
                        selected_path,
                        secrets_path,
                        token_path,
                        title=title,
                        description=description,
                        tags=[tag.strip() for tag in tags_text.split(",") if tag.strip()],
                        privacy_status=privacy,
                    )
                st.success(f"Upload concluído. ID do vídeo: {response.get('id', 'desconhecido')}")
            except YouTubeUploadError as exc:
                st.error(f"Falha no upload: {exc}")

st.divider()
st.caption("Não há garantia de viralização ou monetização. Revise conteúdo, legendas, direitos autorais e promessas comerciais antes de publicar.")
