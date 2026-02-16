import streamlit as st
import os
import shutil
import glob
# Import the PRO backend
from agent_hercules_local import get_agent_with_docs

st.set_page_config(page_title="Hercules", page_icon="🏛️", layout="wide")

st.title("🏛️ Hercules")
st.markdown("### Enterprise Research & Analytics Agent")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Data Center")
    uploaded_files = st.file_uploader(
        "Upload Enterprise Data",
        accept_multiple_files=True,
        type=["pdf", "txt", "csv"]
    )

    if st.button("Initialize System"):
        if uploaded_files:
            with st.spinner("Ingesting Data into Persistent Storage..."):
                # Cleanup temp folder but KEEP hercules_db (persistence)
                temp_dir = "temp_hercules"
                if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
                os.makedirs(temp_dir)

                saved_paths = []
                for file in uploaded_files:
                    path = os.path.join(temp_dir, file.name)
                    with open(path, "wb") as f: f.write(file.getbuffer())
                    saved_paths.append(path)

                # Initialize Agent
                agent, sys_instruct = get_agent_with_docs(saved_paths)
                st.session_state["agent"] = agent
                st.session_state["system_instruction"] = sys_instruct
                st.success("System Online. Database Secured.")
        else:
            st.warning("Please provide data files.")

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hercules Pro Online. I have access to Web Search, Python Analytics, and your Documents."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if user_input := st.chat_input("Enter command..."):
    if "agent" not in st.session_state:
        st.error("⚠️ System Offline. Please upload data and click Initialize.")
        st.stop()

    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                agent = st.session_state["agent"]
                sys_instruct = st.session_state["system_instruction"]
                messages = [("system", sys_instruct)] + [(m["role"], m["content"]) for m in st.session_state.messages]

                config = {"configurable": {"thread_id": "Hercules-Session"}}
                response = agent.invoke({"messages": messages}, config=config)

                # Parse Response
                raw_content = response['messages'][-1].content
                if isinstance(raw_content, list):
                    agent_answer = "".join([block["text"] for block in raw_content if block.get("type") == "text"])
                else:
                    agent_answer = str(raw_content)

                st.markdown(agent_answer)
                st.session_state.messages.append({"role": "assistant", "content": agent_answer})

                # File Downloads
                extensions = [".docx", ".pdf", ".xlsx"]
                for ext in extensions:
                    for f in glob.glob(f"*{ext}"):
                        if f in agent_answer:
                            with open(f, "rb") as file:
                                st.download_button(f"📥 Download {f}", file, file_name=f, mime="application/octet-stream")
            except Exception as e:
                st.error(f"Execution Error: {e}")