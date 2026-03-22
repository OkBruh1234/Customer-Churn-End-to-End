# # import streamlit as st
# # import pandas as pd
# # import joblib

# # # Load model
# # model = joblib.load("churn_model.pkl")

# # st.title("📊 Customer Churn Prediction System")

# # st.write("Provide full customer details for prediction")

# # # ---------------- BASIC INFO ---------------- #

# # gender = st.selectbox("Gender", ["Male", "Female"])

# # senior = st.selectbox("Senior Citizen", [0, 1])

# # partner = st.selectbox("Has Partner?", ["Yes", "No"])

# # dependents = st.selectbox("Has Dependents?", ["Yes", "No"])

# # # ---------------- SERVICES ---------------- #

# # phone = st.selectbox("Phone Service", ["Yes", "No"])

# # multiple_lines = st.selectbox(
# #     "Multiple Lines",
# #     ["Yes", "No", "No phone service"]
# # )

# # internet = st.selectbox(
# #     "Internet Service",
# #     ["DSL", "Fiber optic", "No"]
# # )

# # phone = st.selectbox("Phone Service", ["Yes", "No"])

# # if phone == "No":
# #     multiple_lines = "No phone service"
# #     st.info("No Phone Service → MultipleLines auto-set")

# # else:
# #     multiple_lines = st.selectbox(
# #         "Multiple Lines",
# #         ["Yes", "No"]
# #     )

# # if internet == "No":
# #   online_security = "No internet service"
# #   online_backup = "No internet service" 
# #   device_protection = "No internet service"
# #   tech_support = "No internet service"
# #   streaming_tv = "No internet service"
# #   streaming_movies = "No internet service"
  
# #   st.info("No internet - All internet-related services set to 'No internet service'")
  
# # else:

# #   online_security = st.selectbox(
# #     "Online Security",
# #     ["Yes", "No", "No internet service"]
# #   )

# # online_backup = st.selectbox(
# #     "Online Backup",
# #     ["Yes", "No", "No internet service"]
# # )

# # device_protection = st.selectbox(
# #     "Device Protection",
# #     ["Yes", "No", "No internet service"]
# # )

# # tech_support = st.selectbox(
# #     "Tech Support",
# #     ["Yes", "No", "No internet service"]
# # )

# # streaming_tv = st.selectbox(
# #     "Streaming TV",
# #     ["Yes", "No", "No internet service"]
# # )

# # streaming_movies = st.selectbox(
# #     "Streaming Movies",
# #     ["Yes", "No", "No internet service"]
# # )

# # # ---------------- BILLING ---------------- #

# # contract = st.selectbox(
# #     "Contract Type",
# #     ["Month-to-month", "One year", "Two year"]
# # )

# # paperless = st.selectbox("Paperless Billing", ["Yes", "No"])

# # payment = st.selectbox(
# #     "Payment Method",
# #     [
# #         "Electronic check",
# #         "Mailed check",
# #         "Bank transfer (automatic)",
# #         "Credit card (automatic)"
# #     ]
# # )

# # monthly = st.number_input("Monthly Charges", 0.0, 200.0, 70.0)

# # tenure = st.slider("Tenure (months)", 0, 72, 12)

# # # ---------------- FEATURE ENGINEERING ---------------- #

# # # TotalCharges (important!)
# # total_charges = monthly * tenure

# # # tenure bucket
# # if tenure <= 12:
# #     tenure_bucket = "0-1 year"
# # elif tenure <= 24:
# #     tenure_bucket = "1-2 years"
# # elif tenure <= 48:
# #     tenure_bucket = "2-4 years"
# # else:
# #     tenure_bucket = "4+ years"

# # # service count
# # services = [
# #     online_security,
# #     online_backup,
# #     device_protection,
# #     tech_support,
# #     streaming_tv,
# #     streaming_movies
# # ]

# # service_count = sum([1 for s in services if s == "Yes"])

# # # charges per tenure
# # charges_per_tenure = monthly / (tenure + 1)

# # # ---------------- FINAL INPUT ---------------- #

# # input_df = pd.DataFrame({
# #     "gender": [gender],
# #     "SeniorCitizen": [senior],
# #     "Partner": [partner],
# #     "Dependents": [dependents],
# #     "tenure": [tenure],
# #     "PhoneService": [phone],
# #     "MultipleLines": [multiple_lines],
# #     "InternetService": [internet],
# #     "OnlineSecurity": [online_security],
# #     "OnlineBackup": [online_backup],
# #     "DeviceProtection": [device_protection],
# #     "TechSupport": [tech_support],
# #     "StreamingTV": [streaming_tv],
# #     "StreamingMovies": [streaming_movies],
# #     "Contract": [contract],
# #     "PaperlessBilling": [paperless],
# #     "PaymentMethod": [payment],
# #     "MonthlyCharges": [monthly],
# #     "TotalCharges": [total_charges],
# #     "tenure_bucket": [tenure_bucket],
# #     "service_count": [service_count],
# #     "charges_per_tenure": [charges_per_tenure]
# # })

# # # ---------------- PREDICTION ---------------- #

# # if st.button("Predict Churn"):

# #     prob = model.predict_proba(input_df)[0][1]

# #     st.subheader(f"Churn Probability: {prob:.2f}")

# #     if prob < 0.30:
# #         st.success("🟢 Low Risk")
# #     elif prob < 0.60:
# #         st.warning("🟡 Medium Risk")
# #     else:
# #         st.error("🔴 High Risk")
        
# # st.write("### Prediction Details")
# # st.write(input_df)

# # confidence = abs(prob - 0.5) * 2
# # st.write(f"Model Confidence: {confidence:.2f}")

# # if prob > 0.6:
# #     st.write("⚠️ High risk due to low tenure / contract type / service usage")

# import streamlit as st
# import pandas as pd
# import joblib

# model = joblib.load("churn_model.pkl")

# st.title("📊 Customer Churn Prediction System")

# # ---------------- BASIC INFO ---------------- #

# gender = st.selectbox("Gender", ["Male", "Female"], key="gender")

# senior = st.selectbox("Senior Citizen", [0, 1], key="senior")

# partner = st.selectbox("Partner", ["Yes", "No"], key="partner")

# dependents = st.selectbox("Dependents", ["Yes", "No"], key="dependents")

# # ---------------- PHONE ---------------- #

# phone = st.selectbox("Phone Service", ["Yes", "No"], key="phone")

# if phone == "No":
#     multiple_lines = "No phone service"
#     st.info("No phone service → MultipleLines auto-set")
# else:
#     multiple_lines = st.selectbox(
#         "Multiple Lines",
#         ["Yes", "No"],
#         key="multiple_lines"
#     )

# # ---------------- INTERNET ---------------- #

# internet = st.selectbox(
#     "Internet Service",
#     ["DSL", "Fiber optic", "No"],
#     key="internet"
# )

# if internet == "No":

#     st.info("No internet → all dependent services auto-set")

#     online_security = "No internet service"
#     online_backup = "No internet service"
#     device_protection = "No internet service"
#     tech_support = "No internet service"
#     streaming_tv = "No internet service"
#     streaming_movies = "No internet service"

# else:

#     online_security = st.selectbox(
#         "Online Security",
#         ["Yes", "No"],
#         key="online_security"
#     )

#     online_backup = st.selectbox(
#         "Online Backup",
#         ["Yes", "No"],
#         key="online_backup"
#     )

#     device_protection = st.selectbox(
#         "Device Protection",
#         ["Yes", "No"],
#         key="device_protection"
#     )

#     tech_support = st.selectbox(
#         "Tech Support",
#         ["Yes", "No"],
#         key="tech_support"
#     )

#     streaming_tv = st.selectbox(
#         "Streaming TV",
#         ["Yes", "No"],
#         key="streaming_tv"
#     )

#     streaming_movies = st.selectbox(
#         "Streaming Movies",
#         ["Yes", "No"],
#         key="streaming_movies"
#     )

# # ---------------- BILLING ---------------- #

# contract = st.selectbox(
#     "Contract",
#     ["Month-to-month", "One year", "Two year"],
#     key="contract"
# )

# paperless = st.selectbox(
#     "Paperless Billing",
#     ["Yes", "No"],
#     key="paperless"
# )

# payment = st.selectbox(
#     "Payment Method",
#     [
#         "Electronic check",
#         "Mailed check",
#         "Bank transfer (automatic)",
#         "Credit card (automatic)"
#     ],
#     key="payment"
# )

# monthly = st.number_input(
#     "Monthly Charges",
#     0.0, 200.0, 70.0,
#     key="monthly"
# )

# tenure = st.slider(
#     "Tenure (months)",
#     0, 72, 12,
#     key="tenure"
# )

# # ---------------- FEATURE ENGINEERING ---------------- #

# total_charges = monthly * tenure

# if tenure <= 12:
#     tenure_bucket = "0-1 year"
# elif tenure <= 24:
#     tenure_bucket = "1-2 years"
# elif tenure <= 48:
#     tenure_bucket = "2-4 years"
# else:
#     tenure_bucket = "4+ years"

# services = [
#     online_security,
#     online_backup,
#     device_protection,
#     tech_support,
#     streaming_tv,
#     streaming_movies
# ]

# service_count = sum([1 for s in services if s == "Yes"])

# charges_per_tenure = monthly / (tenure + 1)

# # ---------------- INPUT DF ---------------- #

# input_df = pd.DataFrame({
#     "gender": [gender],
#     "SeniorCitizen": [senior],
#     "Partner": [partner],
#     "Dependents": [dependents],
#     "tenure": [tenure],
#     "PhoneService": [phone],
#     "MultipleLines": [multiple_lines],
#     "InternetService": [internet],
#     "OnlineSecurity": [online_security],
#     "OnlineBackup": [online_backup],
#     "DeviceProtection": [device_protection],
#     "TechSupport": [tech_support],
#     "StreamingTV": [streaming_tv],
#     "StreamingMovies": [streaming_movies],
#     "Contract": [contract],
#     "PaperlessBilling": [paperless],
#     "PaymentMethod": [payment],
#     "MonthlyCharges": [monthly],
#     "TotalCharges": [total_charges],
#     "tenure_bucket": [tenure_bucket],
#     "service_count": [service_count],
#     "charges_per_tenure": [charges_per_tenure]
# })

# # load feature names once
# feature_names = input_df.columns

# # ---------------- PREDICTION ---------------- #

# if st.button("Predict Churn"):

#     prob = model.predict_proba(input_df)[0][1]

#     st.subheader(f"Churn Probability: {prob:.2f}")

#     confidence = abs(prob - 0.5) * 2
#     st.write(f"Model Confidence: {confidence:.2f}")

#     if prob < 0.30:
#         st.success("🟢 Low Risk")
#     elif prob < 0.60:
#         st.warning("🟡 Medium Risk")
#     else:
#         st.error("🔴 High Risk")

#     st.write("### Input Summary")
#     st.write(input_df)

#     # ---------------- SIMPLE EXPLANATION ---------------- #

#     st.write("### 🔍 Why this prediction?")

#     important_factors = []

#     if tenure < 12:
#         important_factors.append("Low tenure → higher churn risk")

#     if contract == "Month-to-month":
#         important_factors.append("Month-to-month contract → high churn risk")

#     if internet == "Fiber optic":
#         important_factors.append("Fiber internet → historically higher churn")

#     if tech_support == "No":
#         important_factors.append("No tech support → higher churn")

#     if monthly > 80:
#         important_factors.append("High monthly charges → higher churn")

#     if len(important_factors) == 0:
#         st.write("No strong churn signals detected")

#     else:
#         for factor in important_factors:
#             st.write("•", factor)
            
    

#     st.write("### Input Summary")
#     st.write(input_df)

import streamlit as st
import pandas as pd
import joblib

model = joblib.load("churn_model.pkl")

st.title("📊 Customer Churn Prediction System")

# ---------------- BASIC ---------------- #
gender = st.selectbox("Gender", ["Male", "Female"], key="gender")
senior = st.selectbox("Senior Citizen", [0, 1], key="senior")
partner = st.selectbox("Partner", ["Yes", "No"], key="partner")
dependents = st.selectbox("Dependents", ["Yes", "No"], key="dependents")

# ---------------- PHONE ---------------- #
phone = st.selectbox("Phone Service", ["Yes", "No"], key="phone")

if phone == "No":
    multiple_lines = "No phone service"
    st.info("No phone → MultipleLines auto-set")
else:
    multiple_lines = st.selectbox("Multiple Lines", ["Yes", "No"], key="multiple_lines")

# ---------------- INTERNET ---------------- #
internet = st.selectbox("Internet Service", ["DSL", "Fiber optic", "No"], key="internet")

if internet == "No":
    st.info("No internet → all dependent services auto-set")

    online_security = "No internet service"
    online_backup = "No internet service"
    device_protection = "No internet service"
    tech_support = "No internet service"
    streaming_tv = "No internet service"
    streaming_movies = "No internet service"

else:
    online_security = st.selectbox("Online Security", ["Yes", "No"], key="os")
    online_backup = st.selectbox("Online Backup", ["Yes", "No"], key="ob")
    device_protection = st.selectbox("Device Protection", ["Yes", "No"], key="dp")
    tech_support = st.selectbox("Tech Support", ["Yes", "No"], key="ts")
    streaming_tv = st.selectbox("Streaming TV", ["Yes", "No"], key="stv")
    streaming_movies = st.selectbox("Streaming Movies", ["Yes", "No"], key="sm")

# ---------------- BILLING ---------------- #
contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"], key="contract")
paperless = st.selectbox("Paperless Billing", ["Yes", "No"], key="paperless")
payment = st.selectbox(
    "Payment Method",
    ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
    key="payment"
)

monthly = st.number_input("Monthly Charges", 0.0, 200.0, 70.0, key="monthly")
tenure = st.slider("Tenure (months)", 0, 72, 12, key="tenure")

# ---------------- FEATURE ENGINEERING ---------------- #
total_charges = monthly * tenure

if tenure <= 12:
    tenure_bucket = "0-1 year"
elif tenure <= 24:
    tenure_bucket = "1-2 years"
elif tenure <= 48:
    tenure_bucket = "2-4 years"
else:
    tenure_bucket = "4+ years"

services = [online_security, online_backup, device_protection, tech_support, streaming_tv, streaming_movies]
service_count = sum([1 for s in services if s == "Yes"])

charges_per_tenure = monthly / (tenure + 1)

# ---------------- INPUT ---------------- #
input_df = pd.DataFrame({
    "gender": [gender],
    "SeniorCitizen": [senior],
    "Partner": [partner],
    "Dependents": [dependents],
    "tenure": [tenure],
    "PhoneService": [phone],
    "MultipleLines": [multiple_lines],
    "InternetService": [internet],
    "OnlineSecurity": [online_security],
    "OnlineBackup": [online_backup],
    "DeviceProtection": [device_protection],
    "TechSupport": [tech_support],
    "StreamingTV": [streaming_tv],
    "StreamingMovies": [streaming_movies],
    "Contract": [contract],
    "PaperlessBilling": [paperless],
    "PaymentMethod": [payment],
    "MonthlyCharges": [monthly],
    "TotalCharges": [total_charges],
    "tenure_bucket": [tenure_bucket],
    "service_count": [service_count],
    "charges_per_tenure": [charges_per_tenure]
})

# ---------------- PREDICTION ---------------- #
if st.button("Predict Churn"):

    prob = model.predict_proba(input_df)[0][1]

    st.subheader(f"Churn Probability: {prob:.2f}")
    st.progress(prob)

    confidence = abs(prob - 0.5) * 2
    st.write(f"Model Confidence: {confidence:.2f}")

    if prob < 0.30:
        st.success("🟢 Low Risk")
    elif prob < 0.60:
        st.warning("🟡 Medium Risk")
    else:
        st.error("🔴 High Risk")
        st.write("👉 Recommend retention strategy (discount / engagement)")

    st.write("### 🔍 Why this prediction?")
    reasons = []

    if tenure < 12:
        reasons.append("Low tenure")
    if contract == "Month-to-month":
        reasons.append("Flexible contract")
    if internet == "Fiber optic":
        reasons.append("Fiber users churn more")
    if tech_support == "No":
        reasons.append("No tech support")
    if monthly > 80:
        reasons.append("High monthly charges")

    if reasons:
        for r in reasons:
            st.write("•", r)
    else:
        st.write("No strong churn signals")

    st.write("### Input Data")
    st.write(input_df)