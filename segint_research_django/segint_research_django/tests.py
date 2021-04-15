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

import io
import time
import os

from django.test import TestCase, TransactionTestCase
from django.core.files import File
from segint_api.models import *
from protobuf import Model_pb2, Primitives3D_pb2
from celery.contrib.testing.worker import start_worker
from segint_research_django.celery import app

#----------------------------------------------------------------------------------------------
# Integration Tests for Anatomical Transaction Server for Research
#----------------------------------------------------------------------------------------------
# Django testing instantiates a temporary test database that is deleted upon test completion.
# Currently does not support asynchronous Celery tasks.  To run the tests, force Celery tasks
# to run synchronously:  Change variable 'CELERY_ALWAYS_EAGER' in 'settings.py' to 'True'.
#----------------------------------------------------------------------------------------------

class PingTestCase(TestCase):
    '''
    End-to-end testing for endpoints:
        /ping
        /api/ping
    Tests GET requests for accepting both 'application/json' and 'application/x-protobuf' types
    '''

    def test_ping_json(self):
        '''
        Test for endpoint: /ping
        With accept-type "application/json"
        '''
        response = self.client.get('/ping', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 200, \
            msg='/ping endpoint did not return 200 status code.')
        self.assertNotEqual(response.json()['Version'], None, \
            msg='/ping endpoint did not return proper JSON message.')

    def test_ping_protobuf(self):
        '''
        Test for endpoint: /ping
        With accept-type "application/x-protobuf"
        '''
        response = self.client.get('/ping', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 200, \
            msg='/ping endpoint did not return 200 status code.')

        response_pb = Model_pb2.ApiInformation()
        response_pb.ParseFromString(response.content)
        self.assertNotEqual(response_pb.Version, None, \
            msg='/ping endpoint did not return proper Protobuf message.')

    def test_api_ping_json(self):
        '''
        Test for endpoint: /api/ping
        With accept-type "application/json"
        '''
        response = self.client.get('/api/ping', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/ping endpoint did not return 200 status code.')
        self.assertNotEqual(response.json()['Version'], None, \
            msg='/api/ping endpoint did not return proper JSON message.')

    def test_api_ping_protobuf(self):
        '''
        Test for endpoint: /api/ping
        With accept-type "application/x-protobuf"
        '''
        response = self.client.get('/api/ping', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/ping endpoint did not return 200 status code.')

        response_pb = Model_pb2.ApiInformation()
        response_pb.ParseFromString(response.content)
        self.assertNotEqual(response_pb.Version, None, \
            msg='/api/ping endpoint did not return proper Protobuf message.')


class GetCreditsTestCase(TestCase):
    '''
    End-to-end testing for endpoints:
        /api/v2/Credits
    Tests GET requests for accepting both 'application/json' and 'application/x-protobuf' types
    '''
    def test_get_credits_json(self):
        '''
        Test for endpoint: /api/v2/Credits
        With accept-type "application/json"
        '''
        response = self.client.get('/api/v2/Credits',\
            **{'HTTP_ACCEPT':'application/json'})
        response_content = response.json()
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Credits endpoint did not return 200 status code.')
        self.assertEqual(response_content['TotalCredits'], 100000.0, \
            msg='/api/v2/Credits endpoint did not return proper JSON message.')

    def test_get_credits_protobuf(self):
        '''
        Test for endpoint: /api/v2/Credits
        With accept-type "application/x-protobuf"
        '''
        response = self.client.get('/api/v2/Credits',\
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Credits endpoint did not return 200 status code.')

        response_pb = Model_pb2.Credits()
        response_pb.ParseFromString(response.content)
        self.assertEqual(response_pb.TotalCredits, 100000.0, \
            msg='/api/v2/Credits endpoint did not return proper Protobuf message.')

    def test_get_credits_fail(self):
        '''
        Test for endpoint: /api/v2/Credits
        With POST request: anticipate 403 code
        '''
        response = self.client.post('/api/v2/Credits', \
            b'Test content', \
            content_type='application/x-protobuf', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 403, \
            msg="/api/v2/Credits endpoint allowed POST request.")


class GetModelsTestCase(TestCase):
    '''
    End-to-end testing for endpoints:
        /api/v2/Model/
    Tests GET requests for accepting both 'application/json' and 'application/x-protobuf' types
    '''

    @classmethod
    def setUpTestData(cls):
        '''
        Load a phantom ModelFamily into the testing database
        '''
        pb_file = open('staticfiles/testing/Centered_Square.pb', 'rb')
        pb_bytes = pb_file.read()
        pb_file.close()
        cls.model_family = ModelFamily.objects.create()
        cls.model_family.pb.save('Centered_Square.pb', File(io.BytesIO(bytes(pb_bytes))))
        cls.model_family.pb_to_model(pb_bytes)
        cls.model_family.save()
        m_v = cls.model_family.modelversion_set.all()[0]
        m_v.model_type = ModelVersion.ModelVersionType.Phantom
        m_v.save()

    @classmethod
    def tearDownClass(cls):
        '''
        The testing-db is deleted upon test completion.  However, Django orphans Filefields to
        protect against data loss.  For testing purposes, we will need to keep track of files
        created and delete them on testcase class teardown.
        '''
        super().tearDownClass()
        os.remove(GetModelsTestCase.model_family.pb.path)

    def setUp(self):
        '''
        Setup a removal list for orphaned media files upon database destruction.
        '''
        self.path_list = []

    def tearDown(self):
        '''
        The testing-db is deleted upon test completion.  However, Django orphans Filefields to
        protect against data loss.  For testing purposes, we will need to keep track of files
        created and delete them on testcase class teardown.
        '''
        for path in self.path_list:
            os.remove(path)

    def test_get_models_json(self):
        '''
        Test for endpoint: /api/v2/Model/
        With accept-type "application/json"
        '''
        response = self.client.get('/api/v2/Model/', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Model/ endpoint did not return 200 status code.')
        response_content = response.json()
        self.assertEqual(len(response_content['Models']), 1, \
            msg='/api/v2/Model/ endpoint did not return correct JSON message.')
        self.assertEqual((response_content['Models'][0])['CanonicalName'], \
            GetModelsTestCase.model_family.canonical_name, \
            msg='/api/v2/Model/ endpoint did not return correct Phantom model.')

    def test_get_models_protobuf(self):
        '''
        Test for endpoint: /api/v2/Model/
        With accept-type "application/x-protobuf"
        '''
        response = self.client.get('/api/v2/Model/', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Model/ endpoint did not return 200 status code.')

        response_pb = Model_pb2.ModelsCollection()
        response_pb.ParseFromString(response.content)
        self.assertEqual(len(response_pb.Models), 1, \
            msg='/api/v2/Model/ endpoint did not return correct JSON message.')
        self.assertEqual(response_pb.Models[0].CanonicalName, \
            GetModelsTestCase.model_family.canonical_name, \
            msg='/api/v2/Model/ endpoint did not return correct Phantom model.')

    def test_get_models_blank_name(self):
        '''
        Test for endpoint: /api/v2/Model/
        With accept-type "application/x-protobuf"
        '''
        # Create new database ModelFamily object.
        with open('staticfiles/testing/Centered_Square.pb', 'rb') as pb_file:
            pb_bytes = pb_file.read()
        new_model_family = ModelFamily.objects.create()
        new_model_family.pb.save('Centered_Square.pb', File(io.BytesIO(bytes(pb_bytes))))
        new_model_family.save()
        self.path_list.append(new_model_family.pb.path)
        # Test endpoint
        response = self.client.get('/api/v2/Model/', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Model/ endpoint did not return 200 status code.')
        # Test model family objects for fidelity
        response_content = response.json()
        for model_family in response_content['Models']:
            self.assertEqual(model_family['CanonicalName'], "Centered Square", \
                msg='/api/v2/Model/ endpoint did not return correct model names')

    def test_get_models_blank_pb(self):
        '''
        Test for endpoint: /api/v2/Model/
        With accept-type "application/json"
        Convert model to fill pb field.
        '''
        with open('staticfiles/testing/Centered_Square.pb', 'rb') as pb_file:
            pbstr = pb_file.read()
        new_model_family = ModelFamily.objects.create()
        new_model_family.pb.save('Centered_Square.pb', File(io.BytesIO(bytes(pbstr))))
        new_model_family.save()
        response = self.client.get('/api/v2/Model/', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Model/ endpoint did not return 200 status code.')

        mf2 = ModelFamily.objects.all()[1]
        self.path_list.append(mf2.pb.path)
        mf2.pb = ''
        mf2.save()
        response = self.client.get('/api/v2/Model/', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Model/ endpoint did not return 200 status code.')
        mf2 = ModelFamily.objects.all()[1]
        self.path_list.append(mf2.pb.path)

    def test_get_models_error(self):
        '''
        Test for endpoint: /api/v2/Model/
        With accept-type "application/json"
        Convert model to fill pb field.
        '''
        with open('staticfiles/testing/Centered_Square.pb', 'rb') as pb_file:
            pbstr = pb_file.read()
        new_model_family = ModelFamily.objects.create()
        new_model_family.pb.save('Centered_Square.pb', File(io.BytesIO(bytes(pbstr))))
        new_model_family.save()
        response = self.client.get('/api/v2/Model/', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Model/ endpoint did not return 200 status code.')
        mf2 = ModelFamily.objects.all()[1]
        self.path_list.append(mf2.pb.path)
        new_model_family.pb = ''
        new_model_family.save()
        response = self.client.get('/api/v2/Model/', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 406, \
            msg='/api/v2/Model/ endpoint did not return 406 status code.')


class PostFeedbackTestCase(TestCase):
    '''
    End-to-end testing for endpoints:
        /api/v2/Feedback/segmentation
    Tests POST requests for accepting both 'application/json' and 'application/x-protobuf' types
    '''

    def setUp(self):
        '''
        Opens a special feedback protobuf message for usage in testing.
        '''
        file_opened = open('staticfiles/testing/test_fb.pb', 'rb')
        self.feedback_message = file_opened.read()
        file_opened.close()

    def test_post_feedback_content_type_json(self):
        '''
        Test for endpoint: /api/v2/Feedback/segmentation
        With content-type "application/json"
        '''
        response = self.client.post('/api/v2/Feedback/segmentation', \
            self.feedback_message, \
            content_type='application/json', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 415, \
            msg='/api/v2/Feedback/segmentation endpoint did not return 415 status code.')

    def test_post_feedback_content_type_protobuf(self):
        '''
        Test for endpoint: /api/v2/Feedback/segmentation
        With content-type "application/x-protobuf"
        '''
        response = self.client.post('/api/v2/Feedback/segmentation', \
            self.feedback_message, \
            content_type='application/x-protobuf', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Feedback/segmentation endpoint did not return 200 status code.')

    def test_post_feedback_invalid(self):
        '''
        Test for endpoint: /api/v2/Feedback/segmentation
        Post invalid feedback message
        '''
        file_opened = open('staticfiles/testing/test_telemetry.pb', 'rb')
        feedback_invalid = file_opened.read()
        file_opened.close()
        response = self.client.post('/api/v2/Feedback/segmentation', \
            feedback_invalid, \
            content_type='application/x-protobuf', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 400, \
            msg='/api/v2/Feedback/segmentation endpoint did not return 400 status code' + \
            ' for invalid feedback protobuf message.')


class PostTelemetryTestCase(TestCase):
    '''
    End-to-end testing for endpoints:
        /api/v2/Telemetry/segmentation
    Tests POST requests for accepting both 'application/json' and 'application/x-protobuf' types
    '''

    def setUp(self):
        '''
        Opens a special telemetry protobuf message for usage in testing.
        '''
        with open('staticfiles/testing/test_telemetry.pb', 'rb') as file_opened:
            self.telemetry = file_opened.read()

    def test_get_telemetry_fail(self):
        '''
        Test for endpoint: /api/v2/Telemetry/segmentation
        With GET request: anticipate 403 code
        '''
        response = self.client.get('/api/v2/Telemetry/segmentation', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 403, \
            msg='/api/v2/Telemetry/segmentation endpoint allowed GET request.')

    def test_post_telemetry_content_type_json(self):
        '''
        Test for endpoint: /api/v2/Telemetry/segmentation
        With content-type "application/json"
        '''
        response = self.client.post('/api/v2/Telemetry/segmentation', \
            self.telemetry, \
            content_type='application/json', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 415, \
            msg='/api/v2/Telemetry/segmentation endpoint did not return 415 status code.')

    def test_post_telemetry_content_type_protobuf(self):
        '''
        Test for endpoint: /api/v2/Telemetry/segmentation
        With content-type "application/x-protobuf"
        '''
        response = self.client.post('/api/v2/Telemetry/segmentation', \
            self.telemetry, \
            content_type='application/x-protobuf', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/Telemetry/segmentation endpoint did not return 200 status code.')

    def test_post_telemetry_invalid_input(self):
        '''
        Test for endpoint: /api/v2/Telemetry/segmentation
        Post invalid telemetry
        '''
        with open('staticfiles/testing/Centered_Square.pb', 'rb') as file_opened:
            bad_telemetry = file_opened.read()
        response = self.client.post('/api/v2/Telemetry/segmentation', \
            bad_telemetry, \
            content_type='application/x-protobuf', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 400, \
            msg='/api/v2/Telemetry/segmentation endpoint did not return 400 status code.')


class GetVendorStatusTestCase(TestCase):
    '''
    End-to-end testing for endpoints:
        /api/v2/VendorStatus
    Tests POST requests for accepting both 'application/json' and 'application/x-protobuf' types
    '''

    def test_vendor_status_json(self):
        '''
        Test for endpoint: /api/v2/VendorStatus
        With content-type "application/json"
        '''
        response = self.client.get('/api/v2/VendorStatus', \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/VendorStatus endpoint did not return 200 status code.')

    def test_vendor_status_protobuf(self):
        '''
        Test for endpoint: /api/v2/VendorStatus
        With content-type "application/x-protobuf"
        '''
        response = self.client.get('/api/v2/VendorStatus', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(response.status_code, 200, \
            msg='/api/v2/VendorStatus endpoint did not return 200 status code.')


class PostSegmentationTestCase(TestCase):
    '''
    End-to-end testing for endpoints:
        /api/v2/Model/{modelId}/segmentation
        /api/v2/Model/{modelId}/segmentation/{segmentationId}
        /api/v2/Model/{modelId}/segmentation/{segmentationId}/result
    Tests requests for accepting both 'application/json' and 'application/x-protobuf' types
    '''
    @classmethod
    def setUpTestData(cls):
        '''
        Sets up temporary database objects for a phantom model family.

        cls.model_family - ModelFamily database object
        cls.model_version - Model Version database object
        '''
        pb_file = open('staticfiles/testing/Centered_Square.pb', 'rb')
        pb_bytes = pb_file.read()
        pb_file.close()
        cls.model_family = ModelFamily.objects.create()
        cls.model_family.pb.save('Centered_Square.pb', File(io.BytesIO(bytes(pb_bytes))))
        cls.model_family.pb_to_model(pb_bytes)
        cls.model_family.save()
        cls.model_version = cls.model_family.modelversion_set.all()[0]
        cls.model_version.model_type = ModelVersion.ModelVersionType.Phantom
        cls.model_version.save()

    @classmethod
    def tearDownClass(cls):
        '''
        The testing-db is deleted upon test completion.  However, Django orphans Filefields to
        protect against data loss.  For testing purposes, we will need to keep track of files
        created and delete them on testcase class teardown.
        '''
        super().tearDownClass()
        os.remove(PostSegmentationTestCase.model_family.pb.path)

    def setUp(self):
        '''
        Creates a test-class object representing the segmentation job to be posted.

        self.seg_job - SegmentationJob Protobuf message read from disk.
        '''
        with open('staticfiles/testing/test_segmentation.pb', 'rb') as file_opened:
            self.seg_job = file_opened.read()
        self.path_list = []

    def tearDown(self):
        '''
        The testing-db is deleted upon test completion.  However, Django orphans Filefields to
        protect against data loss.  For testing purposes, we will need to keep track of files
        created and delete them on testcase class teardown.
        '''
        for path in self.path_list:
            os.remove(path)

    def test_post_job_bad_file(self):
        '''
        Test for endpoints:  /api/v2/Model/{modelId}/segmentation
        Post invalid protobuf object
        '''
        with open('staticfiles/testing/test_fb.pb', 'rb') as file_opened:
            seg_job = file_opened.read()
        model_id = PostSegmentationTestCase.model_version.model_version_id.replace(" ", "%20")
        post_response = self.client.post('/api/v2/Model/{}/segmentation'.format(model_id), \
            seg_job, \
            content_type='application/x-protobuf', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(post_response.status_code, 400, \
            msg='/api/v2/Model/{}/segmentation endpoint did not return 400 status code.'.format(\
                model_id))

    def test_get_progress_invalid_id(self):
        '''
        Test for endpoints: /api/v2/Model/{modelId}/segmentation/{segmentationId}
        Get invalid segmentation job id
        '''
        model_id = PostSegmentationTestCase.model_version.model_version_id.replace(" ", "%20")
        seg_id = "InvalidSegID"
        get_response = self.client.get('/api/v2/Model/{}/segmentation/{}'.format( \
            model_id, seg_id), \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(get_response.status_code, 400, \
            msg='/api/v2/Model/{}/segmentation/{} endpoint did not return 400 status code.'.format(\
                model_id, seg_id))

    def test_get_result_invalid_id(self):
        '''
        Test for endpoints: /api/v2/Model/{modelId}/segmentation/{segmentationId}
        Get invalid segmentation job id
        '''
        model_id = PostSegmentationTestCase.model_version.model_version_id.replace(" ", "%20")
        seg_id = "InvalidSegID"
        get_response = self.client.get('/api/v2/Model/{}/segmentation/{}/result'.format( \
            model_id, seg_id), \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(get_response.status_code, 400, \
            msg='/api/v2/Model/{}/segmentation/{} endpoint did not return 400 status code.'.format(\
                model_id, seg_id))

    def test_post_job_retrieve_results_protobuf(self):
        '''
        Test for endpoints:
            /api/v2/Model/{modelId}/segmentation
            /api/v2/Model/{modelId}/segmentation/{segmentationId}
            /api/v2/Model/{modelId}/segmentation/{segmentationId}/result

        Since database objects are not maintained between test cases, 3 end-points are tested
        here.
        Retrieve protobuf results
        '''

        #----------------------------------------------------------------------
        # Testing POST /api/v2/Model/{modelId}/segmentation
        #----------------------------------------------------------------------
        # Post job to temporary server
        model_id = PostSegmentationTestCase.model_version.model_version_id.replace(" ", "%20")
        post_response = self.client.post('/api/v2/Model/{}/segmentation'.format(model_id), \
            self.seg_job, \
            content_type='application/x-protobuf', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(post_response.status_code, 200, \
            msg='/api/v2/Model/{}/segmentation endpoint did not return 200 status code.'.format(\
                model_id))
        # Append orphaned segmentation job file path to path list for teardown.
        db_seg_path = SegmentationJob.objects.all()[0].model_input.path
        self.path_list.append(db_seg_path)
        # Parse protobuf message output
        seg_task = Model_pb2.SegmentationTask()
        seg_task.ParseFromString(post_response.content)
        seg_id = seg_task.SegmentationID

        #----------------------------------------------------------------------
        # Testing /api/v2/Model/{modelId}/segmentation/{segmentationId}
        #----------------------------------------------------------------------
        # Get progress from temporary server.  Since the test client is running with eager Celery
        # scheduling, it should always return 100% progress.
        get_response = self.client.get('/api/v2/Model/{}/segmentation/{}'.format( \
            model_id, seg_id), \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(get_response.status_code, 200, \
            msg='/api/v2/Model/{}/segmentation/{} endpoint did not return 200 status code.'.format(\
                model_id, seg_id))
        # Parse protobuf message output
        progress = Model_pb2.SegmentationProgress()
        progress.ParseFromString(get_response.content)
        self.assertEqual(progress.Progress, 100, \
            msg='/api/v2/Model/{}/segmentation/{} endpoint did not return 100% progress.'.format(\
                model_id, seg_id))
        # Append orphaned segmentation job file path to path list for teardown.
        db_results_path = SegmentationJob.objects.all()[0].model_output.path
        self.path_list.append(db_results_path)

        #----------------------------------------------------------------------
        # Testing /api/v2/Model/{modelId}/segmentation/{segmentationId}/result
        #----------------------------------------------------------------------
        seg_response = self.client.get('/api/v2/Model/{}/segmentation/{}/result'.format( \
            model_id, seg_id), \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(seg_response.status_code, 200, \
            msg='/api/v2/Model/{}/segmentation/{}/result endpoint did not return 200 status code.'\
            .format(model_id, seg_id))
        seg_result = Model_pb2.ModelOutput()
        seg_result.ParseFromString(seg_response.content)
        self.assertEqual(seg_result.ModelID, model_id.replace("%20"," "), \
            msg='/api/v2/Model/{}/segmentation/{}/result endpoint did not fetch correct result.'\
            .format(model_id, seg_id))

    def test_post_job_retrieve_results_json(self):
        '''
        Test for endpoints:
            /api/v2/Model/{modelId}/segmentation
            /api/v2/Model/{modelId}/segmentation/{segmentationId}
            /api/v2/Model/{modelId}/segmentation/{segmentationId}/result

        Since database objects are not maintained between test cases, 3 end-points are tested
        here.
        Retrieve JSON results
        '''

        #----------------------------------------------------------------------
        # Testing POST /api/v2/Model/{modelId}/segmentation
        #----------------------------------------------------------------------
        # Post job to temporary server
        model_id = PostSegmentationTestCase.model_version.model_version_id.replace(" ", "%20")
        post_response = self.client.post('/api/v2/Model/{}/segmentation'.format(model_id), \
            self.seg_job, \
            content_type='application/x-protobuf', \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(post_response.status_code, 200, \
            msg='/api/v2/Model/{}/segmentation endpoint did not return 200 status code.'.format(\
                model_id))
        # Append orphaned segmentation job file path to path list for teardown.
        db_seg_path = SegmentationJob.objects.all()[0].model_input.path
        self.path_list.append(db_seg_path)
        # Parse protobuf message output
        seg_task = Model_pb2.SegmentationTask()
        seg_task.ParseFromString(post_response.content)
        seg_id = seg_task.SegmentationID

        #----------------------------------------------------------------------
        # Testing /api/v2/Model/{modelId}/segmentation/{segmentationId}
        #----------------------------------------------------------------------
        # Get progress from temporary server.  Since the test client is running with eager Celery
        # scheduling, it should always return 100% progress.
        get_response = self.client.get('/api/v2/Model/{}/segmentation/{}'.format( \
            model_id, seg_id), \
            **{'HTTP_ACCEPT':'application/x-protobuf'})
        self.assertEqual(get_response.status_code, 200, \
            msg='/api/v2/Model/{}/segmentation/{} endpoint did not return 200 status code.'.format(\
                model_id, seg_id))
        # Parse protobuf message output
        progress = Model_pb2.SegmentationProgress()
        progress.ParseFromString(get_response.content)
        self.assertEqual(progress.Progress, 100, \
            msg='/api/v2/Model/{}/segmentation/{} endpoint did not return 100% progress.'.format(\
                model_id, seg_id))
        # Append orphaned segmentation job file path to path list for teardown.
        db_results_path = SegmentationJob.objects.all()[0].model_output.path
        self.path_list.append(db_results_path)

        #----------------------------------------------------------------------
        # Testing /api/v2/Model/{modelId}/segmentation/{segmentationId}/result
        #----------------------------------------------------------------------
        seg_response = self.client.get('/api/v2/Model/{}/segmentation/{}/result'.format( \
            model_id, seg_id), \
            **{'HTTP_ACCEPT':'application/json'})
        self.assertEqual(seg_response.status_code, 200, \
            msg='/api/v2/Model/{}/segmentation/{}/result endpoint did not return 200 status code.'\
            .format(model_id, seg_id))
        seg_result = seg_response.json()
        self.assertEqual(seg_result['ModelID'], model_id.replace("%20"," "), \
            msg='/api/v2/Model/{}/segmentation/{}/result endpoint did not fetch correct result.'\
            .format(model_id, seg_id))
