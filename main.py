# streamlit_app.py
"""
Main Streamlit application file. This file builds the user interface
and orchestrates the calls to the other modules.
"""
import os
import threading
from queue import Queue

import streamlit as st

from config import CORPUS_FOLDER, MISTRAL_API_KEY, MISTRAL_API_URL, state_corpus_files
from data_processing import generate_report, generate_visualization
from llm_services import call_mistral_saba
from map_generator import generate_comparative_maps, generate_map
from utils import extract_metrics_from_query, extract_states_from_query, extract_year

# --- Streamlit UI Configuration ---
st.set_page_config(page_title="Environmental Data Explorer", layout="wide")

def get_theme_css(theme):
    if theme == "Dark":
        return """
            <style>
                body, .stApp { background-color: #1e1e1e; color: #ffffff; }
                .chat-container { min-height: 50px; max-height: 60vh; overflow-y: auto; padding: 15px; border: 1px solid #444; border-radius: 8px; background-color: #2b2b2b; margin-bottom: 20px; }
                .user-msg { padding: 10px; border-radius: 5px; margin: 5px 0; text-align: right; max-width: 80%; margin-left: auto; color: #4a704a; }
                .bot-msg { padding: 10px; margin: 5px 0; text-align: left; max-width: 80%; color: #ffffff; }
                .stChatInput { position: fixed; bottom: 20px; width: 95%; background-color: #333; z-index: 1000; padding: 10px; color: #ffffff; border: 1px solid #444; }
                footer {visibility: hidden;}
                .sidebar .sidebar-content { background-color: #2b2b2b; color: #ffffff; }
                .stButton>button { background-color: #444; color: #ffffff; border: 1px solid #666; border-radius: 5px; }
                .stButton>button:hover { background-color: #555; }
                .stSelectbox { background-color: #333; color: #ffffff; }
                .graph-container { padding: 10px; border-radius: 8px; background-color: #2b2b2b; margin: 5px; }
            </style>
        """
    else:
        return """
            <style>
                body, .stApp { background-color: #ffffff; color: #000000; }
                .user-msg { padding: 10px; border-radius: 5px; margin: 5px 0; text-align: right; max-width: 80%; margin-left: auto; color: #2e6b2e; }
                .bot-msg { padding: 10px; margin: 5px 0; text-align: left; max-width: 80%; color: #000000; }
                footer {visibility: hidden;}
                .sidebar .sidebar-content { background-color: #f0f0f0; color: #000000; }
                .stButton>button { background-color: #e0e0e0; color: #000000; border: 1px solid #ccc; border-radius: 5px; }
                .stButton>button:hover { background-color: #d0d0d0; }
                .stSelectbox { background-color: #ffffff; color: #000000; }
                .graph-container { padding: 10px; border-radius: 8px; background-color: #f9f9f9; margin: 5px; }
            </style>
        """

def main():
    # --- Session State Initialization ---
    if "chats" not in st.session_state: st.session_state.chats = {}
    if "current_chat" not in st.session_state: st.session_state.current_chat = None
    if "theme" not in st.session_state: st.session_state.theme = "White"
    if "processing_stage" not in st.session_state: st.session_state.processing_stage = None
    if "partial_response" not in st.session_state: st.session_state.partial_response = None

    # --- Sidebar UI ---
    with st.sidebar:
        st.markdown("### Chat History")
        if st.session_state.chats:
            for chat_name in st.session_state.chats.keys():
                if st.button(chat_name, key=chat_name, use_container_width=True):
                    st.session_state.current_chat = chat_name
                    st.session_state.processing_stage = None
                    st.session_state.partial_response = None
                    st.rerun()
        st.markdown("---")
        if st.button("New Chat", key="new_chat", use_container_width=True):
            st.session_state.current_chat = None
            st.session_state.processing_stage = None
            st.session_state.partial_response = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Theme")
        theme = st.selectbox("Select Theme", ["White", "Dark"],
                             index=0 if st.session_state.theme == "White" else 1,
                             label_visibility="collapsed")
        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.rerun()

    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)
    st.title("🌍 Environmental Data Explorer")
    st.subheader("Analyze environmental metrics with graphs")

    messages = st.session_state.chats.get(st.session_state.current_chat, 
                                          [{"role": "user", "content": "Ask about environmental data (e.g., 'Land cover for Kerala 2023')"}])

    # --- Chat History Display ---
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for msg in messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        else: # Assistant
            if "report" in msg and msg["report"]:
                st.markdown("### Environmental Report")
                st.markdown(f'<div class="bot-msg">{msg["report"]}</div>', unsafe_allow_html=True)
            if "visualizations" in msg and msg["visualizations"]:
                st.markdown("### Visualizations")
                for i in range(0, len(msg["visualizations"]), 2):
                    graphs_to_show = msg["visualizations"][i:i+2]
                    cols = st.columns(len(graphs_to_show))
                    for idx, fig in enumerate(graphs_to_show):
                        with cols[idx]:
                            st.plotly_chart(fig, use_container_width=True)
            if "map" in msg and msg["map"]:
                st.markdown("### GEE Map")
                with st.spinner("Loading GEE Map..."):
                    msg["map"].to_streamlit(height=400)
                if "map_captions" in msg and msg["map_captions"]:
                    for caption in set(msg["map_captions"]):
                        st.caption(caption)
            if "comparative_maps" in msg and msg["comparative_maps"]:
                st.markdown("### Comparative GEE Maps Across Years")
                maps_by_state = {}
                for m in msg["comparative_maps"]:
                    if m['state'] not in maps_by_state: maps_by_state[m['state']] = []
                    maps_by_state[m['state']].append(m)
                for state, state_maps in maps_by_state.items():
                    if len(state_maps) > 1:
                        st.markdown(f"#### {state}")
                        tabs = st.tabs([f"{m['year']}" for m in state_maps])
                        for tab, map_data in zip(tabs, state_maps):
                            with tab:
                                with st.spinner(f"Loading map for {state} {map_data['year']}..."):
                                    map_data["map"].to_streamlit(height=400)
            if "error" in msg:
                st.error(msg["error"])
    st.markdown("</div>", unsafe_allow_html=True)

    # --- User Input and Orchestration ---
    if query := st.chat_input("Type your query here (e.g., 'Land cover for Kerala 2023')"):
        if st.session_state.current_chat is None:
            chat_name = query[:50]
            if chat_name in st.session_state.chats: chat_name += f"_{len(st.session_state.chats)}"
            st.session_state.chats[chat_name] = []
            st.session_state.current_chat = chat_name

        messages = st.session_state.chats[st.session_state.current_chat]
        messages.append({"role": "user", "content": query})
        
        detected_states = extract_states_from_query(query)
        if not detected_states:
            messages.append({"role": "assistant", "error": "Please include a state name."})
            st.rerun()

        year_dict = extract_year(query)
        requested_metrics = extract_metrics_from_query(query)
        
        with st.spinner("Generating report..."):
            checkout_corpus_data = ""
            for state in detected_states:
                corpus_file_path = os.path.join(CORPUS_FOLDER, state_corpus_files.get(state, ''))
                if os.path.exists(corpus_file_path):
                    with open(corpus_file_path, "r", encoding="utf-8") as f:
                        checkout_corpus_data += f"\n--- {state} ---\n" + f.read()
                else:
                    messages.append({"role": "assistant", "error": f"No data file for {state}."})
                    st.rerun()

            mistral_values = call_mistral_saba(MISTRAL_API_URL, MISTRAL_API_KEY, checkout_corpus_data, query, detected_states, requested_metrics)
            print(f"Mistral Values: {mistral_values}")

            if "API Error" in mistral_values:
                messages.append({"role": "assistant", "error": mistral_values})
            else:
                report = generate_report(query, detected_states, year_dict, checkout_corpus_data, mistral_values)
                messages.append({"role": "assistant", "report": report})
                st.session_state.processing_stage = "visualizations"
                st.session_state.partial_response = {
                    "mistral_values": mistral_values, "detected_states": detected_states,
                    "year_dict": year_dict, "query": query, "requested_metrics": requested_metrics
                }
        st.rerun()

    if st.session_state.processing_stage == "visualizations" and st.session_state.partial_response:
        with st.spinner("Generating visualizations..."):
            pr = st.session_state.partial_response
            viz_figs = generate_visualization(pr["mistral_values"], pr["detected_states"], pr["year_dict"], pr["query"], pr["requested_metrics"])
            
            response = st.session_state.chats[st.session_state.current_chat][-1]
            if viz_figs:
                response["visualizations"] = viz_figs
            else:
                response["error"] = "No visualizations generated. Check data and logs."
            
            st.session_state.processing_stage = "maps"
            st.rerun()

    if st.session_state.processing_stage == "maps" and st.session_state.partial_response:
        with st.spinner("Generating maps..."):
            pr = st.session_state.partial_response
            map_result_queue = Queue()
            
            has_multiple_years = any(len(pr["year_dict"].get(state, [])) > 1 for state in pr["detected_states"])
            
            threads = []
            if has_multiple_years:
                thread = threading.Thread(target=generate_comparative_maps, args=(pr["detected_states"], pr["year_dict"], pr["query"], pr["requested_metrics"], map_result_queue))
            else:
                thread = threading.Thread(target=generate_map, args=(pr["detected_states"], pr["year_dict"], pr["query"], map_result_queue))
            
            threads.append(thread)
            thread.start()
            for t in threads:
                t.join()

            map_data, map_error, map_captions = map_result_queue.get()
            
            response = st.session_state.chats[st.session_state.current_chat][-1]
            if map_error:
                response["error"] = response.get("error", "") + f"\nMap Error: {map_error}"
            elif map_data:
                if has_multiple_years:
                    response["comparative_maps"] = map_data
                else:
                    response["map"] = map_data
                    response["map_captions"] = map_captions

            st.session_state.processing_stage = None
            st.session_state.partial_response = None
            st.rerun()

if __name__ == "__main__":
    main()
