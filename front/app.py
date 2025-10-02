import streamlit as st
import os
import shutil
import json
from PIL import Image
import requests
from io import BytesIO

# --- Configuration ---
def get_api_base_url():
    """Fetches the API base URL from environment variables or Streamlit secrets."""
    # 1. Check for Docker/CI environment variable
    env_url = os.environ.get("API_BASE_URL")
    if env_url:
        return env_url
    # 2. Check for Streamlit secrets (for deployment)
    try:
        api_url = st.secrets.get("API_BASE_URL")
        if api_url:
            return api_url
    except Exception:
        pass
    # 3. Fallback for local development
    return "http://127.0.0.1:8000"

API_BASE = get_api_base_url()
TEMP_DIR = "temp_uploads"

# --- Session State Initialization ---
def initialize_session_state():
    """Initializes session state variables."""
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = {}
    if "total_session_files" not in st.session_state:
        st.session_state.total_session_files = 0
    if "total_processed_count" not in st.session_state:
        st.session_state.total_processed_count = 0

# --- UI Layout and Logic ---
st.title("📄 Document OCR and Transcription Service")

# Create a temporary directory for uploads
os.makedirs(TEMP_DIR, exist_ok=True)
initialize_session_state()

# --- File Input Methods ---
files_to_process = []
input_method = st.radio(
    "Choose input method:",
    ("Upload Files", "Process Local Directory"),
    horizontal=True
)

if input_method == "Upload Files":
    uploaded_files = st.file_uploader(
        "Upload JPG, JPEG, or PDF files",
        type=["jpg", "jpeg", "pdf"],
        accept_multiple_files=True
    )
    if uploaded_files:
        for uf in uploaded_files:
            path = os.path.join(TEMP_DIR, uf.name)
            with open(path, "wb") as f:
                f.write(uf.getvalue())
            files_to_process.append({"name": uf.name, "path": path, "upload_obj": uf})

elif input_method == "Process Local Directory":
    dir_path = st.text_input("Enter the full path to a local directory:")
    if dir_path and os.path.isdir(dir_path):
        st.write(f"Scanning directory: {dir_path}")
        for f_name in os.listdir(dir_path):
            if f_name.lower().endswith((".jpg", ".jpeg", ".pdf")):
                files_to_process.append({
                    "name": f_name,
                    "path": os.path.join(dir_path, f_name),
                    "upload_obj": None
                })
    elif dir_path:
        st.error("The provided path is not a valid directory.")

# --- Processing Logic ---
if files_to_process:
    st.write(f"Found {len(files_to_process)} files to process.")
    st.session_state.total_session_files = len(files_to_process)

    if st.button("✨ Start Processing", type="primary"):
        progress_bar = st.progress(0)
        st.session_state.processed_files = {} # Reset state on new run
        
        for i, file_info in enumerate(files_to_process):
            file_name = file_info["name"]
            file_path = file_info["path"]
            
            try:
                # --- Step 1: Upload the file ---
                with open(file_path, "rb") as f:
                    files_payload = {"file": (file_name, f, "application/octet-stream")}
                    upload_response = requests.post(f"{API_BASE}/files/upload", files=files_payload)

                if upload_response.status_code == 200:
                    upload_data = upload_response.json()
                    file_id = upload_data.get("file_id")
                    st.info(f"'{file_name}' uploaded successfully. File ID: {file_id}")

                    # --- Step 2: Transcribe the file ---
                    transcribe_url = f"{API_BASE}/files/{file_id}/transcribe"
                    transcribe_response = requests.post(transcribe_url)
                    
                    if transcribe_response.status_code == 200:
                        transcribe_data = transcribe_response.json()
                        extracted_text = transcribe_data.get("text", "")
                        transcript_id = transcribe_data.get("transcript_id")
                        
                        # Store results in session state
                        st.session_state.processed_files[file_name] = {
                            "text": extracted_text,
                            "path": file_path,
                            "file_id": file_id,
                            "transcript_id": transcript_id,
                        }
                        st.success(f"'{file_name}' transcribed successfully.")
                    else:
                        st.error(f"Error transcribing '{file_name}': {transcribe_response.status_code} - {transcribe_response.text}")
                else:
                    st.error(f"Error uploading '{file_name}': {upload_response.status_code} - {upload_response.text}")

            except Exception as e:
                st.error(f"An unexpected error occurred with '{file_name}': {e}")
            
            progress_bar.progress((i + 1) / len(files_to_process))

        st.session_state.total_processed_count = len(st.session_state.processed_files)
        st.balloons()
        st.subheader("🎉 Processing Complete!")
        st.write(f"Files in session: {st.session_state.total_session_files}")
        st.write(f"Successfully processed: {st.session_state.total_processed_count}")

# --- Display and Edit Results ---
if st.session_state.processed_files:
    st.header("📝 Review and Edit Transcripts")
    for name, data in st.session_state.processed_files.items():
        with st.expander(f"**{name}** (File ID: {data['file_id']}, Transcript ID: {data['transcript_id']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    # Display PDF as an info box, image as an image
                    if data["path"].lower().endswith('.pdf'):
                        st.info("PDF preview is not available.")
                    else:
                        img = Image.open(data["path"])
                        st.image(img, caption="Image Preview", use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not display preview for {name}. Error: {e}")

            with col2:
                edited_text = st.text_area(
                    "Extracted Text",
                    value=data["text"],
                    height=300,
                    key=f"text_{name}"
                )
                
                if edited_text != data["text"]:
                    st.session_state.processed_files[name]["text"] = edited_text
                    st.info("Changes are saved in the session. Re-run export to get updated data.")

                # NOTE: The "Save Changes" button has been removed because the backend in `main.py`
                # does not include an endpoint to PUT/update a transcript after it has been created.
                # This functionality would need to be added to the backend API first.

# --- Export Functionality ---
if st.session_state.processed_files:
    st.header("💾 Export Data")
    
    export_format = st.selectbox("Select export format:", ("JSON", "CSV", "TXT"))

    if st.button("Download Export"):
        export_data_list = []
        for name, data in st.session_state.processed_files.items():
            export_data_list.append({
                "filename": name,
                "file_id": data["file_id"],
                "transcript_id": data["transcript_id"],
                "text": data["text"]
            })

        if export_format == "JSON":
            export_str = json.dumps(export_data_list, ensure_ascii=False, indent=4)
            mime = "application/json"
            file_ext = ".json"
        elif export_format == "CSV":
            # Simple CSV: filename, text
            csv_lines = ['"filename","text"']
            for item in export_data_list:
                # Basic CSV escaping for double quotes
                text_escaped = item['text'].replace('"', '""')
                csv_lines.append(f'"{item["filename"]}","{text_escaped}"')
            export_str = "\n".join(csv_lines)
            mime = "text/csv"
            file_ext = ".csv"
        else: # TXT
            txt_lines = []
            for item in export_data_list:
                txt_lines.append(f"--- File: {item['filename']} ---\n{item['text']}\n")
            export_str = "\n".join(txt_lines)
            mime = "text/plain"
            file_ext = ".txt"

        st.download_button(
            label="Download Data",
            data=export_str,
            file_name=f"archive_export{file_ext}",
            mime=mime,
        )

# --- Cleanup ---
if st.button("🧹 Clear Session and Files"):
    try:
        shutil.rmtree(TEMP_DIR)
    except Exception as e:
        st.error(f"Could not delete temp directory: {e}")
    st.session_state.clear()
    st.success("Session cleared. Please refresh the page.")
    st.rerun()

