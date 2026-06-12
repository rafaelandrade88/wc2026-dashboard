import os

import streamlit as st
import requests

from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

st.set_page_config(
    page_title="Copa do Mundo 2026",
    page_icon="🏆",
    layout="wide"
)

headers = {
    "X-Auth-Token": API_KEY
}

@st.cache_data(ttl=3600)
def carregar_jogos():

    url = "https://api.football-data.org/v4/competitions/WC/matches"

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data["matches"]

jogos = carregar_jogos()

st.title("🏆 Copa do Mundo 2026")

# =====================
# MÉTRICAS
# =====================

total = len(jogos)

finalizados = len(
    [j for j in jogos if j["status"] == "FINISHED"]
)

ao_vivo = len(
    [j for j in jogos if j["status"] == "LIVE"]
)

proximos = total - finalizados - ao_vivo

m1, m2, m3, m4 = st.columns(4)

m1.metric("Partidas", total)
m2.metric("Finalizadas", finalizados)
m3.metric("Ao Vivo", ao_vivo)
m4.metric("Próximas", proximos)

st.divider()

# =====================
# FILTROS
# =====================

c1, c2, c3 = st.columns(3)

with c1:
    busca = st.text_input(
        "🔍 Buscar seleção"
    )

with c2:

    fases = sorted(
        list(
            set(
                jogo["stage"]
                for jogo in jogos
            )
        )
    )

    fase = st.selectbox(
        "🏆 Fase",
        ["TODAS"] + fases
    )

with c3:

    grupos = sorted(
        list(
            set(
                jogo.get("group", "")
                for jogo in jogos
                if jogo.get("group")
            )
        )
    )

    grupo = st.selectbox(
        "👥 Grupo",
        ["TODOS"] + grupos
    )

# =====================
# PREPARAÇÃO DOS DADOS
# =====================

dados = []

for jogo in jogos:

    casa = jogo["homeTeam"].get("name") or "A definir"
    fora = jogo["awayTeam"].get("name") or "A definir"

    if busca:

        texto = f"{casa} {fora}".lower()

        if busca.lower() not in texto:
            continue

    if fase != "TODAS":

        if jogo["stage"] != fase:
            continue

    if grupo != "TODOS":

        if jogo.get("group", "") != grupo:
            continue

    utc = datetime.fromisoformat(
        jogo["utcDate"].replace("Z", "+00:00")
    )

    brasil = utc.astimezone(
        ZoneInfo("America/Sao_Paulo")
    )

    placar_casa = jogo["score"]["fullTime"]["home"]
    placar_fora = jogo["score"]["fullTime"]["away"]

    if placar_casa is None:

        placar = "VS"

    else:

        placar = f"{placar_casa} x {placar_fora}"

    dados.append(
        {
            "Casa": casa,
            "Fora": fora,
            "EscudoCasa": jogo["homeTeam"]["crest"],
            "EscudoFora": jogo["awayTeam"]["crest"],
            "Data": brasil.strftime("%d/%m/%Y"),
            "Hora": brasil.strftime("%H:%M"),
            "Grupo": jogo.get("group", ""),
            "Fase": jogo["stage"],
            "Status": jogo["status"],
            "Placar": placar,
            "SortDate": brasil
        }
    )

dados = sorted(
    dados,
    key=lambda x: x["SortDate"]
)

# =====================
# RENDER
# =====================

def render_cards(lista):

    st.write(f"### {len(lista)} partidas")

    for jogo in lista:

        with st.container(border=True):

            if jogo["Status"] == "LIVE":
                st.error("🔴 AO VIVO")

            elif jogo["Status"] == "FINISHED":
                st.success("✅ ENCERRADO")

            else:
                st.info("📅 AGENDADO")

            c1, c2, c3 = st.columns([3, 2, 3])

            with c1:

                if jogo["EscudoCasa"]:
                    st.image(
                        jogo["EscudoCasa"],
                        width=70
                    )

                st.subheader(
                    jogo["Casa"]
                )

            with c2:

                st.markdown(
                    f"## {jogo['Placar']}"
                )

            with c3:

                if jogo["EscudoFora"]:
                    st.image(
                        jogo["EscudoFora"],
                        width=70
                    )

                st.subheader(
                    jogo["Fora"]
                )

            st.caption(
                f"📅 {jogo['Data']} | 🕒 {jogo['Hora']}"
            )

            st.caption(
                f"🏆 {jogo['Fase']}"
            )

            if jogo["Grupo"]:

                st.caption(
                    f"👥 {jogo['Grupo']}"
                )

# =====================
# ABAS
# =====================

aba1, aba2, aba3, aba4, aba5 = st.tabs(
    [
        "🏆 Todos",
        "🔴 Ao Vivo",
        "✅ Encerrados",
        "📅 Próximos",
        "👕 Seleções"
    ]
)

with aba1:
    render_cards(dados)

with aba2:

    render_cards(
        [
            j for j in dados
            if j["Status"] == "LIVE"
        ]
    )

with aba3:

    render_cards(
        [
            j for j in dados
            if j["Status"] == "FINISHED"
        ]
    )

with aba4:

    render_cards(
        [
            j for j in dados
            if j["Status"] not in [
                "FINISHED",
                "LIVE"
            ]
        ]
    )

# =====================
# SELEÇÕES
# =====================

with aba5:

    st.header("👕 Uniformes das Seleções")

    selecoes = {}

    for jogo in jogos:

        casa = jogo["homeTeam"].get("name")
        fora = jogo["awayTeam"].get("name")

        if casa:
            selecoes[casa] = jogo["homeTeam"].get("crest")

        if fora:
            selecoes[fora] = jogo["awayTeam"].get("crest")

    lista_selecoes = sorted(
        [nome for nome in selecoes.keys() if nome]
    )

    # ── Estado inicial ───────────────────────────────────────
    if "selecao_ativa" not in st.session_state:
        st.session_state.selecao_ativa = lista_selecoes[0]

    selecao_ativa = st.session_state.selecao_ativa

    # ── Radio OCULTO — é o que o Streamlit lê de verdade ─────
    idx_atual = lista_selecoes.index(selecao_ativa)

    escolha = st.radio(
        label="seleção",
        options=lista_selecoes,
        index=idx_atual,
        key="radio_selecao_oculto",
        label_visibility="collapsed"
    )

    # CSS injetado APÓS o radio — esconde visualmente sem remover do DOM
    # display:none quebraria o monitoramento do Streamlit
    st.markdown("""
    <style>
        div[data-testid="stRadio"] {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            overflow: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    if escolha != selecao_ativa:
        st.session_state.selecao_ativa = escolha
        st.rerun()

    # ── Grade visual via components.v1.html ──────────────────
    # Tem acesso real ao DOM pai via window.parent
    import json as _json
    import streamlit.components.v1 as components

    dados_grade = [
        {
            "nome": nome,
            "escudo": selecoes.get(nome, "") or "",
            "ativo": nome == selecao_ativa
        }
        for nome in lista_selecoes
    ]

    altura_grade = 60 * (1 + len(lista_selecoes) // 8)

    grade_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: transparent; font-family: sans-serif; }}
        .grade {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 4px 2px;
        }}
        .card {{
            display: flex;
            align-items: center;
            gap: 7px;
            padding: 5px 11px 5px 7px;
            border: 1.5px solid #444;
            border-radius: 8px;
            cursor: pointer;
            background: #1e1e1e;
            color: #ccc;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.15s ease;
            white-space: nowrap;
            user-select: none;
        }}
        .card:hover {{
            border-color: #e74c3c;
            color: #fff;
            background: #2a2a2a;
        }}
        .card.ativo {{
            border-color: #e74c3c;
            background: #2c1a1a;
            color: #e74c3c;
            font-weight: 700;
        }}
        .card img {{
            width: 22px;
            height: 22px;
            object-fit: contain;
            flex-shrink: 0;
        }}
        .card .sem-escudo {{
            width: 22px;
            height: 22px;
            flex-shrink: 0;
        }}
    </style>
    </head>
    <body>
    <div class="grade" id="grade">
    </div>
    <script>
        const selecoes = {_json.dumps(dados_grade, ensure_ascii=False)};

        const grade = document.getElementById('grade');

        selecoes.forEach(function(s) {{
            const card = document.createElement('div');
            card.className = 'card' + (s.ativo ? ' ativo' : '');
            card.title = s.nome;

            if (s.escudo) {{
                const img = document.createElement('img');
                img.src = s.escudo;
                img.alt = s.nome;
                img.onerror = function() {{ this.style.display = 'none'; }};
                card.appendChild(img);
            }} else {{
                const ph = document.createElement('span');
                ph.className = 'sem-escudo';
                card.appendChild(ph);
            }}

            const label = document.createElement('span');
            label.textContent = s.nome;
            card.appendChild(label);

            card.addEventListener('click', function() {{
                // Localiza o radio oculto do Streamlit no DOM pai
                const radios = window.parent.document.querySelectorAll(
                    'input[type="radio"]'
                );
                for (let r of radios) {{
                    const lbl = r.closest('label') || r.parentElement;
                    const txt = lbl ? lbl.innerText.trim() : '';
                    if (txt === s.nome) {{
                        r.click();
                        break;
                    }}
                }}
            }});

            grade.appendChild(card);
        }});
    </script>
    </body>
    </html>
    """

    components.html(grade_html, height=altura_grade, scrolling=False)

    st.divider()

    selecao = st.session_state.selecao_ativa
    crest = selecoes[selecao]

    col_logo, col_titulo = st.columns([1, 6])

    with col_logo:
        if crest:
            st.image(crest, width=80)

    with col_titulo:
        st.subheader(selecao)

    nome_arquivo = selecao

    ajustes = {
        "South Africa": "South_Africa",
        "South Korea": "South_Korea",
        "United States": "United_States",
        "Bosnia and Herzegovina": "Bosnia_and_Herzegovina",
        "Cape Verde": "Cape_Verde",
        "DR Congo": "DR_Congo",
        "New Zealand": "New_Zealand",
        "Saudi Arabia": "Saudi_Arabia"
    }

    if selecao in ajustes:
        nome_arquivo = ajustes[selecao]

    nome_arquivo = nome_arquivo.replace(" ", "_")

    camisa_casa = f"assets/jerseys/{nome_arquivo}_home.png"
    camisa_fora = f"assets/jerseys/{nome_arquivo}_away.png"

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🏠 Uniforme Casa")

        if os.path.exists(camisa_casa):

            st.image(
                camisa_casa,
                use_container_width=True
            )

        else:

            st.warning(
                f"Arquivo não encontrado: {camisa_casa}"
            )

    with col2:

        st.markdown("### ✈️ Uniforme Visitante")

        if os.path.exists(camisa_fora):

            st.image(
                camisa_fora,
                use_container_width=True
            )

        else:

            st.warning(
                f"Arquivo não encontrado: {camisa_fora}"
            )