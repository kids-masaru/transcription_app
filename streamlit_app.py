import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import tempfile
import time

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI文字起こしアプリ",
    page_icon="🎙️",
    layout="centered"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        height: 3em;
        font-size: 20px;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def init_gemini(api_key):
    genai.configure(api_key=api_key)

def main():
    st.title("🎙️ AI文字起こしアプリ")
    st.markdown("音声ファイルをアップロードして、AIに文字起こしを依頼しましょう。")

    # Sidebar for Settings
    with st.sidebar:
        st.header("設定 (Settings)")
        
        # API Key Handling
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Check Streamlit secrets if env var not found
        if not api_key and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            
        if not api_key:
            api_key = st.text_input("Gemini API Keyを入力してください", type="password")
            if not api_key:
                st.warning("⚠️ APIキーが必要です。")
                st.stop()
        
        st.success("✅ API Key loaded")
        
        model_name = st.selectbox(
            "使用モデル (Model)",
            ["gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-3-pro"],
            index=0
        )

    # Main Interface
    uploaded_file = st.file_uploader("音声ファイルを選択してください (MP3, M4A, WAV)", type=['mp3', 'm4a', 'wav'])

    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/mp3')
        
        if st.button("文字起こし開始 (Start Transcription)"):
            try:
                init_gemini(api_key)
                
                # Progress Bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 1. Save uploaded file to temp
                status_text.text("📂 ファイルを準備中... (Preparing file...)")
                progress_bar.progress(10)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                try:
                    # 2. Upload to Gemini
                    status_text.text("☁️ サーバーへアップロード中... (Uploading to Gemini...)")
                    progress_bar.progress(30)
                    
                    audio_file = genai.upload_file(tmp_file_path)
                    
                    # Wait for processing
                    while audio_file.state.name == "PROCESSING":
                        status_text.text("⏳ 音声処理待ち... (Processing audio...)")
                        time.sleep(1)
                        audio_file = genai.get_file(audio_file.name)
                    
                    if audio_file.state.name == "FAILED":
                        raise Exception("Audio file processing failed on server.")

                    # 3. Generate Content
                    status_text.text("🤖 AIが文字起こし中... (AI is transcribing...)")
                    progress_bar.progress(60)
                    
                    model = genai.GenerativeModel(model_name)
                    prompt = (
                        "音声データを一字一句、聞こえたまま忠実に文字起こししてください。\n"
                        "整文、要約、言い換え、話者分離のタグ付けは一切行わないでください。\n"
                        "フィラー（えー、あー等）も発話されている通りに記述してください。"
                    )
                    
                    # Spinner for the actual generation which can take time
                    with st.spinner("文字起こしを実行しています...これには数分かかる場合があります。"):
                        response = model.generate_content([prompt, audio_file])
                    
                    progress_bar.progress(100)
                    status_text.text("✅ 完了しました！ (Done!)")
                    
                    # 4. Display Result
                    st.subheader("📝 文字起こし結果")
                    st.text_area("Result", value=response.text, height=400)
                    
                    # 5. Download Button
                    st.download_button(
                        label="💾 テキストファイルをダウンロード (Download .txt)",
                        data=response.text,
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}.txt",
                        mime="text/plain"
                    )
                    
                finally:
                    # Cleanup temp file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                        
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                progress_bar.empty()
                status_text.empty()

if __name__ == "__main__":
    main()
