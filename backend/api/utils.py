import pandas as pd
import json
import os
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


def find_files_live(sig_id: str) -> dict:
    """
    Mock function to simulate finding files based on signal ID.
    
    Args:
        sig_id (str): The signal ID to search for.
        
    Returns:
        dict: A dictionary containing found files.
    """
    # This is a mock implementation. Replace with actual logic as needed.
    directory = r"L:\TO_Traffic\TMC"
    front_page_sheet_folder = "001 - Front Page Sheets"
    signal_timing_folder = "002 - Signal Timing"
    fya_folder = "006 - FYA"
    files_dict = {
        "front_page_sheets": list(get_files(os.path.join(directory, front_page_sheet_folder), looking_for=sig_id)),
        "signal_timing": list(get_files(os.path.join(directory, signal_timing_folder), looking_for=sig_id)),
        "fya": list(get_files(os.path.join(directory, fya_folder), looking_for=sig_id)),
    }
    return files_dict

def get_files(path, looking_for, recursive=True):
    """
    Recursively yield absolute file paths in 'path' that contain 'looking_for' in their filename.
    If 'recursive' is False, only search the top-level directory.
    """
    if recursive:
        for root, dirs, files in os.walk(path):
            for _file in files:
                if looking_for in _file:
                    yield os.path.join(root, _file)
    else:
        for _file in os.listdir(path):
            full_path = os.path.join(path, _file)
            if os.path.isfile(full_path) and looking_for in _file:
                yield full_path
