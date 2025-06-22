import streamlit as st
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display

from db import init_db
from recognize import recognize, T_RECORD, SR, TEMP_FOLDER, TEMP_PATH

st.set_page_config(
    page_title="Re:Chord",
    page_icon="🎧",
    layout="centered"
)

def show_recognition_tab():
    st.subheader("Record Audio")

    if 'recognizing' not in st.session_state:
        st.session_state['recognizing'] = False
    if 'result' not in st.session_state:
        st.session_state['result'] = None
    if 'stop_requested' not in st.session_state:
        st.session_state['stop_requested'] = False

    def stop_recognition():
        st.session_state['recognizing'] = False
        st.session_state['stop_requested'] = True

    if not st.session_state['recognizing']:
        if st.button("Start Recording", type="primary"):
            st.session_state['recognizing'] = True
            st.session_state['result'] = None
            st.session_state['stop_requested'] = False
            st.rerun()
    else:
        st.button("Stop", on_click=stop_recognition, type="secondary")

    # Recognition loop
    if st.session_state['recognizing'] and not st.session_state['stop_requested']:
        with st.spinner("Listening and recognizing... (press Stop to end)"):
            os.makedirs(TEMP_FOLDER, exist_ok=True)
            # Record audio chunk
            recording = sd.rec(int(T_RECORD * SR), samplerate=SR, channels=1)
            sd.wait()
            sf.write(TEMP_PATH, recording, SR)
            conn = init_db()
            title, score, recommendations, url = recognize(conn, TEMP_PATH)
            conn.close()
            if title:
                audio_data, _ = librosa.load(TEMP_PATH, sr=SR)
                st.session_state['result'] = (TEMP_PATH, audio_data, title, score, recommendations, url)
                st.session_state['recognizing'] = False
                st.rerun()
            else:
                # No match, rerun to record again unless stopped
                if not st.session_state['stop_requested']:
                    st.rerun()

    if st.session_state['result']:
        temp_path, audio_data, title, score, recommendations, url = st.session_state['result']
        
        st.markdown(f"### Match Found: [{title}]({url})")
        st.markdown(f"**Confidence:** {score}")
        

        
        st.markdown("#### Similar Songs You Might Like:")
        for _, name, c, rec_url in recommendations:
            st.markdown(f"- [{name}]({rec_url})  _(Shared tags: {c})_", unsafe_allow_html=True)


        st.markdown("#### Snippet Recorded")
        st.markdown("This is the audio you just recorded and matched. You can listen to it below.")
        st.audio(temp_path)
        
        st.markdown("### Audio Waveform & Spectrogram")
        st.markdown(
            "The waveform (left) shows amplitude over time. "
            "The spectrogram (right) visualizes frequencies present in your audio over time. "
            "Brighter colors indicate stronger frequencies."
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Waveform**")
            fig_wave = plt.figure(figsize=(6, 3))
            librosa.display.waveshow(audio_data, sr=SR)
            plt.title('Audio Waveform')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.tight_layout()
            st.pyplot(fig_wave)
            plt.close(fig_wave)

        with col2:
            st.markdown("**Spectrogram**")
            D = librosa.amplitude_to_db(np.abs(librosa.stft(audio_data)), ref=np.max)
            fig_spec = plt.figure(figsize=(6, 3))
            img = librosa.display.specshow(D, y_axis='log', x_axis='time', sr=SR, cmap='viridis')
            plt.title('Spectrogram')
            plt.colorbar(img, format="%+2.f dB")
            plt.tight_layout()
            st.pyplot(fig_spec)
            plt.close(fig_spec)

        if os.path.exists(temp_path):
            os.remove(temp_path)
        st.session_state['result'] = None



def show_help_tab():
    st.markdown("""
### How to Use

#### Introduction

Welcome to **Re:Chord**, an interactive application for real-time song recognition, music recommendations and insightful sound visualization.

This project was always something that I wanted to create.
After diving into Digital Communications during my coursework, I was motivated to build something hands-on.
Re:Chord is designed to identify songs from short 5-second audio snippets and recommend similar tracks by integrating techniques from signal processing, audio fingerprinting, and content-based recommendation models.

---
#### Quick Guide

1. **Start Recording:**  
   Tap **Start Recording** and sing, hum, or play music for 5–10 seconds.

2. **Identify the Song:**  
   Re:Chord extracts audio features, hashes frequency peaks, and searches the database for a match.

3. **View Results:**  
   - See the matched title with a confidence score.  
   - Listen to your clip and check waveform + spectrogram visuals.

4. **Discover More:**  
   Get top 5 similar songs based on tags like genre, mood, and instruments.

---

#### How It Works

- Built using **Python**, **Streamlit**, and **Librosa**.  
- Uses **audio fingerprinting** and **content-based filtering**.  
- Visuals generated with **Matplotlib**.

Re:Chord is a fun, hands-on tool to explore how machines recognize sound and suggest similar music — great for learning, demos, and musical curiosity.

---

#### Music Source

All tracks are sourced from **[Pixabay Music](https://pixabay.com/music/)** — free for educational and demo use.


""")

    with st.expander("Supported Songs (30 tracks)"):
        st.markdown("""
1. [alone-296348](https://pixabay.com/music/future-bass-alone-296348/)  
2. [amalgam-217007](https://pixabay.com/music/future-bass-amalgam-217007/)  
3. [better-day-186374](https://pixabay.com/music/beats-better-day-186374/)  
4. [coverless-book-lofi-186307](https://pixabay.com/music/beats-coverless-book-lofi-186307/)  
5. [creative-technology-showreel-241274](https://pixabay.com/music/beats-creative-technology-showreel-241274/)  
6. [dont-talk-315229](https://pixabay.com/music/future-bass-dont-talk-315229/)  
7. [eona-emotional-ambient-pop-351436](https://pixabay.com/music/beats-eona-emotional-ambient-pop-351436/)  
8. [ethereal-vistas-191254](https://pixabay.com/music/beats-ethereal-vistas-191254/)  
9. [flow-211881](https://pixabay.com/music/beats-flow-211881/)  
10. [for-her-chill-upbeat-summel-travel-vlog-and-ig-music-royalty-free-use-202298](https://pixabay.com/music/beats-for-her-chill-upbeat-summel-travel-vlog-and-ig-music-royalty-free-use-202298/)  
11. [future-design-344320](https://pixabay.com/music/future-bass-future-design-344320/)  
12. [gardens-stylish-chill-303261](https://pixabay.com/music/rnb-gardens-stylish-chill-303261/)  
13. [gorila-315977](https://pixabay.com/music/beats-gorila-315977/)  
14. [groovy-ambient-funk-201745](https://pixabay.com/music/funk-groovy-ambient-funk-201745/)  
15. [in-slow-motion-inspiring-ambient-lounge-219592](https://pixabay.com/music/future-bass-in-slow-motion-inspiring-ambient-lounge-219592/)  
16. [jungle-waves-drumampbass-electronic-inspiring-promo-345013](https://pixabay.com/music/drum-n-bass-jungle-waves-drumampbass-electronic-inspiring-promo-345013/)  
17. [kugelsicher-by-tremoxbeatz-302838](https://pixabay.com/music/beats-kugelsicher-by-tremoxbeatz-302838/)  
18. [lazy-day-stylish-futuristic-chill-239287](https://pixabay.com/music/beats-lazy-day-stylish-futuristic-chill-239287/)  
19. [lost-in-dreams-abstract-chill-downtempo-cinematic-future-beats-270241](https://pixabay.com/music/beats-lost-in-dreams-abstract-chill-downtempo-cinematic-future-beats-270241/)  
20. [movement-200697](https://pixabay.com/music/upbeat-movement-200697/)  
21. [night-detective-226857](https://pixabay.com/music/beats-night-detective-226857/)  
22. [nightfall-future-bass-music-228100](https://pixabay.com/music/future-bass-nightfall-future-bass-music-228100/)  
23. [perfect-beauty-191271](https://pixabay.com/music/pulses-perfect-beauty-191271/)  
24. [sad-soul-chasing-a-feeling-185750](https://pixabay.com/music/beats-sad-soul-chasing-a-feeling-185750/)  
25. [so-fresh-315255](https://pixabay.com/music/future-bass-so-fresh-315255/)  
26. [solitude-dark-ambient-electronic-197737](https://pixabay.com/music/upbeat-solitude-dark-ambient-electronic-197737/)  
27. [spinning-head-271171](https://pixabay.com/music/trap-spinning-head-271171/)  
28. [stylish-deep-electronic-262632](https://pixabay.com/music/future-bass-stylish-deep-electronic-262632/)  
29. [tell-me-the-truth-260010](https://pixabay.com/music/future-bass-tell-me-the-truth-260010/)  
30. [vlog-music-beat-trailer-showreel-promo-background-intro-theme-274290](https://pixabay.com/music/beats-vlog-music-beat-trailer-showreel-promo-background-intro-theme-274290/)  
        """)
    
def show_about_tab():
    st.markdown("""
    ### About Me

    Hi, I’m **Manthan Parmar** — currently pursuing a B.Tech. (Honours) in **Information and Communication Technology** (2022–2026), with a **minor in Computational Science** at Dhirubhai Ambani Institute of Information and Communication Technology (DA-IICT), now known as **DAU**.

    I’m passionate about building at the intersection of **code, math, and data**. I particularly enjoy working on **data analytics** and **visualization**, turning raw information into interactive tools and intuitive insights.

    My current focus lies in **Machine Learning**, especially **Supervised Learning** and **Reinforcement Learning**. I’ve also been exploring **Neural Networks**, **Deep Learning**, and **Financial Analytics** — and I’m fascinated by how **Generative AI** is transforming creative fields like **art** and **music**.

    Beyond the technical world, I enjoy keeping up with trends in **music**, **gaming**, and **fine arts**, always looking for ways to blend creativity with computation.

    I love learning, building, and collaborating on meaningful tech projects.  
    Thanks for exploring **Re:Chord** — I hope you enjoy using it as much as I enjoyed creating it!

    ---

    ### Connect with me:

    - 🔗 [LinkedIn](https://www.linkedin.com/in/manthan-d-parmar/)  
    - 🌐 [GitHub](https://github.com/Manthan-D-Parmar)

    *Re:Chord is released for educational purposes—feel free to dive into the code, experiment, and learn!*  
    """)



if __name__ == "__main__":
    st.markdown("""## 🎧 Re:Chord : Song Recognition and Recommendation
    Identify Songs. Discover Similar Tracks. Visualise Audio.""")

    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = False
    
    tab_recognition, tab_help, tab_about = st.tabs(["Music Recognition", "Help", "About"])
    
    with tab_recognition:
        show_recognition_tab()
    
    with tab_help:
        show_help_tab()
    
    with tab_about:
        show_about_tab()