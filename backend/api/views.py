import os
import json
from django.http import JsonResponse
from .utils import *
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse

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
def find_file_live_view(request, sig_id):
    sig_id = sig_id.lower()
    base_dir = r"L:\TO_Traffic\TMC"

    def event_stream():
        yield "retry: 1000\n"  # auto reconnect

        # search each folder type
        search_folders = {
            "front_page_sheets": r"001 - Front Page Sheets",
            "signal_timing": r"002 - Signal Timing",
            "fya": r"006 - FYA",
        }

        for key, folder_name in search_folders.items():
            path = os.path.join(base_dir, folder_name)
            for file_path in get_files(path, sig_id):
                yield f"data: {json.dumps({'type': key, 'file': file_path})}\n\n"

        yield "data: {\"done\": true}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")