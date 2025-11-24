import pandas as pd
import json
def dataframe_to_json(intersections_csv_path: str) -> str:
    """
    Convert a CSV string of intersections into a JSON string.
    Args:
        intersections_csv_path (str): Path to the CSV file containing intersection data.
        the files columns are Signal ID,Corridor from signal list,Intersection Name,Group,Device DNS,Vendor,IP Address,Sub Mask,Gateway,IP not by 1,Longitude,Latitude
    Returns:
        str: JSON string representation of the intersections data.
    """
    df = pd.read_csv(intersections_csv_path)
    df_unique_ids = df.drop_duplicates(subset=['Signal ID'])
    return df_unique_ids.to_json(orient='records')



def find_file(file_path, sig_id: str, looking_text: str) -> str:
    """
    Find a file in the resources directory based on the signal ID and looking text.
    
    Args:
        sig_id (str): The signal ID to search for.
        looking_text (str): The text to look for in the file name.
        
    Returns:
        str: The path to the found file, or an empty string if not found.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    to_return = []
    for item in data:
        item_lowered = item.lower()
        if sig_id in item_lowered and looking_text in item_lowered:
            to_return.append(item)
    
    return to_return
    