
import supabase
from libs.supabase import key,url
from typing import Dict, Any




def insert_user_service(user_data: Dict[str, Any]) -> Any:
    abc = supabase.create_client(url, key)

    response = abc.table("users").insert({
        "name": user_data["name"],
        "age": user_data["age"],
    }).execute()

    return response
