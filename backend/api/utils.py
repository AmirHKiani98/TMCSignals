import pandas as pd
import json
import os
import requests
import time
from tqdm import tqdm
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


def find_files_live(sig_id: str, search_folders) -> dict:
    """
    Mock function to simulate finding files based on signal ID.
    
    Args:
        sig_id (str): The signal ID to search for.
        
    Returns:
        dict: A dictionary containing found files.
    """
    # This is a mock implementation. Replace with actual logic as needed.
    directory = r"L:\TO_Traffic\TMC"
    files_dict = {
        key: [] for key in search_folders.keys()
    }
    for key, folder in search_folders.items():
        folder_path = os.path.join(directory, folder)
        files_dict[key] = list(get_files(folder_path, looking_for=sig_id))

    
    return files_dict

def get_files(path, looking_for, recursive=True):
    """
    Recursively yield absolute file paths in 'path' that contain 'looking_for' in their filename.
    If 'recursive' is False, only search the top-level directory.
    Returns an empty list if no files are found.
    Uses ThreadPoolExecutor for concurrent directory walking.
    """
    looking_for = looking_for.lower()
    stack = [path]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                name = entry.name.lower()
                if entry.is_file() and looking_for in name:
                    yield entry.path
                elif entry.is_dir():
                    # stack.append(entry.path)
                    pass


def get_snapshot(ip: str, str_format=None):
    """
    Generate a snapshot URL based on the provided IP, format, and quality.
    
    Args:
        ip (str): The IP address of the device.
        str_format (str): The format string to use for the URL.        
    Returns:
        str: The image will be returned
    """
    try:
        if str_format is None:
            streams_api_path = r"L:\TO_Traffic\TMC\TMCGIS\streams_api.json"
            with open(streams_api_path, 'r') as f:
                streams_api = json.load(f)
            for vendor_name, vendor_url_format in streams_api.items():
                url = vendor_url_format.format(ip=ip)
                try:
                    response = requests.get(url, timeout=2)
                    response.raise_for_status()
                    return response.content, True
                except requests.RequestException as e:
                    continue
            return None, False
        else:
            url = str_format.format(ip=ip)
            try:
                response = requests.get(url, timeout=2)
                response.raise_for_status()
                return response.content, True
            except requests.RequestException as e:
                return None, False
    except Exception as e:
        print(f"Error in get_snapshot: {e}")
        return None, False



def check_noise(image):
    pass


def get_snapshot_all_intersections(save_path=None):
    """
    Check all intersections from the intersections CSV file and verify their snapshot URLs.
    
    Returns:
        dict: A dictionary with signal IDs as keys and their snapshot URL status as values.
    """
    results = {}
    intersections_csv_path = os.path.join(
       r"L:\TO_Traffic\TMC",
        'TMCGIS',
        'compelete_intersections.csv'
    )
    df = pd.read_csv(intersections_csv_path)
    df_unique_ids = df[(df["Device DNS"].str.contains("tap") | df["Device DNS"].str.contains("ptz"))]
    streams_api_path = r"L:\TO_Traffic\TMC\TMCGIS\streams_api.json"
    with open(streams_api_path, 'r') as f:
        streams_api = json.load(f)
    print(f"Total unique intersections to check: {len(df_unique_ids)}")
    for _, row in tqdm(df_unique_ids.iterrows(), total=len(df_unique_ids), desc="Checking intersections"):
        sig_id = row['Signal ID']
        ip = row['IP Address']
        vendor = row['Vendor'].lower()
        for vendor_name, vendor_url_format in streams_api.items():
            if "api/v1" in vendor_url_format:
                for i in range(1, 6):
                    vendor_url_format_variant = vendor_url_format.replace("api/v1", f"api/v1/cameras/{i}")
                    snapshot, status = get_snapshot(ip, vendor_url_format_variant)
                    time.sleep(0.1)  # To avoid overwhelming the network

                    if status == True:
                        if save_path:
                            os.makedirs(save_path, exist_ok=True)
                            file_path = os.path.join(save_path, f"{sig_id}_{vendor_name}_{i}.jpg")
                            with open(file_path, 'wb') as img_file:
                                img_file.write(snapshot)
                            
                        results[sig_id] = {
                            "ip": ip,
                            "vendor": vendor_name,
                            "snapshot_url": vendor_url_format_variant.format(ip=ip),
                            "status": status
                        }
                if status == True:
                    break
            else:
                snapshot, status = get_snapshot(ip, vendor_url_format)
                time.sleep(0.1)  # To avoid overwhelming the network
                if status == True:
                    if save_path:
                        os.makedirs(save_path, exist_ok=True)
                        file_path = os.path.join(save_path, f"{sig_id}_{vendor_name}.jpg")
                        with open(file_path, 'wb') as img_file:
                            img_file.write(snapshot)
                        
                    results[sig_id] = {
                        "ip": ip,
                        "vendor": vendor_name,
                        "snapshot_url": vendor_url_format.format(ip=ip),
                        "status": status
                    }
                    break
    
    return results

