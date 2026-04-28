import streamlit as st
import os
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder
from groq import Groq
import mongo as db


load_dotenv()


api_key = os.getenv("GROQ_API_KEY")


if api_key:
    client = Groq(api_key=api_key)
else:
    st.error("Hiba: Az API kulcs nem található a .env fájlban!")
    st.stop() 

st.set_page_config(page_title="MI-hészet - Okos Méhész Napló", page_icon="🐝")
st.title("MI-hészet")
st.subheader("Generatív MI alapú méhészeti szakértői rendszer")


with st.sidebar:
    st.header("⚙️ Modell Beállítások")
    
  
    model_option = st.selectbox(
        "Válassz modellt:",
        ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    )
    
    
    temp = st.slider("Kreativitás (hőmérséklet):", min_value=0.0, max_value=1.0, value=0.2, step=0.1)

    max_tokens = st.slider("Maximális válaszhossz :", min_value=100, max_value=800, value=300)

    st.info("""
    **Tipp:** A diagnózishoz alacsony (0.2), 
    ötleteléshez magasabb (0.7) 
    hőmérséklet ajánlott.
    """)

    def analyze_beekeeping_note(user_text):
   
        system_prompt = """
            SZEMÉLYISÉG (Persona):
            Te egy tudományos alapossággal rendelkező mesterméhész és állategészségügyi szakértő vagy. 
            Segítesz a terepen dolgozó méhészeknek a terepi jegyzeteik elemzésében.

            FELADAT ÉS LOGIKA (Chain of Thought):
            A választ szigorúan az alábbi lépésekben építsd fel:
            1. ADATOK: Listázd ki a megfigyelt tényeket.
            2. ANALÍZIS: Értékeld az összefüggéseket (pl. időjárás vs. hordás, anya állapota vs. fiasítás).
            3. DIAGNÓZIS: Mondd ki, mi a család aktuális állapota.
            4. JAVASLAT: Írj 3 konkrét teendőt fontossági sorrendben.

            PÉLDA (Few-shot):
            Bevitel: '6-os kaptár: sok a fedett fias, de kevés a hely, az anyát láttam.'
            Válasz:
            - Adatok: Erős népesség, sok fiasítás, helyhiány.
            - Analízis: A család kinőtte a fészket, a rajzási ösztön bármikor beindulhat.
            - Diagnózis: Rajzásközeli állapot.
            - Javaslat: 1. Új fiók felhelyezése. 2. Keretkivétel (csapolás). 3. Itatás ellenőrzése.
            """
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Itt a jegyzetem az elemzéshez: {user_text}"}
                ],
                model=model_option,
                temperature=temp,
                max_tokens=max_tokens,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Hiba történt az elemzés során: {str(e)}"
st.markdown("""
Írd be a kaptár mellett készített gyors jegyzeteidet. 
Az MI segít kielemezni a család állapotát és javaslatokat tesz a következő lépésekre.
""")
audio = mic_recorder(
    start_prompt="🎤 Beszéd indítása",
    stop_prompt="🛑 Megállítás",
    key='recorder'
)
st.session_state.beszed_szoveg = st.session_state.get('beszed_szoveg', "")



tab1, tab2 = st.tabs(["📝 Új bejegyzés", "📚 Korábbi naplók"])

with tab1:
   with tab1:
    # 1. Előbb feldolgozzuk a hangot, ha van felvétel
    if audio:
        with st.spinner("Hang feldolgozása..."):
            try:
                transcription = client.audio.transcriptions.create(
                    file=("memo.wav", audio['bytes']),
                    model="whisper-large-v3-turbo",
                    language="hu"
                )
                # Beírjuk a session_state-be a felismert szöveget
                st.session_state.beszed_szoveg = transcription.text
            except Exception as e:
                st.error(f"Hiba a hangfelismerésben: {e}")

    # 2. Megjelenítjük a szövegmezőt
    # Ha van valami a beszed_szoveg-ben, az lesz az alapértelmezett érték (value)
    input_text = st.text_area(
        "Mai naplóbejegyzés:", 
        value=st.session_state.get('beszed_szoveg', ""),
        height=150, 
        placeholder="Írj ide vagy használd a mikrofont..."
    )

    # 3. Elemzés gomb
    if st.button(" Elemzés futtatása", type="primary"):
        if input_text:
            with st.spinner("Elemzés..."):
                result = analyze_beekeeping_note(input_text)
                db.save_entry(input_text, result)
                st.success("Bejegyzés mentve!")
                st.write(result)
                # Mentés után opcionálisan törölhetjük a session_state-et:
                st.session_state.beszed_szoveg = ""
        else:
            st.warning("Üres bejegyzés")
with tab2:
    st.title("📚 Naplóarchívum")
    history = db.get_entries()
    
    if not history:
        st.info("Még nincsenek mentett bejegyzések a felhőben.")
    else:
        for bejegyzes in history:
            # Itt kulcsok alapján érjük el az adatokat (bejegyzes['kulcs'])
            datum = bejegyzes.get('datum', 'Nincs dátum')
            tartalom = bejegyzes.get('tartalom', '')
            elemzes = bejegyzes.get('elemzes', '')
            
            with st.expander(f"📅 {datum}"):
                st.write(f"**Eredeti jegyzet:** {tartalom}")
                st.markdown("---")
                st.markdown(f"**Szakértői elemzés:**\n\n{elemzes}")
            
st.markdown("---")
st.caption("MI-hészet v1.0")