import streamlit as st
import requests

BASE_API_URL = "http://localhost:8000"

st.title("IPC to BNS Mapping Tool")

# Search functionality
search_query = st.text_input("Search legal sections")
if search_query:
    results = requests.get(f"{BASE_API_URL}/search?q={search_query}").json()
    for result in results:
        st.write(f"**{result['code_type']} {result['section_number']}**: {result['section_title']}")

# IPC to BNS mapping
st.header("IPC to BNS Section Mapping")
ipc_section = st.text_input("Enter IPC Section (e.g., '302')")
if ipc_section:
    mappings = requests.get(f"{BASE_API_URL}/mappings/{ipc_section}").json()
    if not mappings:
        st.warning("No BNS mappings found for this IPC section")
    else:
        for mapping in mappings:
            st.subheader(f"IPC {mapping['ipc_section']['section_number']} → BNS {mapping['bns_section']['section_number']}")
            st.write(f"**Mapping Type**: {mapping['mapping_type']} (Confidence: {mapping['confidence']}%)")
            st.write(f"**IPC Title**: {mapping['ipc_section']['section_title']}")
            st.write(f"**BNS Title**: {mapping['bns_section']['section_title']}")
            st.write("---")