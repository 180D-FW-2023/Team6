import streamlit as st
import sqlite3
import time

def get_latest_note():
    conn = sqlite3.connect('piano_notes.db')
    c = conn.cursor()
    c.execute("SELECT note FROM notes ORDER BY rowid DESC LIMIT 1")
    latest_note = c.fetchone()
    conn.close()
    return latest_note[0] if latest_note else "No notes detected yet."

st.title('Piano Note Detection')

latest_iteration = st.empty()
bar = st.progress(0)

for i in range(100):
    # Update the progress bar with each iteration.
    latest_iteration.text(f'Latest Note: {get_latest_note()}')
    bar.progress(i + 1)
    time.sleep(0.1)
