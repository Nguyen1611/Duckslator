import os
import requests
import streamlit as st

# Backend API URL
API_URL = "http://127.0.0.1:8000/process-file/"

# Page Configuration
st.set_page_config(
    page_title="Duckslator",
    page_icon=":duck:",
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
    
# Display uploaded file details and preview
if uploaded_file is not None:
    st.session_state["uploaded_files"] = uploaded_file
    file_details = {"Filename": uploaded_file.name,
                    "File type": uploaded_file.type,
                    "File size": f"{uploaded_file.size / 1024:.2f} KB"}

    header_placeholder.write("### **Uploaded File Details:**")
    file_details_placeholder.json(file_details)
    
    placeholder.empty()  # Clear the content of col2
    
    # Use preview_placeholder for audio or video preview
    if file_details["File type"].startswith("audio/"):
        preview_placeholder.audio(uploaded_file, format=file_details["File type"])
    elif file_details["File type"].startswith("video/") or uploaded_file.name.endswith(".mp4"):
        preview_placeholder.video(uploaded_file)
    else:
        preview_placeholder.error("Unsupported file format.")
        
# Sidebar Button for Translation
with st.sidebar:
    if st.button("⌛️ Translate File"):
        file_details_placeholder.empty()  # Removes the file details block
        preview_placeholder.empty()
        header_placeholder.empty()

        if uploaded_file is not None and selected_language:
            placeholder_gifload.image("gif1.gif", use_container_width=False, width=700)
            try:
                # Remove language emoji for backend compatibility
                selected_language = selected_language.split(" ")[0]

                st.sidebar.write("Uploading file to backend for processing...")
                
                # Send file and language selection to the backend
                files = {"file": uploaded_file}
                data = {"language": selected_language}
                response = requests.post(API_URL, files=files, data=data)

                # Check if the request was successful
                if response.status_code == 200:
                    # Save the processed file
                    output_file_path = "translated_video.mp4"
                    with open(output_file_path, "wb") as f:
                        f.write(response.content)
                    
                    # Store the processed file in session state
                    st.session_state['output_ready'] = True
                    st.session_state['output_file_path'] = output_file_path

                    st.sidebar.success("Processing complete! File is ready.")
                    if st.session_state.get('output_ready'):
                        placeholder_gifload.empty()
                else:
                    error_message = response.json().get("error", "Unknown error occurred.")
                    st.sidebar.error(f"Backend error: {error_message}")

            except Exception as e:
                st.sidebar.error(f"An error occurred: {str(e)}")
        else:
            st.sidebar.warning("Please upload a file and select a language.")

# Main Display for Processed File
if st.session_state.get('output_ready'):
    placeholder.empty()
    
    st.write("### Processed File:")
    # Show the processed file
    output_file_path = st.session_state['output_file_path']
    
    
    if output_file_path.endswith(".mp4"):
        st.video(output_file_path)
    else:
        st.audio(output_file_path)

    # Download button for the processed file
    with open(output_file_path, "rb") as f:
        st.download_button(
            label="Download Translated File",
            data=f,
            file_name="translated_video.mp4",
            mime="video/mp4" if output_file_path.endswith(".mp4") else "audio/wav"
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