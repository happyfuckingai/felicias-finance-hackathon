#!/usr/bin/env python3
"""
🧪 Enkel testversion av Streamlit-appen för att verifiera att allt fungerar
"""

import streamlit as st
import sys
import os

# Fix path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="🧪 Test - AI Crypto Trader",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Testversion - AI Crypto Trading Platform")
st.markdown("Enkel test för att verifiera att allt fungerar!")

# Test imports
try:
    from rules.intent_processor import IntentProcessor
    st.success("✅ Intent Processor: OK")

    from core.llm_integration import LLMIntegration
    st.success("✅ LLM Integration: OK")

    from handlers.risk import RiskHandler
    st.success("✅ Risk Handler: OK")

except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.info("Kontrollera att alla filer finns och att PYTHONPATH är korrekt")

# Simple chat interface
st.header("💬 Test Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Testa att skriva något..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Simple AI response
    response = f"Du skrev: '{prompt}'. Detta är en testversion!"
    if "bitcoin" in prompt.lower():
        response = "📊 **AI Analys av Bitcoin:** Positiv trend med 85% konfidens!"
    elif "ethereum" in prompt.lower():
        response = "📊 **AI Analys av Ethereum:** Stark fundamentals, rekommenderar köp!"
    elif "risk" in prompt.lower():
        response = "🛡️ **Riskråd:** Använd alltid stop-loss och diversifiera!"

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

# System info
st.header("🔧 System Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Python Version", f"{sys.version.split()[0]}")

with col2:
    st.metric("Working Directory", os.getcwd())

with col3:
    st.metric("Platform", sys.platform)

st.info("✅ Om du ser detta fungerar grundinställningarna! Nu kan du köra den fullständiga appen.")

if st.button("🚀 Öppna Fullständig App"):
    st.info("Använd: `python crypto/run_streamlit.py` i terminalen för den fullständiga upplevelsen!")