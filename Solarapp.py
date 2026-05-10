import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io
import json

# Configuration
API_KEY = "AIzaSyA-mPQ8TUx9vr3-BwJRPbbicxOPZmGMp7w"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Solar Bill Automator", page_icon="☀️")

st.title("☀️ MSEDCL Solar Load Automator")
st.markdown("Upload a bill image to automatically generate your Solar Calculation Excel.")

uploaded_file = st.file_uploader("Choose an MSEDCL Bill (Image/PDF)...", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Bill", width=400)
    
    if st.button("🚀 Process Bill & Generate Excel"):
        with st.spinner("AI is reading the bill..."):
            # The prompt is designed to match your specific Excel template fields
            prompt = """
            Look at this MSEDCL electricity bill and extract the following details in JSON format:
            {
                "consumer_name": "Full name of the consumer",
                "consumer_no": "12 digit number",
                "sanctioned_load": "value in kW",
                "fixed_charges": "value",
                "connection_type": "e.g. 1-Phase or 3-Phase",
                "current_month_units": "Units consumed this month",
                "month_year": "Billing month and year"
            }
            Ensure the consumer name matches the bill exactly.
            """
            
            response = model.generate_content([prompt, image])
            
            try:
                # Clean the response to get pure JSON
                json_data = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(json_data)
                
                st.success("Data Extracted Successfully!")
                
                # Display extracted data for confirmation
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {data['consumer_name']}")
                    st.write(f"**Consumer No:** {data['consumer_no']}")
                with col2:
                    st.write(f"**Units:** {data['current_month_units']}")
                    st.write(f"**Load:** {data['sanctioned_load']}")

                # --- Create the Excel File ---
                output = io.BytesIO()
                
                # Logic to mimic your Solar Excel Template
                excel_data = {
                    "Field": ["Consumer Name", "Consumer No", "Fixed Charges", "Sanct. Load (kW)", "Connection Type", "Month Units"],
                    "Value": [
                        data['consumer_name'], 
                        data['consumer_no'], 
                        data['fixed_charges'], 
                        data['sanctioned_load'], 
                        data['connection_type'],
                        data['current_month_units']
                    ]
                }
                
                df = pd.DataFrame(excel_data)
                
                # Mathematical calculation for Solar Size (Example Logic)
                # If units > 300, suggest 3kW, etc.
                units = float(data['current_month_units'])
                suggested_kw = round(units / 100, 2)
                
                summary_df = pd.DataFrame({
                    "Calculation": ["Recommended Solar Capacity", "Estimated Panels (550W)"],
                    "Result": [f"{suggested_kw} kW", round((suggested_kw * 1000) / 550)]
                })

                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Customer_Data', index=False)
                    summary_df.to_excel(writer, sheet_name='Solar_Calculation', index=False)
                
                st.download_button(
                    label="📥 Download Processed Excel File",
                    data=output.getvalue(),
                    file_name=f"Solar_Report_{data['consumer_no']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"Error parsing data: {e}")
                st.write("AI Response was:", response.text)
