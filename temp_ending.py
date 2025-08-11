    # === ADDITIONAL NOTES ===
    if prediction.get('notes'):
        st.markdown("## 📝 **Additional Analysis Notes**")
        with st.expander("View Detailed Analysis Notes", expanded=False):
            st.info(prediction['notes'])

else:
    st.error("Please make a prediction to see mature buck hunting analysis.")
