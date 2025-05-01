import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# Set the page configuration
st.set_page_config(page_title="Finance App", page_icon=":money_with_wings:", layout="wide")

category_file = "categories.json"

if "Categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": []
    }

if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)


# Function to save categories to a JSON file
# This function will save the categories to a JSON file
def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)


# Function to categorize transactions based on keywords
# This function will categorize transactions based on the keywords provided in the categories dictionary
def categorize_transaction(df):
    # Create a new column for categories
    df["Category"] = "Uncategorized"
    # Loop through the categories and assign them to the transactions
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue
        # Convert keywords to lowercase and strip whitespace 
        lowered_keywords = [keyword.lower().strip() for keyword in keywords]
        # Check if any of the keywords are in the transaction details
        # Assuming the transaction details are in a column named "Details"
        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if details in lowered_keywords:
                df.at[idx, "Category"] = category
                break   # Break after the first match to avoid overwriting

    return df


# Load the transaction file and clean it up
# This function will load the transaction file and clean it up
def load_transaction(file):
    try:
        df = pd.read_csv(file)
        # To clean up file
        df.columns = [col.strip() for col in df.columns] # Remove leading/trailing whitespace from column names
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float) # Remove $ sign and convert to float
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y") # Convert to datetime format
        
      
        return categorize_transaction(df) # Call the categorize function to categorize transactions
        # Check if the file is empty
    except Exception as e:
        st.error(f"Error processing file: {str}")
        return None

# Function to add a keyword to a category
# This function will add a keyword to a category in the categories dictionary
def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    
    return False

# write my main function
# This function will be the main function that will run the app
def main():
    st.title("Finance Dashboard")
# to upload my file i can change the file uploader to accept multiple files through "type" parameter
    uploaded_file = st.file_uploader("Upload your transaction CSV file", type=["csv"])

    if uploaded_file is not None:
        df = load_transaction(uploaded_file)

        if df is not None:
            # optional depending on the type of statement file i have
            debits_df = df[df["Debit/Credit"] == "Debit"].copy()
            credits_df = df[df["Debit/Credit"] == "Credit"].copy()

            st.session_state.debits_df = debits_df.copy()
            st.session_state.credits_df = credits_df.copy()


            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
            with tab1:
                new_category = st.text_input("Add a new category")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()
                
                # Display the existing categories
                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits_df[["Date", "Details", "Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="$%.2f AED"),
                        "Category": st.column_config.SelectboxColumn("Category", options=list(st.session_state.categories.keys()), default="Uncategorized"),
                
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor",
                )

                save_button = st.button("Save Changes", type="primary")
                if save_button:
                    for  idx, row in edited_df.iterrows():
                        # Check if the category has changed
                        new_category = row["Category"]
                        if new_category == st.session_state.debits_df.at[idx, "Category"]:
                            continue
                        # Update the category in the original DataFrame

                        details = row["Details"].lower().strip()
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)
                        # Save the changes to the JSON file
                   
                st.subheader("Expenses Summary")
                # Display the summary of expenses by category
                category_total = st.session_state.debits_df.groupby("Category")["Amount"].sum().reset_index()
                category_total = category_total.sort_values(by="Amount", ascending=False)
                # Display the summary in a table
                st.dataframe(
                    category_total,
                    column_config={
                        "Amount": st.column_config.NumberColumn("Total Amount", format="$%.2f AED"),
                    },
                    use_container_width=True,
                    hide_index=True,
                )
                # Create a pie chart of expenses by category
                fig = px.pie(
                    category_total,
                    values="Amount",
                    names="Category",
                    title="Expenses by Category",
                    color_discrete_sequence=px.colors.sequential.RdBu,
                )
                st.plotly_chart(fig, use_container_width=True)
            with tab2:
                st.subheader("Income Summary")
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Payments", f"${total_payments:,.2f} AED") 
                st.write(credits_df)

main()