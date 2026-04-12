import datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


# -------------------------------
# Google Sheets Verbindung
# -------------------------------
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


# -------------------------------
# State für Button
# -------------------------------
if "submitted" not in st.session_state:
    st.session_state.submitted = False


# -------------------------------
# Config
# -------------------------------
st.set_page_config(
    page_title="Umfrage: Vergleich von Songtexten",
    layout="wide"
)


@st.cache_data
def load_pairs():
    df = pd.read_csv("songpairs.csv")
    df.columns = df.columns.str.strip()
    return df


pairs = load_pairs()

st.title("Umfrage: Vergleich von Songtexten – Ähnlichkeitsbewertung")
st.write("**Geschätzte Dauer: 10–20 Minuten**")
st.write("Erstellt von Steve Tacke.")

st.header("Hinweise zur Bewertung")

st.markdown("""
Bitte bewerten Sie die folgenden Textpaare ausschließlich hinsichtlich ihrer **inhaltlichen (semantischen) Ähnlichkeit**.  
Melodie, Genre oder Bekanntheit der Songs sollen **keine Rolle spielen**.

### Bedeutung der Bewertungsskala:
- **1 = gar nicht ähnlich**
- **2 = eher unähnlich**
- **3 = teilweise ähnlich**
- **4 = eher ähnlich**
- **5 = sehr ähnlich**
- **KA = keine Angabe**

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

Sie können bei einzelnen Kriterien **„KA“ (keine Angabe)** wählen, wenn Sie sich unsicher sind oder das Kriterium nicht sinnvoll bewerten können.
""")

st.divider()

# -------------------------------
# Optionale Fragen
# -------------------------------
st.header("Optionale Angaben")

music_interest = st.selectbox(
    "Wie häufig achten Sie bewusst auf Songtexte?",
    ["Keine Angabe", "Nie", "Selten", "Manchmal", "Oft", "Sehr oft"],
)

language_confidence = st.selectbox(
    "Wie sicher fühlen Sie sich beim Verstehen englischer Songtexte?",
    ["Keine Angabe", "Sehr unsicher", "Unsicher", "Mittel", "Sicher", "Sehr sicher"],
)

st.divider()

# -------------------------------
# Bewertung
# -------------------------------
responses = []

for _, row in pairs.iterrows():
    pair_id = row["pair_id"]

    st.markdown(f"## Paar {pair_id}")

    colA, colB = st.columns(2)
    with colA:
        st.subheader("Text A")
        st.text(row["textA"].replace("\\n", "\n"))
    with colB:
        st.subheader("Text B")
        st.text(row["textB"].replace("\\n", "\n"))

    st.caption("1 = gar nicht ähnlich | 5 = sehr ähnlich | KA = keine Angabe")

    # -------- THEMA --------
    thema_raw = st.radio(
        f"Thematische Ähnlichkeit – Paar {pair_id}",
        [1, 2, 3, 4, 5, "KA"],
        index=2,
        horizontal=True,
        key=f"{pair_id}_thema",
    )
    thema_value = 0 if thema_raw == "KA" else thema_raw

    # -------- EMOTION --------
    emotion_raw = st.radio(
        f"Emotionale Ähnlichkeit – Paar {pair_id}",
        [1, 2, 3, 4, 5, "KA"],
        index=2,
        horizontal=True,
        key=f"{pair_id}_emotion",
    )
    emotion_value = 0 if emotion_raw == "KA" else emotion_raw

    # -------- METAPHOR --------
    metaphor_raw = st.radio(
        f"Bildsprache / Metaphern – Paar {pair_id}",
        [1, 2, 3, 4, 5, "KA"],
        index=2,
        horizontal=True,
        key=f"{pair_id}_metaphor",
    )
    metaphor_value = 0 if metaphor_raw == "KA" else metaphor_raw

    # -------- GESAMT --------
    overall_raw = st.radio(
        f"Gesamteindruck – Paar {pair_id}",
        [1, 2, 3, 4, 5, "KA"],
        index=2,
        horizontal=True,
        key=f"{pair_id}_overall",
    )
    overall_value = 0 if overall_raw == "KA" else overall_raw

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

# -------------------------------
# Freitext
# -------------------------------
st.header("Abschluss")

similar_songs_free_text = st.text_area(
    "Kennen Sie Songs, die Sie als ähnlich empfinden?",
    height=150,
)

# -------------------------------
# Absenden
# -------------------------------
if st.button("Antworten absenden", disabled=st.session_state.submitted):
    st.session_state.submitted = True

    with st.spinner("Antworten werden gespeichert..."):
        try:
            sheet = connect_to_gsheet()
            timestamp = datetime.datetime.now().isoformat()

            for r in responses:
                sheet.append_row(
                    [
                        timestamp,
                        music_interest,
                        language_confidence,
                        r["pairid"],
                        r["thema"],
                        r["emotion"],
                        r["metaphor"],
                        r["overall"],
                        similar_songs_free_text,
                    ]
                )

            st.success("Danke! Ihre Antworten wurden gespeichert.")

        except Exception as e:
            st.error(f"Fehler beim Speichern: {e}")
            st.session_state.submitted = False
