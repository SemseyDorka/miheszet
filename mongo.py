import os
from dotenv import load_dotenv
import streamlit as st
import pymongo
import certifi
from datetime import datetime
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")



if mongo_uri:
    print(f"Siker: A betöltött URI eleje: {mongo_uri[:20]}...")
else:
    print("HIBA: A MONGO_URI üres! Ellenőrizd a .env fájlt.")

def get_database():
    if not mongo_uri:
            raise ValueError("A MONGO_URI környezeti változó nincs beállítva!")
            
    client = pymongo.MongoClient(mongo_uri, tlsCAFile=certifi.where())
    return client["mehesz_projekt_db"]

def save_entry(tartalom, elemzes):
    try:
        db = get_database()
        collection = db["naplo_bejegyzesek"]
        
        document = {
            "datum": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tartalom": tartalom,
            "elemzes": elemzes,
            "created_at": datetime.utcnow()  
        }
        
        collection.insert_one(document)
    except Exception as e:
        st.error(f"Adatbázis mentési hiba: {e}")

def get_entries():
    try:
        db = get_database()
        collection = db["naplo_bejegyzesek"]
        

        cursor = collection.find().sort("created_at", -1)
        return list(cursor)
    except Exception as e:
        st.error(f"Adatbázis lekérdezési hiba: {e}")
        return []
