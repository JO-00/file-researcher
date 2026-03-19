import streamlit as st
from file_loader import load_file
from query_handlers import broad_qa, specific_qa, extract_people, extract_dates, external_search
from models import models
from query_handlers.summarizer import summarizer_factory
import time

st.set_page_config(page_title="file-researcher", layout="wide")


# soon only the admin panel will be able to do this
with st.sidebar:
    st.title("⚙️ Performance Settings")
    use_async = st.checkbox("Use async processing", value=False, 
                           help="Async can be faster but uses more memory")
    thread_count = st.number_input("Thread count", min_value=1, max_value=8, value=1,
                                   help="More threads = faster but more memory (async only)")
    
    st.divider()
    st.title("📊 Analysis Detail")
    
    # Slider for number of chunks
    chunk_count = st.slider(
        "Number of text chunks:", 
        min_value=4, 
        max_value=50, 
        value=12,
        step=1,
        help="More chunks = more detailed but slower analysis"
    )
    
    st.info("High Analysis Depth for Small Documents gives bad output")
    if 4 <= chunk_count <= 10:
        st.info("⚡ **Quick Analysis** - Fast processing, good for getting the main ideas")
    elif 11 <= chunk_count <= 20:
        st.success("📊 **Moderate Analysis** - Balanced between speed and detail")
    elif 21 <= chunk_count <= 30:
        st.warning("🔍 **Detailed Analysis** - More thorough, will take some time")
    elif 31 <= chunk_count <= 50:
        st.error("⚠️ **Analysis in Great Detail** - This might take long! Consider reducing chunk count for faster results")
    
    # Confirm button
    confirm_chunks = st.button("✅ Confirm Chunk Count", use_container_width=True)
    
    if confirm_chunks:
        st.session_state.chunk_count = chunk_count
        st.success(f"Chunk count set to {chunk_count}")
    
    # Use session state value if confirmed, otherwise use slider value
    active_chunk_count = st.session_state.get('chunk_count', chunk_count)
    
    # Create summarizer with selected settings
    summarizer = summarizer_factory.create_summarizer(
        async_mode=use_async, 
        thread_count=thread_count,
        NUMBER_CHUNKS_PER_ARTICLE=active_chunk_count
    )

#no loss of info
if 'full_text' not in st.session_state:
    st.session_state.full_text = None
if 'people_list' not in st.session_state:
    st.session_state.people_list = []
if 'doc_context' not in st.session_state:
    st.session_state.doc_context = ""
if 'root' not in st.session_state:
    st.session_state.root = None
if 'processing_time' not in st.session_state:
    st.session_state.processing_time = None

# ======================
# File control sidebar
# ======================
with st.sidebar:
    st.divider()
    st.title("📁 File Control")
    uploaded = st.file_uploader("Upload doc", type=['pdf', 'docx', 'txt'])
    
    if uploaded and st.button("Load Document"):
        with st.spinner("Processing document..."):
            # Load file
            text = load_file(uploaded)
            st.session_state.full_text = text
            
            # Build tree (with timing)
            print("Building summary tree...")
            t = time.time()
            
            try:
                if use_async:
                    # Async version
                    st.session_state.root = summarizer['createTree'](text)
                else:
                    # Sync version
                    st.session_state.root = summarizer['createTree'](text)

                st.session_state.processing_time = time.time() - t
                print(f"Tree built in {st.session_state.processing_time:.2f} seconds")
                
                # Get document context/domain/topic !
                try:
                    st.session_state.doc_context = summarizer['get_document_domain'](st.session_state.root)
                except Exception as e:
                    print(f"Context extraction error: {e}")
                    st.session_state.doc_context = "General"
                
                st.success(f"✅ Loaded! Context: {st.session_state.doc_context}")
                if st.session_state.processing_time:
                    st.caption(f"Processing time: {st.session_state.processing_time:.2f}s")
                    
            except Exception as e:
                st.error(f"Error processing document: {e}")
                print(f"Error: {e}")

    # Editable context (moved here to keep sidebar organized)
    if st.session_state.doc_context:
        edited_context = st.text_input(
            "Edit document context:", 
            value=st.session_state.doc_context
        )
        if edited_context and edited_context != st.session_state.doc_context:
            st.session_state.doc_context = edited_context
            st.rerun()


if st.session_state.full_text:
    st.header(f"📄 Working on: {st.session_state.doc_context}")
    
    
    if st.session_state.processing_time:
        mode = "async" if use_async else "sync"
        st.caption(f"Mode: {mode} with {thread_count} thread(s) | Tree built in {st.session_state.processing_time:.2f}s")

    tab1, tab2 = st.tabs(["🔍 Analysis", "🌐 Research"])


    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            number_value = st.number_input(
                "Summary detail level (0=root, 1-3=deeper):", 
                min_value=0, max_value=3, value=0,
                help="0: Overall summary, 1-3: More detailed breakdowns"
            )

            if st.button("📝 Generate Summary", use_container_width=True):
                if st.session_state.root:
                    with st.spinner("Generating summary..."):
                        summary = summarizer['summarize_pdf'](st.session_state.root, number_value)
                        st.info(summary)
                else:
                    st.error("Please load a document first")

        with col2:
            if st.button("👥 Find People", use_container_width=True):
                with st.spinner("Extracting names..."):
                    people = extract_people.extract_people(st.session_state.full_text)
                    st.session_state.people_list = people
                    if people:
                        st.success(f"Found {len(people)} people")
                        st.write(f"📋 **Names:** {', '.join(people)}")
                    else:
                        st.warning("No people found in document")

        with col3:
            if st.button("📅 Timeline", use_container_width=True):
                with st.spinner("Extracting dates..."):
                    dates = extract_dates.extract_dates_with_context(st.session_state.full_text)
                    if dates:
                        st.success(f"Found {len(dates)} dates")
                        for d in dates:
                            st.write(f"**{d['date']}**: {d['context']}")
                    else:
                        st.warning("No dates found in document")

        st.divider()
        
        # Q&A section
        st.subheader("❓ Ask Questions")
        query = st.text_input("Ask anything about the file:", placeholder="e.g., What is this document about?")
        
        if query:
            is_broad = any(x in query.lower() for x in ['who', 'what is', 'describe', 'tell', 'summarize'])
            
            if is_broad:
                with st.spinner("📖 Reading and analyzing..."):
                    answer = broad_qa.answer_broad(query, st.session_state.root )
                    st.markdown(f"**Answer:** {answer}")
            else:
                with st.spinner("🔍 Searching for specific answer..."):
                    answer, confidence = specific_qa.answer_specific(query, st.session_state.full_text)
                    st.markdown(f"**Answer:** {answer}")
                    st.caption(f"Confidence: {confidence:.1%}")

   
    with tab2:
        st.subheader("🌐 Web Research")
        
        if st.session_state.people_list:
            col1, col2 = st.columns([3, 1])
            with col1:
                person = st.selectbox("Select a person to research:", st.session_state.people_list)
            with col2:
                st.write("")  # Spacing
                st.write("")  # Spacing
                research_button = st.button("🔍 Research", use_container_width=True)
            
            if research_button:
                with st.spinner(f"Searching the web for information about {person}..."):
                    results = external_search.search_and_summarize_entity(
                        person, 
                        context=st.session_state.doc_context
                    )
                
                st.markdown("### 📊 Research Results")
                st.markdown(results)
                
                # Add option to export
                if st.button("📋 Copy to clipboard"):
                    st.code(results, language="text")
                    st.success("Results ready to copy!")
        else:
            st.info("👆 No people found yet. Go to the Analysis tab and click 'Find People' first.")
            
            # Quick action button
            if st.button("Extract People Now"):
                with st.spinner("Extracting names..."):
                    people = extract_people.extract_people(st.session_state.full_text)
                    st.session_state.people_list = people
                    st.rerun()

else:
    # Welcome screen when no document is loaded
    st.title("📚 File Researcher")
    st.markdown("""
    Welcome to File Researcher! This tool helps you analyze documents using AI.
    
    ### 🚀 Getting Started:
    1. Upload a PDF, DOCX, or TXT file using the sidebar
    2. Wait for the AI to build a summary tree
    3. Explore the Analysis and Research tabs
    
    ### ✨ Features:
    - **Summarization** at different detail levels
    - **Entity extraction** (people, dates, locations)
    - **Q&A** about your documents
    - **Web research** on mentioned people
    
    ### ⚙️ Performance Tips:
    - For small documents (<10 pages), use sync mode with 1 thread
    - For large documents, try async with 2-4 threads
    - Monitor memory usage if using many threads
    """)
    
    # Show sample
    with st.expander("📖 Example"):
        st.markdown("""
        **Upload a document like:**
        - Research papers
        - Business reports
        - News articles
        - Legal documents
        
        The AI will create a hierarchical summary tree, then you can:
        - Get overview summaries
        - Find all mentioned people
        - Extract dates for timelines
        - Ask specific questions
        """)