import os
import json
from django.http import JsonResponse
from .utils import *
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
    return JsonResponse({"data": data, "message": "ok"}, safe=False)


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
        return JsonResponse({"found_files": found_files, "message": "ok"}, safe=False)
    
    return JsonResponse({"message": "Method not allowed"}, status=405)

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

    return JsonResponse({"message": "File search started"}, safe=False)

@csrf_exempt
def get_snapshot_view(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)
    sig = request.POST.get('sig_id', '').lower()
    directory = r"L:\TO_Traffic\TMC"
    complete_intersection = os.path.join(directory, 'TMCGIS/compelete_intersections.csv')
    df = pd.read_csv(complete_intersection)
    ip_address = df.loc[df['Signal ID'].astype(str).str.lower() == sig, 'IP Address']
    if ip_address.empty:
        return JsonResponse({"message": "Signal ID not found"}, status=404)
    ip_address = ip_address.values[0]
    snapshot, status = get_snapshot(ip_address)
    if status != 200:
        return JsonResponse({"message": "Failed to get snapshot"}, status=500)
    response = JsonResponse({"snapshot": snapshot, "message": "ok"}, safe=False)
    return response
