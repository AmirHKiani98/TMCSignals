import os
import json
from django.http import JsonResponse
from .utils import *
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

@csrf_exempt
def get_intersections(request):
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
            'resources',
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
def find_file_live_view(request):
    if request.method == 'POST':
        sig_id = request.POST.get('sig_id', '')
        
        data = find_files_live(sig_id)
        return JsonResponse({"data": data, "message": "ok"}, safe=False)
    
    return JsonResponse({"message": "Method not allowed"}, status=405)