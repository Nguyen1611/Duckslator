import json
import time
import os
import streamlit as st
from io import BytesIO
from streamlit_lottie import st_lottie

# Page 
st.set_page_config(
    page_title="# Duckslator",
    page_icon=":duck:",
    # initial_sidebar_state="collapsed",  # Sidebar hidden on start
)

# Animation

col1, col2, col3 = st.columns([0.35, 1, 0.1])

# Create a placeholder for the GIF and File
placeholder = col2.empty()
placeholder_gifload = st.empty()
header_placeholder = st.empty()
file_details_placeholder = st.empty()  # Placeholder for file details
preview_placeholder = st.empty() 

placeholder.image("gif2.gif", use_container_width=False, width=600)

# Side bar
with st.sidebar:
    st.title("🦆 Duckslator")
    st.subheader("The Ultimate Translator For Video And Audio.")
    st.header("⚙️ Settings")
    
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0

    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []
    

    
    uploaded_file = st.file_uploader("**Upload an audio or video file.**", type=["wav", "mp4", "mov"], key=st.session_state["file_uploader_key"],accept_multiple_files=False,)
    
    if st.button("🗑️ Clear Uploaded File"):
        st.session_state["file_uploader_key"] += 1
        st.rerun()


    
    
    # 17 language options
    languages = [
                "English 🇬🇧", "Spanish 🇪🇸", "French 🇫🇷", "German 🇩🇪", "Chinese 🇨🇳", "Japanese 🇯🇵", "Russian 🇷🇺", 
                "Portuguese 🇵🇹", "Italian 🇮🇹", "Arabic 🇸🇦", "Hindi 🇮🇳", "Bengali 🇧🇩", "Korean 🇰🇷", "Turkish 🇹🇷", 
                "Dutch 🇳🇱", "Polish 🇵🇱", "Swedish 🇸🇪"
                ]
            
    # User selects a language from the options
    selected_language = st.selectbox("**Choose your language**", languages, index= 0)
    

# File
if uploaded_file is not None:
    st.session_state["uploaded_files"] = uploaded_file
    # file details
    file_details = {
            "Filename": uploaded_file.name,
            "File type": uploaded_file.type,
            "File size": f"{uploaded_file.size} bytes"
        }
    header_placeholder.write("### **Uploaded File Details:**")
    file_details_placeholder.json(file_details)
    
    placeholder.empty()  # Clear the content of col2
    
    if file_details["File type"].startswith("audio/"):
        preview_placeholder.audio(uploaded_file, format=file_details["File type"])
    elif file_details["File type"].startswith("video/") or uploaded_file.name.endswith(".mp4"):
        preview_placeholder.video(uploaded_file)
    else:
        preview_placeholder.error("Unsupported file format.")


# Button
# Button to trigger language selection
# Show the expander with language selection when button is clicked

# Button 2: Upload file and translate to the chosen language
with st.sidebar:
    if st.button("⌛️ Translate File"):
        file_details_placeholder.empty()  # Removes the file details block
        preview_placeholder.empty()
        header_placeholder.empty()
    
        
        if uploaded_file is not None and selected_language:
            placeholder_gifload.image("gif1.gif", use_container_width=False, width=500)
        
            try:
                st.sidebar.write("Converting...")  # Show progress message in the sidebar
                
                # Simulate conversion logic
                output_buffer = uploaded_file  # Replace with your processing logic
                placeholder = col2.empty()  # Create a placeholder for col2
                # --- MOVE OUT OF SIDEBAR ---
                st.session_state['output_ready'] = True  # Flag for conversion completion
                st.session_state['output_buffer'] = output_buffer  # Store converted file
            except Exception as e:
                st.sidebar.error(f"An error occurred during conversion: {str(e)}")
        else:
            st.sidebar.write("Please upload a file to translate.")

# Main screen display
if st.session_state.get('output_ready'):
    
    output_buffer = st.session_state['output_buffer']  # Retrieve the converted file
    
    header_placeholder = st.empty()
    header_placeholder.write("### Converted File:")
    
    preview_placeholder = st.empty() 
    
    placeholder_gifload.empty()
    if output_buffer.type.startswith("audio/"):
        preview_placeholder.audio(output_buffer, format=output_buffer.type)
    else:
        preview_placeholder.video(output_buffer)
    
    # Add a download button
    check = st.download_button(
        label=f"Download file",
        data=output_buffer.getvalue(),
        file_name=f"converted_{file_details.get('Filename')}",
        mime=f"{file_details.get('File type')}"
    )
    
with st.sidebar:
        if st.button("🔄 Reset All"):  # When the Reset button is clicked
            st.session_state.clear()  # Clear all session state variables
            placeholder.empty()  # Clear the main placeholder
            header_placeholder.empty()  # Clear the header
            file_details_placeholder.empty()  # Clear file details
            preview_placeholder.empty()  # Clear preview
            st.sidebar.write("File and settings reset. Please upload a new file to translate.")
            st.rerun()  # Rerun the app to reset the interface