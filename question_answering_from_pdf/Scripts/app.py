import streamlit as st
import sqlite3
from passlib.hash import pbkdf2_sha256
from langchain.document_loaders import PyPDFLoader, OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from PyPDF2 import PdfReader
from langchain.vectorstores import Pinecone
from dotenv import load_dotenv
import tempfile
from sentence_transformers import SentenceTransformer
from langchain.chains.question_answering import load_qa_chain
from nltk.tokenize import word_tokenize
import pinecone
import json
import os
import base64

# Create a connection to the SQLite database
conn_user = sqlite3.connect("user_db.db")
cursor = conn_user.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        email TEXT,
        password TEXT,
        search_history TEXT
    )
""")


conn_user.commit()

@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


img = get_img_as_base64("bg.jpg")

page_bg_img = f"""
<style>

[data-testid="stAppViewContainer"] > .main {{
background-image: url("https://digitalsynopsis.com/wp-content/uploads/2017/02/beautiful-color-gradients-backgrounds-029-everlasting-sky.png");
background-size: 200%;
background-position: top left;
background-repeat: repeat;
background-attachment: local;
}}

[data-testid="stSidebar"] > div:first-child {{
background-image: url("data:image/png;base64,{img}");
background-position: center; 
background-repeat: no-repeat;
background-attachment: fixed;
}}


</style>
"""

import streamlit as st
import base64

LOGO_IMAGE = "logo.png"

st.markdown(
    """
    <style>
    .container {
        
        position: fixed;
        bottom: 10px;
        right: 20px;
    }
    
    }
    .logo-img {
        float:right;
        width: 60px;
        height: 60px;

    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="container">
        <img class="logo-img" src="data:image/png;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}">
       
    </div>
    """,
    unsafe_allow_html=True
)
# Streamlit app
def main():

    menu = ["Home", "Register", "Login"]
    choice = st.sidebar.selectbox("Choose to register and login", menu)
    
    if choice == "Home":
        if is_logged_in():
            username = get_logged_in_username()
            # st.title("Home Screen")
            # st.subheader("You are all set for your QA LLM's")
            st.subheader("Hello, {}".format(username))
            #st.write("Welcome to the User Registration and Login system.")
            
            search_history_button = st.button("Search History")
            clear_history_button = st.button("Clear")
            logout_button = st.button("Logout")
    
            if logout_button:
                logout()
            elif search_history_button:
                show_search_history(username)
            elif clear_history_button:
                clear_search_history(username)                
            
        else:
            st.subheader("Please register and log in to our app.")


    elif choice == "Register":
        st.subheader("Create New Account")
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        if st.button("Register"):
            if user_exists(new_username):
                st.warning("Username already exists")
            elif email_exists(new_email):
                st.warning("Email address already registered")
            elif new_password == confirm_password:
                if register_user(new_username, new_email, new_password):
                    st.success("Account created for {}".format(new_username))
                    st.snow()
                else:
                    st.warning("Registration failed")
            else:
                st.warning("Passwords do not match")


    elif choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.checkbox("Login"):
            if login_user(username, password):
                set_logged_in_username(username)
                st.success("Logged in as {}".format(username))
                tab1, tab2= st.tabs(["QA LLM model","OCR"])
                with tab1:
                    if is_logged_in():
                        st.title("You are all set for your QA LLM's")
                        st.subheader("Search from your pdf")
                        ask_pdf_section(username)
                
            else:
                st.warning("Invalid username or password")


def register_user(username, email, password):
    encrypted_password = pbkdf2_sha256.hash(password)
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, encrypted_password))
        conn_user.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user and pbkdf2_sha256.verify(password, user[3]):
        return True
    return False

def user_exists(username):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user:
        return True
    return False

def email_exists(email):
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user:
        return True
    return False

def clear_search_history(username):
    print("Clearing search history...")
    try:
        cursor.execute("UPDATE users SET search_history = ? WHERE username = ?", (None, username))
        conn_user.commit()
        st.success("Search history cleared successfully.")
    except sqlite3.OperationalError as e:
        print("OperationalError:", e)
        st.warning("Search history feature not available for this user.")
    except Exception as e:
        st.warning("An error occurred:", e)


def ask_pdf_section(username):
    load_dotenv()
    file = st.file_uploader("Upload your file",type='pdf') 

    if file is not None:
        try:
            # Save the uploaded PDF to a temporary file
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, file.name)
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file.read())

            # Load PDF using PyPDFLoader
            pdf_reader = PyPDFLoader(temp_file_path)
            file = pdf_reader.load()
            st.write(len(file))
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                os.rmdir(temp_dir)

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
                docs = text_splitter.split_documents(file)
                st.write(len(docs))

                embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

                pinecone.init(
                   api_key = os.getenv('PINECONE_API_KEY'),
                   environment = os.getenv('PINECONE_API_ENV')
                )
                index_name = "langchainpinecone1"

                # Create Embeddings for Each of the Text Chunk
                dosearch =Pinecone.from_texts([t.page_content for t in docs], embeddings, index_name=index_name)

                # If you already have an index, you can load it like this
                dosearch = Pinecone.from_existing_index(index_name, embeddings)
                
                query = st.text_input("Ask Questions from your PDF:")
                
                if query:
                    search_results = dosearch.similarity_search(query)
                   
                    if search_results:
                        extracted_txt = ""
                        for index, result in enumerate(search_results):
                            print(index,result)
                        
                            page_content = result.page_content
                            extracted_txt =extracted_txt.strip()+page_content

                        extracted = word_tokenize(extracted_txt)
                   
                        extracted = extracted[:120]
                        # print(extracted)
                        extracted_text = ' '.join(extracted)
                        # print(extracted_text)
                        st.write(extracted_text,"\n")
                        st.write("This is trained on :red[minimal resources]","\n")

                        st.write("You can find :blue[search history] in home")   

                        
                        store_search_history(username, query, extracted_text)





def show_search_history(username):
    try:
        cursor.execute("SELECT search_history FROM users WHERE username = ?", (username,))
        current_history = cursor.fetchone()[0]
        
        if current_history:
            current_history = json.loads(current_history)
        
            for entry in current_history:
                st.write("Query:", entry["query"])
                st.write("Result:", entry["result"])
                st.write("-----")
            
        else:
            st.warning("No search history available for this user.")
    except sqlite3.OperationalError as e:
        st.warning("OperationalError:", e)
        st.warning("Search history feature not available for this user.")
    except Exception as e:
        st.warning("An error occurred:", e)


def store_search_history(username, query, result):
    try:
        cursor.execute("SELECT search_history FROM users WHERE username = ?", (username,))
        current_history = cursor.fetchone()[0]

        new_entry = {"query": query, "result": result}

        if current_history:
            current_history = json.loads(current_history)
            current_history.append(new_entry)
            updated_history = json.dumps(current_history)
        else:
            updated_history = json.dumps([new_entry])

        cursor.execute("UPDATE users SET search_history = ? WHERE username = ?", (updated_history, username))
        conn_user.commit()
        st.success("Search history updated successfully.")
    except sqlite3.OperationalError as e:
        st.warning("OperationalError:", e)
        st.warning("Search history feature not available for this user.")
    except Exception as e:
        st.warning("An error occurred:", e)




def is_logged_in():
    return st.session_state.get("logged_in_username") is not None

def logout():
 
    set_logged_in_username(None)


def set_logged_in_username(username):
    st.session_state.logged_in_username = username

def get_logged_in_username():
    return st.session_state.logged_in_username

if __name__ == "__main__":
    main()
