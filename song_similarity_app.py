import datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


def connect_to_gsheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open("song_similarity_results").sheet1
    return sheet


st.set_page_config(page_title="Vergleich von Songtexten", layout="wide")


@st.cache_data
def load_pairs():
    df = pd.read_csv("songpairs.csv")
    # df.columns = df.columns.str.strip()
    return df


pairs = load_pairs()

st.title("Umfrage: Vergleich von Songtexten – Ähnlichkeitsbewertung Dauer 10-20 Minuten")

st.write(
    "Erstellt von Steve Tacke."
)
st.header("Hinweise zur Bewertung")

st.markdown("""
Bitte bewerten Sie die folgenden Textpaare ausschließlich hinsichtlich ihrer **inhaltlichen (semantischen) Ähnlichkeit**.  
Melodie, Genre oder Bekanntheit der Songs sollen **keine Rolle spielen**.

### Bedeutung der Bewertungsskala:
- **1 = gar nicht ähnlich**
- **3 = teilweise ähnlich**
- **5 = sehr ähnlich**

Zwischenwerte können entsprechend abgestuft verwendet werden.

### Erklärung der Kriterien:

**Thematische Ähnlichkeit**  
→ Bezieht sich auf das grundlegende Thema des Textes  
(z. B. Liebe, Trennung, Einsamkeit, Selbstfindung)

**Emotionale Ähnlichkeit**  
→ Bezieht sich auf die vermittelte Stimmung oder Emotion  
(z. B. traurig, hoffnungsvoll, wütend)

**Bildsprache / Metaphern**  
→ Bezieht sich auf sprachliche Bilder oder Vergleiche  
(z. B. „gebrochenes Herz“, „im Regen stehen“)  
→ Falls keine oder kaum Metaphern vorhanden sind, können Sie **„Keine Angabe (KA)“** wählen

**Gesamteindruck**  
→ Subjektive Einschätzung, ob sich die Textpassagen insgesamt ähnlich anfühlen  
→ Also: *„Wirken die Texte wie die gleiche Aussage – nur anders formuliert?“*

---

Sie können bei einzelnen Kriterien **„KA“ (keine Angabe)** wählen, wenn Sie sich unsicher sind oder das Kriterium nicht sinnvoll bewerten können.
""")

# --------------------------------------------------
# Optionale Fragen ganz oben
# --------------------------------------------------
st.header("Optionale Angaben")

music_interest = st.selectbox(
    "Wie häufig achtest du bewusst auf Songtexte? (optional)",
    options=[
        "Keine Angabe",
        "Nie oder fast nie",
        "Selten",
        "Manchmal",
        "Oft",
        "Sehr oft",
    ],
    index=0,
)

language_confidence = st.selectbox(
    "Wie sicher fühlst du dich beim Verstehen englischer Songtexte? (optional)",
    options=[
        "Keine Angabe",
        "Sehr unsicher",
        "Eher unsicher",
        "Mittel",
        "Eher sicher",
        "Sehr sicher",
    ],
    index=0,
)

st.divider()

# --------------------------------------------------
# Songpaare bewerten
# --------------------------------------------------
responses = []

for _, row in pairs.iterrows():
    pair_id = row["pair_id"]

    st.markdown(f"## Paar {pair_id}")

    text_col1, text_col2 = st.columns(2)
    with text_col1:
        st.subheader("Text A")
        st.text(row["textA"])
    with text_col2:
        st.subheader("Text B")
        st.text(row["textB"])

    st.caption("KA = keine Angabe")

    # -------- THEMA --------
    label_col, checkbox_col = st.columns([8, 1], vertical_alignment="center")
    with label_col:
        st.markdown("**Thematische Ähnlichkeit**")
    with checkbox_col:
        no_thema = st.checkbox("KA", key=f"{pair_id}_thema_na")

    thema = st.slider(
        f"Thematische Ähnlichkeit – Paar {pair_id}",
        min_value=1,
        max_value=5,
        value=3,
        disabled=no_thema,
        key=f"{pair_id}_thema",
        label_visibility="collapsed",
    )
    thema_value = 0 if no_thema else thema

    # -------- EMOTION --------
    label_col, checkbox_col = st.columns([8, 1], vertical_alignment="center")
    with label_col:
        st.markdown("**Emotionale Ähnlichkeit**")
    with checkbox_col:
        no_emotion = st.checkbox("KA", key=f"{pair_id}_emotion_na")

    emotion = st.slider(
        f"Emotionale Ähnlichkeit – Paar {pair_id}",
        min_value=1,
        max_value=5,
        value=3,
        disabled=no_emotion,
        key=f"{pair_id}_emotion",
        label_visibility="collapsed",
    )
    emotion_value = 0 if no_emotion else emotion

    # -------- METAPHOR --------
    label_col, checkbox_col = st.columns([8, 1], vertical_alignment="center")
    with label_col:
        st.markdown("**Bildsprache / Metaphern**")
    with checkbox_col:
        no_metaphor = st.checkbox("KA", key=f"{pair_id}_metaphor_na")

    metaphor = st.slider(
        f"Bildsprache / Metaphern – Paar {pair_id}",
        min_value=1,
        max_value=5,
        value=3,
        disabled=no_metaphor,
        key=f"{pair_id}_metaphor",
        label_visibility="collapsed",
    )
    metaphor_value = 0 if no_metaphor else metaphor

    # -------- GESAMT --------
    label_col, checkbox_col = st.columns([8, 1], vertical_alignment="center")
    with label_col:
        st.markdown("**Gesamteindruck**")
    with checkbox_col:
        no_overall = st.checkbox("KA", key=f"{pair_id}_overall_na")

    overall = st.slider(
        f"Gesamteindruck – Paar {pair_id}",
        min_value=1,
        max_value=5,
        value=3,
        disabled=no_overall,
        key=f"{pair_id}_overall",
        label_visibility="collapsed",
    )
    overall_value = 0 if no_overall else overall

    responses.append(
        {
            "pairid": pair_id,
            "thema": thema_value,
            "emotion": emotion_value,
            "metaphor": metaphor_value,
            "overall": overall_value,
        }
    )

    st.divider()

# --------------------------------------------------
# Offene Abschlussfrage
# --------------------------------------------------
st.header("Abschluss")

similar_songs_free_text = st.text_area(
    "Kennst du Songs, die du textlich bzw. semantisch ähnlich findest? "
    "Dann trage sie hier gerne ein. (optional)",
    height=150,
)

# --------------------------------------------------
# Vorschau der Antworten
# --------------------------------------------------
preview_rows = []
for r in responses:
    preview_rows.append(
        {
            "music_interest": music_interest,
            "language_confidence": language_confidence,
            "pairid": r["pairid"],
            "thema": r["thema"],
            "emotion": r["emotion"],
            "metaphor": r["metaphor"],
            "overall": r["overall"],
            "similar_songs_free_text": similar_songs_free_text,
        }
    )

result_df = pd.DataFrame(preview_rows)

with st.expander("Vorschau der Antworten anzeigen"):
    st.dataframe(result_df, use_container_width=True)

# --------------------------------------------------
# Antworten absenden
# --------------------------------------------------
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if st.button("Antworten absenden", disabled=st.session_state.submitted):
    st.session_state.submitted = True

    with st.spinner("Antworten werden gespeichert..."):
        try:
            sheet = connect_to_gsheet()
            import datetime

            timestamp = datetime.datetime.now().isoformat()

            for r in responses:
                sheet.append_row([
                    timestamp,
                    music_interest,
                    language_confidence,
                    r["pairid"],
                    r["thema"],
                    r["emotion"],
                    r["metaphor"],
                    r["overall"],
                    similar_songs_free_text
                ])

            st.success("Danke! Ihre Antworten wurden gespeichert.")

        except Exception as e:
            st.error(f"Fehler beim Speichern: {e}")
            st.session_state.submitted = False
