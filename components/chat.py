import streamlit as st
from datetime import datetime

def render_chat():
    st.markdown("""
        <style>
        .chat-container {
            background: linear-gradient(45deg, #1E1E1E, #2D2D2D);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #3D3D3D;
            height: 500px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        .message {
            padding: 10px 15px;
            border-radius: 10px;
            margin: 5px 0;
            max-width: 80%;
        }
        .user-message {
            background: #2D2D2D;
            margin-left: auto;
            color: #FFFFFF;
        }
        .bot-message {
            background: #00FF94;
            color: #0E1117;
        }
        .timestamp {
            font-size: 0.8em;
            color: #888888;
            margin-top: 5px;
        }
        .input-container {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize chat history in session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Chat container
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for message in st.session_state.messages:
        message_class = "user-message" if message["is_user"] else "bot-message"
        st.markdown(f"""
            <div class='message {message_class}'>
                {message["text"]}
                <div class='timestamp'>{message["timestamp"]}</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Input area
    col1, col2 = st.columns([4, 1])
    
    with col1:
        message = st.text_input("", placeholder="Scrivi un messaggio...", key="chat_input")
    
    with col2:
        if st.button("Invia", use_container_width=True):
            if message:
                # Add user message
                st.session_state.messages.append({
                    "text": message,
                    "is_user": True,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                # Simulate bot response
                bot_response = "Grazie per il tuo messaggio! Questa è una risposta di esempio."
                st.session_state.messages.append({
                    "text": bot_response,
                    "is_user": False,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                # Clear input
                st.session_state.chat_input = ""
                st.rerun()
