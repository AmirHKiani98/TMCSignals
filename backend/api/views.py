import os
import json
import base64
import pandas as pd
from django.http import JsonResponse, HttpResponse
from .utils import dataframe_to_json, find_file, find_files_live, get_snapshot
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse
from threading import Thread
# Create your views here.

@csrf_exempt
def get_intersections(request):
    file_path = os.path.join(r"L:\TO_Traffic\TMC\TMCGIS",
        'compelete_intersections.csv'
        )
    print(file_path)
    json_string = dataframe_to_json(file_path)
    # Parse the JSON string back to Python objects
    data = json.loads(json_string)
    response = JsonResponse({"data": data, "message": "ok"}, safe=False)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@csrf_exempt
def find_file_view(request):
    if request.method == 'POST':
        sig_id = request.POST.get('sig_id', '')
        looking_text = request.POST.get('looking_text', '')
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
            'resources',
            'all_tmc_files.json'
            )
        found_files = find_file(file_path, sig_id, looking_text)
        response = JsonResponse({"found_files": found_files, "message": "ok"}, safe=False)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    response = JsonResponse({"message": "Method not allowed"}, status=405)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@csrf_exempt
def find_file_live_view(request, sig_id):
    sig_id = sig_id.lower()
    directory = r"L:\TO_Traffic\TMC"
    search_folder_path = os.path.join(directory, "TMCGIS/search_folders.json")
    with open(search_folder_path, 'r') as f:
        search_folders = json.load(f)
    # Thread on find_files_live
    thread = Thread(target=find_files_live, args=(sig_id, search_folders))
    thread.start()
    response = JsonResponse({"message": "File search started"}, safe=False)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@csrf_exempt
def get_snapshot_view(request):
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = HttpResponse()
        response.status_code = 200
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Content-Length"] = "0"
        response["Content-Type"] = "application/json"
        return response
    if request.method != "POST":
        response = JsonResponse({"message": "Method not allowed"}, status=405)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # Support both form POST and JSON POST
    sig = None
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body.decode('utf-8'))
            sig = body.get('sig_id', '').lower()
        except Exception:
            sig = ''
    else:
        sig = request.POST.get('sig_id', '').lower()
    print(f"Received sig_id: {sig}")
    directory = r"L:\TO_Traffic\TMC"
    complete_intersection = os.path.join(directory, 'TMCGIS/compelete_intersections.csv')
    df = pd.read_csv(complete_intersection)
    ip_address = df.loc[df['Signal ID'].astype(str).str.lower() == sig, 'IP Address']
    if ip_address.empty:
        response = JsonResponse({"message": "Signal ID not found"}, status=404)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POS T, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    ip_address = ip_address.values[0]
    snapshot, status = get_snapshot(ip_address)
    if status != 200 or snapshot is None:
        response = JsonResponse({"message": "Failed to get snapshot"}, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    # Encode image as base64 string for browser display
    snapshot_b64 = base64.b64encode(snapshot).decode('utf-8')
    # You may want to specify the image type, e.g. jpeg
    data_url = f"data:image/jpeg;base64,{snapshot_b64}"
    response = JsonResponse({"snapshot": data_url, "message": "ok"}, safe=False)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response
