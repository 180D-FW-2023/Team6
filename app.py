import streamlit as st
import sqlite3
import time

# Function to get the last N notes
def get_latest_notes(limit=10):
    with sqlite3.connect('piano_notes.db') as conn:
        c = conn.cursor()
        c.execute("SELECT note FROM notes ORDER BY rowid DESC LIMIT ?", (limit,))
        latest_notes = c.fetchall()
    return [note[0] for note in latest_notes]

st.title('Piano Note Detection')

# Display the last note
last_note_container = st.empty()

# Button for refreshing the last 10 notes
if st.button('Refresh Last 10 Notes'):
    st.session_state['last_10_notes'] = get_latest_notes(10)

# Display the last 10 notes, update only when the button is pressed
if 'last_10_notes' in st.session_state:
    st.write("### Last 10 Notes Played:")
    st.write(', '.join(st.session_state['last_10_notes']))
else:
    st.write("### Last 10 Notes Played:")
    st.write("Press 'Refresh' to load notes.")

# Main loop to update the last note displayed
while True:
    # Fetch the latest note
    last_note = get_latest_notes(1)[0] if get_latest_notes(1) else "No notes detected yet."
    last_note_container.text(f'Last Note Played: {last_note}')
    time.sleep(0.3)  # Update interval for the last note
