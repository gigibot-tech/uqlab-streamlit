"""Dataset Statistics Page"""
import streamlit as st
import pandas as pd

def render(api_client):
    st.title("📊 Dataset Statistics")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        dataset = st.selectbox("Dataset", ["cifar10n"])
    with col2:
        noise_type = st.selectbox("Noise Type", ["worse_label", "aggre_label", "random_label1"])
    
    try:
        stats = api_client.get(f"/api/v1/datasets/{dataset}/stats", {"noise_type": noise_type})
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", f"{stats['total_samples']:,}")
        col2.metric("Clean", f"{stats['clean_samples']:,}")
        col3.metric("Noisy", f"{stats['noisy_samples']:,}")
        col4.metric("Noise Rate", f"{stats['noise_rate']*100:.1f}%")
        
        st.subheader("Per-Class Distribution")
        data = []
        for cid, d in stats['noise_per_class'].items():
            data.append({
                "Class": stats['class_names'][int(cid)],
                "Total": d['total'],
                "Clean": d['total'] - d['noisy'],
                "Noisy": d['noisy'],
                "Rate": f"{d['rate']*100:.1f}%"
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Error: {e}")
