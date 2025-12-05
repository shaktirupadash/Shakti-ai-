import streamlit as st

st.title("⚡ Shakti-AI ⚡")
st.write("Welcome to my first Streamlit app!")

name = st.text_input("What's your name my dear?")
if name:
    st.write(f"Hello, {name}! 👋")
