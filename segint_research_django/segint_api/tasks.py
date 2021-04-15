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
import os
import sys
import importlib
import inspect
import gzip
import warnings
# This is a hack. Tensorflow and numpy versions disagree
# TODO: rectify tf and np versions
warnings.filterwarnings('ignore', category=FutureWarning)

from io import BytesIO

# Utility imports
from celery.decorators import task
from celery.utils.log import get_task_logger
from django.core.files import File
import numpy as np

# Local imports
from protobuf import Model_pb2, Primitives3D_pb2
from segint_api.models import SegmentationJob, ModelVersion, Structure

# ML imports
import torch
import tensorflow as tf
from tensorflow import keras

logger = get_task_logger(__name__)

@task(name="start_pytorch_segmentation_single_structure")
def start_pytorch_segmentation_single_structure(model_id, job_id):
    '''
    Single structure pytorch segmentation.

    Parameters:
        model_id - str - Model ID to use for segmentation job
        job_id - str - Segmentation job ID
    Returns: None
    '''
    logger.info("\nStarting Pytorch with job_id {} and model_id {}".format(job_id, model_id))

    # Find the job
    try:
        seg_job = SegmentationJob.objects.get(model_id=model_id, segmentation_id=job_id)
        m_v = ModelVersion.objects.filter(model_version_id=model_id)[0]
        structure = Structure.objects.filter(model_version=m_v)[0]
    except:
        logger.info("\nCan't find job!")
        return

    # Segmentation schema.  See helper functions below for details
    model_in = acquire_model_input(seg_job)
    channels_data = parse_model_in(model_in)
    segment_result = volumetric_pytorch_segment(m_v, channels_data)
    model_out = construct_model_out(m_v, structure, segment_result)
    save_to_disk(seg_job, model_out)

@task(name='start_tensorflow_segmentation_single_structure')
def start_tensorflow_segmentation_single_structure(model_id, job_id):
    '''
    Single structure pytorch segmentation.

    Parameters:
        model_id - str - Model ID to use for segmentation job
        job_id - str - Segmentation job ID
    Returns: None
    '''
    logger.info("\nStarting Tensorflow with job_id {} and model_id {}".format(job_id, model_id))

    # Find the job
    try:
        seg_job = SegmentationJob.objects.get(model_id=model_id, segmentation_id=job_id)
        m_v = ModelVersion.objects.filter(model_version_id=model_id)[0]
        structure = Structure.objects.filter(model_version=m_v)[0]
    except:
        logger.info("\nCan't find job!")
        return

    # Segmentation schema.  See helper functions below for details
    model_in = acquire_model_input(seg_job)
    channels_data = parse_model_in(model_in)
    segment_result = volumetric_tensorflow_segment(m_v, channels_data)
    model_out = construct_model_out(m_v, structure, segment_result)
    save_to_disk(seg_job, model_out)


@task(name="start_phantom_segmentation")
def start_phantom_segmentation(model_id, job_id, seg_jobb=None):
    '''
    Single structure phantom segmentation.  Generates centered rectangular prism structure.

    Parameters:
        model_id - str - Model ID to use for segmentation job
        job_id - str - Segmentation job ID
    Returns: None
    '''
    logger.info("\nStarting phantom segmentation with job_id {} and model_id {}".format(job_id, \
        model_id))

    # Find the job
    seg_job = SegmentationJob.objects.get(model_id=model_id, segmentation_id=job_id)
    m_v = ModelVersion.objects.filter(model_version_id=model_id)[0]
    structure = Structure.objects.filter(model_version=m_v)[0]

    # Segmentation schema.  See helper functions below for details
    model_in = acquire_model_input(seg_job)
    channels_data = parse_model_in(model_in)
    segment_result = mock_segment(channels_data)
    model_out = construct_model_out(m_v, structure, segment_result)
    save_to_disk(seg_job, model_out)


# ----------------------------------------------------------------------------------
# Segmentation Standard Helper Functions
# The following details a schema for all extensible segmentation tasks.
#   1. Acquire job model input
#   2. Parse job model_input as channel data
#   3. Model evaluation/segmentation upon channel data
#   4. Construct model output using segmentation results
#   5. Save to disk.
# ----------------------------------------------------------------------------------

def acquire_model_input(seg_job):
    '''
    Acquires the ModelInput protobuf message object from the corresponding
    segmentation job.

    Parameters:
        seg_job - django.db.SegmentationJob - Django model for a segmentation
            job.
    Returns:
        model_in - ModelInput.pb - Protobuf message object for the model input
    '''
    file_path = open(seg_job.model_input.path, 'rb')
    file_input = file_path.read()
    file_path.close()
    model_in = Model_pb2.ModelInput()
    model_in.ParseFromString(file_input)
    return model_in


def parse_model_in(model_in):
    '''
    Parses model input channels from provided ModelInput protobuf object.

    Parameters:
        model_in - ModelInput.pb - Protobuf message object for the model input
    Returns:
        channels_data - [ndarray] - List of channel data in ndarray form.
    '''
    channels_data = []
    for in_channel in model_in.Channels:
        channel_calibrated_volume = in_channel.CalibratedVolume
        channel_volume = channel_calibrated_volume.Volume
        volume_width = channel_volume.Width
        volume_height = channel_volume.Height
        volume_depth = channel_volume.Depth
        volume_data = channel_volume.Data
        gzip_volume = gzip.GzipFile(fileobj=BytesIO(volume_data)).read()
        loaded_np = np.frombuffer(gzip_volume, \
            dtype=np.int16).reshape((volume_depth, volume_height, volume_width))
        channels_data.append(loaded_np)
    return channels_data


def mock_segment(channels_data):
    '''
    Mock segmentation function for generating centered rectangular prism
    for testing purposes.

    Parameters:
        channels_data - [ndarray] - List of channel data in ndarray form
    Returns:
        segment_result - [ndarray] - List of output channel data in ndarray form
    '''
    segment_result = []
    for channel_data in channels_data:
        channel_shape = channel_data.shape
        fake_out = np.zeros(channel_shape, dtype=np.byte)
        depth, height, width = channel_shape
        fake_out[int(depth/4):3*int(depth/4), \
            int(height/2-30):int(height/2+30), \
            int(width/2-30):int(width/2+30)] += 1
        segment_result.append(fake_out)
    return segment_result


def construct_model_out(m_v, structure, segment_result):
    '''
    Construct ModelOutput protobuf message object using segmentation results.

    Parameters:
        m_v - django.db.ModelVersion - Database model entry for model version
        structure - django.db.Structure - Databse model entry for the structure
            corresponding to the model version.
        segment_result - [ndarray] - List of output channel data in ndarray form
    Returns:
        model_out - ModelOutput.pb - Protobuf message object for the model output
    '''
    model_out = Model_pb2.ModelOutput()
    model_out.ModelID = m_v.model_version_id
    model_out.ProcesserVersion = "{}.{}".format(m_v.major_version, \
        m_v.minor_version)
    model_out.LanguageCode = m_v.language_code
    structure_pb = structure.model_to_pb()
    for result in segment_result:
        out_channel = Model_pb2.ModelOutputChannel()
        out_channel.Structure.CopyFrom(structure_pb)
        depth, height, width = result.shape
        out_channel.Volume.Width = width
        out_channel.Volume.Height = height
        out_channel.Volume.Depth = depth
        result_bytes = result.tobytes()
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode='w') as file_out:
            file_out.write(result_bytes)
        out_channel.Volume.Data = out.getvalue()
        out_channel.Volume.DataType = Primitives3D_pb2.VolumeData3D.DataTypes.Byte
        out_channel.Volume.CompressionMethod = 0
        model_out.Channels.append(out_channel)
    return model_out


def save_to_disk(seg_job, model_out):
    '''
    Converts segmentation job object into serialized protobuf message, stores on disk,
    and saves database entry model output to point to disk location.

    Parameters:
        seg_job - django.db.SegmentationJob - Django model for a segmentation
            job.
        model_out - ModelOutput.pb - Protobuf message object for the model output
    Returns:
        None
    '''
    response_data = bytes(model_out.SerializeToString())
    file_io = io.BytesIO(response_data)
    fname = "{}.pb".format("Result{}".format(seg_job.segmentation_id))
    seg_job.model_output.save(fname, File(file_io))


# ----------------------------------------------------------------------------------
# Segmentation Library Functions
# ----------------------------------------------------------------------------------

def volumetric_pytorch_segment(m_v, channels_data):
    '''
    Volumetric segmentation helper function for pytorch volumetric neural
    networks.

    Parameters:
        m_v - django.db.ModelVersion - Database model entry for model version
        channels_data - [ndarray] - List of channel data in ndarray form
    Returns:
        segment_result - [ndarray] - List of output channel data in ndarray form
    '''
    folder, module_name = os.path.split(m_v.model_module.path)
    module_name = module_name.split(".")[0]

    sys.path.append(folder+"/")
    mymodule = importlib.import_module(module_name)
    for i in dir(mymodule):
        attribute = getattr(mymodule, i)
        if inspect.isclass(attribute) or inspect.isfunction(attribute):
            setattr(sys.modules[__name__], i, attribute)

    torch_model = torch.load(m_v.model_file.path)
    torch_model.eval()
    segment_result = []
    for channel_data in channels_data:
        segment_result.append(torch_model(channel_data))
    return segment_result

def volumetric_tensorflow_segment(m_v, channels_data):
    '''
    Volumetric segmentation helper function for tensorflow volumetric neural
    networks.

    Parameters:
        m_v - django.db.ModelVersion - Database model entry for model version
        channels_data - [ndarray] - List of channel data in ndarray form
    Returns:
        segment_result - [ndarray] - List of output channel data in ndarray form
    '''
    tf_model = tf.keras.models.load_model(m_v.model_file.path)
    segment_result = []
    for channel_data in channels_data:
        segment_result.append(tf_model.evaluate(channel_data))
    return segment_result
