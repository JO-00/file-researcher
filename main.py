import streamlit as st
from file_loader import load_file
from query_handlers import summarizer, broad_qa, specific_qa, extract_people, extract_dates, external_search
from models import models  

st.set_page_config(page_title="file-researcher", layout="wide")

if 'full_text' not in st.session_state:
    st.session_state.full_text = None
if 'people_list' not in st.session_state:
    st.session_state.people_list = []
if 'doc_context' not in st.session_state:
    st.session_state.doc_context = ""

with st.sidebar:
    st.title("📁 File Control")
    uploaded = st.file_uploader("Upload doc", type=['pdf', 'docx', 'txt'])
    
    if uploaded and st.button("Load"):
        with st.spinner("Processing..."):
            text = load_file(uploaded)
            st.session_state.full_text = text
            
            try:
                st.session_state.doc_context = summarizer.get_document_domain(text)
            except:
                st.session_state.doc_context = "General"
                
        st.success(f"Context: {st.session_state.doc_context}")

    if st.session_state.doc_context:
        st.session_state.doc_context = st.text_input(
            "Current focus (edit to refine):", 
            value=st.session_state.doc_context
        )

if st.session_state.full_text:
    st.header(f"Working on: {st.session_state.doc_context}")

    tab1, tab2 = st.tabs(["Analysis", "Research"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Summarize"):
                st.info(summarizer.summarize_pdf(st.session_state.full_text))

        with col2:
            if st.button("Find People"):
                people = extract_people.extract_people(st.session_state.full_text)
                st.session_state.people_list = people
                st.write(f"Found: {', '.join(people)}")

        with col3:
            if st.button("Timeline"):
                dates = extract_dates.extract_dates_with_context(st.session_state.full_text)
                for d in dates:
                    st.write(f"**{d['date']}**: {d['context']}")

        st.divider()
        query = st.text_input("Ask anything about the file:")
        if query:
            is_broad = any(x in query.lower() for x in ['who', 'what is', 'describe', 'tell'])
            
            if is_broad:
                with st.spinner("Reading..."):
                    st.write(broad_qa.answer_broad(query, st.session_state.full_text))
            else:
                with st.spinner("Searching..."):
                    ans, conf = specific_qa.answer_specific(query, st.session_state.full_text)
                    st.write(f"{ans} (Confidence: {conf:.1%})")

    with tab2:
        if st.session_state.people_list:
            person = st.selectbox("Pick someone to research:", st.session_state.people_list)
            if st.button("Run Web Research"):
                with st.spinner(f"Sifting through results for {person}..."):
                    results = external_search.search_and_summarize_entity(
                        person, 
                        context=st.session_state.doc_context
                    )
                st.markdown(results)
        else:
            st.warning("Extract people in the Analysis tab first.")