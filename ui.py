import streamlit as st
import requests
from database import Session, LegalSection

BASE_API_URL = "http://localhost:8000"  # Or your API endpoint

def highlight_text(text, query):
    """Highlight search terms in the results"""
    if not query:
        return text
    return text.replace(query, f"**{query}**")

def search_sections():
    st.title("IPC to BNS Mapping Tool")
    
    # Search functionality with improved layout
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Search legal sections", key="search_input")
    with col2:
        code_type = st.selectbox("Code", ["All", "IPC", "BNS"], index=0)
    
    if search_query:
        st.subheader("Search Results")
        
        # Build API query parameters
        params = {"q": search_query}
        if code_type != "All":
            params["code_type"] = code_type
        
        try:
            results = requests.get(
                f"{BASE_API_URL}/search",
                params=params
            ).json()
            
            if not results:
                st.warning("No matching sections found")
                return
            
            # Group results by section
            grouped_results = {}
            for result in results:
                if result['section_number'] not in grouped_results:
                    grouped_results[result['section_number']] = []
                grouped_results[result['section_number']].append(result)
            
            # Display grouped results
            for section_num, records in grouped_results.items():
                with st.expander(f"{records[0]['code_type']} Section {section_num}: {records[0]['section_title']}"):
                    for record in records:
                        # Highlight search terms in the text
                        highlighted_text = highlight_text(record['full_text'], search_query)
                        st.markdown(f"**Full Text:** {highlighted_text}")
                        
                        # Show mappings if available
                        if record['code_type'] == 'IPC':
                            mappings = requests.get(
                                f"{BASE_API_URL}/mappings/{section_num}"
                            ).json()
                            if mappings:
                                st.markdown("**BNS Mappings:**")
                                for mapping in mappings:
                                    st.write(f"- BNS {mapping['bns_section']['section_number']}: {mapping['bns_section']['section_title']} (Confidence: {mapping['confidence']}%)")
                        st.write("---")
                        
        except Exception as e:
            st.error(f"Search failed: {str(e)}")

if __name__ == "__main__":
    search_sections()