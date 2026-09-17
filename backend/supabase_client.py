"""
Supabase client initialization and helper functions.
"""

import os
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")

supabase: Client = None

def init_supabase():
    """Initialize Supabase client"""
    global supabase
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    return None

def get_supabase():
    """Get Supabase client instance"""
    if supabase is None:
        init_supabase()
    return supabase

def store_analysis(user_id, file_name, analysis_result):
    """Store analysis result in Supabase"""
    try:
        client = get_supabase()
        if not client:
            return None
        
        data = {
            "user_id": user_id,
            "file_name": file_name,
            "result": analysis_result,
        }
        
        response = client.table("analyses").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error storing analysis: {e}")
        return None

def get_user_analyses(user_id):
    """Retrieve all analyses for a user"""
    try:
        client = get_supabase()
        if not client:
            return []
        
        response = client.table("analyses").select("*").eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        print(f"Error retrieving analyses: {e}")
        return []

def upload_file_to_storage(bucket_name, file_path, file_bytes, user_id):
    """Upload file to Supabase Storage"""
    try:
        client = get_supabase()
        if not client:
            return None
        
        full_path = f"{user_id}/{file_path}"
        client.storage.from_(bucket_name).upload(full_path, file_bytes)
        
        # Get public URL
        url = client.storage.from_(bucket_name).get_public_url(full_path)
        return url
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None
