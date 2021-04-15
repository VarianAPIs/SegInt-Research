"""
Copyright 2021 Varian Medical Systems, Inc.
Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without 
restriction, including without limitation the rights to use, copy, modify, merge, publish, 
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the 
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or 
substantial portions of the Software.
The Software shall be used for non-clinical use only and shall not be used to enable, provide, 
or support patient treatment. "Non-clinical" or "non-clinical use" means usage not involving: 
(i) the direct observation of patients; (ii) the diagnoses of disease or other conditions in 
humans or other animals; or (iii) the cure, mitigation, therapy, treatment, treatment planning,
or prevention of disease in humans or other animals to affect the structure or function thereof.  
The Software is NOT U.S. FDA 510(k) cleared for use on humans and shall not be used on humans.
Any use of the Software outside of its intended use (“off-label”) could lead to physical harm
or death of patients. 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING 
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY NON-CLINICAL OR OFF-LABEL 
USE OF THE SOFTWARE AND ANY PERSON THAT USES, COPIES, MODIFIES, MERGES, PUBLISHES, DISTRIBUTES, 
SUBLICENSES, AND/OR SELLS COPIES OF THE SOFTWARE UNDER THIS PERMISSION NOTICE HEREBY AGREES TO 
INDEMNIFY AND HOLD HARMLESS THE AUTHORS AND COPYRIGHT HOLDERS FOR ANY LIABILITY, DEMAND, DAMAGE,
COST OR EXPENSE ARISING FROM OR RELATING TO SUCH NON-CLINICAL OR OFF-LABEL USE OF THE SOFTWARE.
"""

"""Segint django api module"""

from django.shortcuts import render

# Django imports
from django.http import HttpResponse, HttpRequest, Http404, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files import File
from django.utils import timezone

# Model imports
from segint_api.models import *
from segint_api.tasks import *

# Protobuf imports
from protobuf import Model_pb2, Primitives3D_pb2
import google.protobuf.json_format as json_format

# Other imports
import re
import io
import uuid
import pytz
import socket
from base64 import decodestring

# Version-control
GROUP_VERSION = '0'
MAJOR_VERSION = '0.'
MINOR_VERSION = '0.1 Research Server Development Test'

def format_and_send_response(request, response, status=200):
    '''
    Helper method for sending either Protobuf or JSON response.
    '''
    if request.headers["accept"] == "application/x-protobuf":
        return HttpResponse(response.SerializeToString(), status=status)
    return JsonResponse(json_format.MessageToDict(response), status=status)

def get_check(func):
    '''
    Decorator function to check to see if the endpoint is being accessed with GET request.

    Parameters:
        request - request body object

    Returns:
        bad request message if request method is not GET
    '''
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.method != "GET":
            msg = "Invalid request."
            details = "POST request invalid.  This endpoint only allows GET requests."
            return bad_request_helper(request, msg, details, 403)
        return func(*args, **kwargs)
    return wrapper


def post_check(func):
    '''
    Decorator function to check to see if the endpoint is being accessed with POST request.

    Parameters:
        request - request body object

    Returns:
        bad request message if request method is not POST
    '''
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.method != "POST":
            msg = "Invalid request."
            details = "GET request invalid.  This endpoint only allows POST requests."
            return bad_request_helper(request, msg, details, 403)
        return func(*args, **kwargs)
    return wrapper

def enforce_protobuf(func):
    '''
    Decorator function to check to see if the endpoint is being accessed the correct content-type.
    Currently, the endpoint requires "application/x-protobuf".

    Parameters:
        request - request body object

    Returns:
        bad request message if request body is incorrect content-type
    '''
    def wrapper(*args, **kwargs):
        request = args[0]
        if request.content_type != 'application/x-protobuf':
            msg = "Invalid request."
            details = "Content type invalid. This endpoint" + \
                " currently only accepts protobuf messages."
            return bad_request_helper(request, msg, details, 415)
        return func(*args, **kwargs)
    return wrapper

def bad_request_helper(request, msg, details, status):
    '''
    Helper method for generating bad request responses.

    Parameters:
        request - The original request
        msg - str - Error message
        details - str - Details regarding the bad request response.
        status - int - Status code to use in response.

    Returns:
        HttpResponse - Model_pb2.BadRequestResponse - If 'accept' type is 'application/x-protobuf'
        JsonResponse - Model_pb2.BadRequestResponse - Otherwise

    '''
    response = Model_pb2.BadRequestResponse()
    response.ErrorMessage = msg
    response.ExceptionDetails = details
    return format_and_send_response(request, response, status=status)



# /ping
# /api/ping
@csrf_exempt
@get_check
def ping(request):
    '''
    Endpoint for API ping GET requests.

    Returns either:
        1. Protobuf-serialized response if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''
    version = MAJOR_VERSION + MINOR_VERSION
    api_info = Model_pb2.ApiInformation()
    api_info.Version = version
    return format_and_send_response(request, api_info)


# /api/v2/Credits/
@csrf_exempt
@get_check
def get_credits(request):
    '''
    Endpoint for API GET Credits request.  Since this is a research server, mock information
    will be returned.  The user will have plenty of credits.  In addition, a message will be
    returned to indicate that credits will not apply.

    Returns either:
        1. Protobuf-serialized response if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''

    total_cred = 100000
    display_warning = True
    message = "Local Research Server - Credits will not apply."
    language = "English"

    credits_info = Model_pb2.Credits()
    credits_info.TotalCredits = total_cred
    credits_info.DisplayCreditsWarning = display_warning
    credits_info.CreditsWarningMessage = message
    credits_info.LanguageCode = language
    return format_and_send_response(request, credits_info)


# /api/v2/Feedback/segmentation/
@csrf_exempt
@post_check
@enforce_protobuf
def post_feedback(request):
    '''
    Endpoint for API POST Segmentation Feedback request.  Since this is a research server,
    information will be stored in the database, but it will be up to the end-user to decide
    how to interpret feedback.

    Enforces request to be in protobuf format.

    Returns:
        1. Protobuf message if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''
    # Tries to construct feedback in database, returning error if fields are empty.
    try:
        new_feedback = Feedback()
        new_feedback.pb_to_model(request.body)
        new_feedback.save()
        return HttpResponse("POST successful.", status=200)

    # On exception, returns invalid request error message pb.
    except:
        msg = "Invalid request."
        details = "The posted segmentation feedback is not valid." +\
        	" It might have empty fields that are required."
        return bad_request_helper(request, msg, details, 400)


# /api/v2/Model/
@csrf_exempt
@get_check
def get_models(request):
    '''
    Endpoint for API GET Model Collections request.

    Returns:
        1. ModelsCollection protobuf message if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''
    # Tries to construct collection of model families, returning an error if failure.
    try:
        # Creates protobuf collection object
        response = Model_pb2.ModelsCollection()

        # Iterates through all model familys and adds to collection
        for model_fam in ModelFamily.objects.all():

            # Check if pb file exists.
            if model_fam.pb == '':
                fname = model_fam.canonical_name
                fname.replace(' ', '-')
                pb_msg = model_fam.model_to_pb().SerializeToString()
                file_io = io.BytesIO(bytes(pb_msg))
                model_fam.pb.save(fname+".pb", File(file_io))
                model_fam.save()

            mf_file = open(model_fam.pb.path, 'rb')
            file_pb = mf_file.read()
            mf_file.close()

            # Check if fields are filled.
            if model_fam.canonical_name == '':
                model_fam.pb_to_model(file_pb)
                model_fam.save()

            mf_pb = Model_pb2.ModelFamily()
            mf_pb.ParseFromString(file_pb)
            response.Models.append(mf_pb)

        return format_and_send_response(request, response)

    # On exception, returns invalid request error message pb.
    except:
        msg = "Invalid request."
        details = "The request is not acceptable."
        return bad_request_helper(request, msg, details, 406)



# /api/v2/Model/{modelId}/segmentation/
@csrf_exempt
@post_check
@enforce_protobuf
def post_segmentation(request, model_id):
    '''
    Endpoint for API POST Segmentation Job requests.
    Enforces protobuf msg input.

    Parameters:
        model_id (str) - model_id with which the segmentation job should use.

    Returns:
        1. SegmentationTask protobuf message if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''

    # Tries to create a segmentation task entry in the database.
    seg_job = SegmentationJob()
    try:
        # Set model ID
        seg_job.model_id = model_id
        # Generate Segmentation ID and 'time_created' using current datetime with TZ support.
        seg_job.time_field = timezone.now()
        # Generate file on disk and point database to location
        request_data = bytes(request.body)
        # Check valid model input
        seg_pb = Model_pb2.ModelInput()
        seg_pb.ParseFromString(request_data)
        # Save model input
        file_io = io.BytesIO(request_data)
        fname = "{}.pb".format("Segmentation_{}".format(seg_job.segmentation_id))
        seg_job.model_input.save(fname, File(file_io))
        seg_job.save()

    except:
        seg_job.delete()
        msg = "Invalid request."
        details = "The posted model input is not valid. "+\
        	"It might have empty fields that are required."
        return bad_request_helper(request, msg, details, 400)

    # Start asynchronous segmentation with state machine

    m_v = ModelVersion.objects.filter(model_version_id=model_id)[0]
    if m_v.model_type == ModelVersion.ModelVersionType.Phantom:
        start_phantom_segmentation.delay(model_id, seg_job.segmentation_id)
    elif m_v.model_type == ModelVersion.ModelVersionType.Pytorch:
        start_pytorch_segmentation_single_structure.delay(model_id, seg_job.segmentation_id)
    elif m_v.model_type == ModelVersion.ModelVersionType.Tensorflow:
        start_phantom_segmentation.delay(model_id, seg_job.segmentation_id)
    else:
        start_phantom_segmentation.delay(model_id, seg_job.segmentation_id)

    # Construct SegmentationTask response.
    response = seg_job.get_task_response()
    return format_and_send_response(request, response)


# /api/v2/Model/{modelId}/segmentation/{segmentationId}/
@csrf_exempt
@get_check
def get_segmentation_progress(request, model_id, segmentation_id):
    '''
    Endpoint for API GET Segmentation Job progress requests.

    Parameters:
        model_id (str) - model_id with which the segmentation job should use.
        segmentation_id (str) - UUID str for the segmentation job

    Returns:
        1. SegmentationTask protobuf message if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''

    # Database query for segmentation job with segmentation_id parameter.
    try:
        seg_job = SegmentationJob.objects.get(model_id=model_id, segmentation_id=segmentation_id)
    except:
        msg = "Invalid request."
        details = "The segmentation job does not exist."
        return bad_request_helper(request, msg, details, 400)

    # Query for job progress
    response = seg_job.get_job_progress()
    return format_and_send_response(request, response)


# /api/v2/Model/{modelId}/segmentation/{segmentationId}/result/
@csrf_exempt
@get_check
def get_segmentation_result(request, model_id, segmentation_id):
    '''
    Endpoint for API GET Segmentation Job result requests.

    Parameters:
        model_id (str) - model_id with which the segmentation job should use.
        segmentation_id (str) - UUID str for the segmentation job

    Returns:
        1. ModelOutput protobuf message if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''

    # Database query for segmentation job with segmentation_id parameter.
    try:
        seg_job = SegmentationJob.objects.get(model_id=model_id, segmentation_id=segmentation_id)
    except:
        msg = "Invalid request."
        details = "The segmentation job does not exist."
        return bad_request_helper(request, msg, details, 400)

    job_status = seg_job.get_job_progress()

    # Return unfinished bad request if progress isn't 100.
    if job_status.Progress < 100:
        msg = "Invalid request."
        details = "The segmentation job is still processing."
        return bad_request_helper(request, msg, details, 400)

    try:
        # Attempts to read the file as bytestring
        model_out_path = seg_job.model_output.path
        f_in = open(model_out_path, 'rb')
        model_out = f_in.read()
        f_in.close()

        if request.headers["accept"] == "application/x-protobuf":
            seg_job.delete()
            return HttpResponse(model_out, status=200)
        # Else
        response = Model_pb2.ModelOutput()
        response.ParseFromString(model_out)
        seg_job.delete()
        return JsonResponse(json_format.MessageToDict(response), status=200)
    except:
        msg = "Invalid request."
        details = "The segmentation job has encountered an error."
        return bad_request_helper(request, msg, details, 400)


# /api/v2/Telemetry/segmentation/
@csrf_exempt
@post_check
@enforce_protobuf
def post_telemetry(request):
    '''
    Endpoint for API POST Segmentation Telemetry request.  Since this is a research server,
    information will be stored in the database, but it will be up to the end-user to decide
    how to interpret telemetry.

    Enforces request to be in protobuf format.

    Returns:
        1. Protobuf message if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''

    # Tries to construct telemetry in database, returning error if fields are empty.
    try:
        new_telemetry = SegmentationTelemetry()
        new_telemetry.pb_to_model(request.body)
        new_telemetry.save()
        return HttpResponse("POST successful.", status = 200)

    # On exception, returns invalid request error message pb.
    except:
        msg = "Invalid request."
        details = "The posted segmentation telemetry is not valid. "+\
        	"It might have empty fields that are required."
        return bad_request_helper(request, msg, details, 400)

# /api/v2/VendorStatus/
@csrf_exempt
@get_check
def get_vendor_status(request):
    '''
    Endpoint for API GET Vendor Status requests.

    Since this is a private research server, all information is mocked up.

    Returns:
        1. ModelOutput protobuf message if "accept" header is "application/x-protobuf"
        2. JSON response otherwise
    '''
    response = Model_pb2.VendorStatus()
    response.TotalCredits = 100000
    response.LowCreditsWarningMessage = "Local Research Server - Credits will not apply."
    response.ClientCountryCode = "US"
    response.SegmentationServiceStatus = Model_pb2.VendorStatus.VendorServiceStatus.Available
    ip_addr = get_ip_address()
    response.SegmentationServiceUrl = "http://" + ip_addr + ":8000/api/v2/"
    response.AvailableSegmentationServiceLocations.append("US")
    response.VendorName = "Research Server"
    response.VendorDescriptionHtml = ""
    response.LanguageCode = "en-US"
    return format_and_send_response(request, response)

def get_ip_address():
    '''
    Helper method to return external IP address for the server.

    Returns:
        ip_ad - str - external IP address for the server.
    '''
    web_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    web_socket.connect(("8.8.8.8", 80))
    ip_ad = web_socket.getsockname()[0]
    web_socket.shutdown(0)
    web_socket.close()
    return ip_ad
