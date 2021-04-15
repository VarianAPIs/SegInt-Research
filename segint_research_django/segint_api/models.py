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

import uuid
import pytz
import ast

from google.protobuf.timestamp_pb2 import Timestamp
from protobuf import Model_pb2
from datetime import datetime


from django.db import models

MODELS_DIRECTORY = "../files/models/"

class Feedback(models.Model):
    '''
    Segmentation Feedback database model for segmentation API

    Fields:
        client_information - str - Contains client software version information.
        segmentation_id - str - The UUID for the segmentation job.
        segmentation_accepted - bool - Client-provided acceptance of segmentation results.
        general_comments - str - Client-provided comments
        general_score - float - Client-provided overall score.

    Related Fields:
        structure_comments - relationally added when parsing protobuf message.
    '''

    # Class Fields
    client_information = models.CharField(max_length=200)
    segmentation_id = models.CharField(max_length=200)
    segmentation_accepted = models.BooleanField()
    general_comments = models.TextField()
    general_score = models.FloatField(null=True)

    def pb_to_model(self, pb_str):
        '''
        Converts a protobuf message into attributes for the model.
        DoubleValues are just stored as their values within the database.

        Parameters:
        pb_str - (bytestring) - protobuf message to interpret into django db model

        Returns: none
        '''

        # Parse protobuf message
        feedback_pb = Model_pb2.SegmentationFeedback()
        feedback_pb.ParseFromString(pb_str)
        assert feedback_pb.IsInitialized(), \
            "Protobuf SegmentationFeedback model not initialized after parsing Protobuf input"

        # Assign class fields
        self.client_information = feedback_pb.ClientInformation.SoftwareVersion
        self.segmentation_id = feedback_pb.SegmentationID
        self.segmentation_accepted = feedback_pb.SegmentationAccepted
        self.general_comments = feedback_pb.GeneralComments
        self.general_score = None if feedback_pb.GeneralScore is None else \
            feedback_pb.GeneralScore.Value
        self.save()

        # Iterate through structure comments and add to database
        for struc_com in feedback_pb.StructureComments:
            self.structurecomment_set.create(
                structure_id=struc_com.StructureID,
                comments=struc_com.Comments,
                score=None if struc_com.Score is None else struc_com.Score.Value
                )


class StructureComment(models.Model):
    '''
    Structure Comment database model for segmentation API

    Fields:
        feedback - Related Feedback database entry.
        structure_id - str - Shared identifier for the structure.
        comments - str - Client-provided comments for the segmented structure.
        score - float - Client-provided score for the segmented structure.
    '''

    # Class Fields
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    structure_id = models.CharField(max_length=200)
    comments = models.TextField()
    score = models.FloatField(null=True)


class ModelFamily(models.Model):
    '''
    Model Family database model for segmentation API

    Fields:
        pb - File - File object representation of protobuf message location on disk.
           Generally, within the /media/ directory.
           See MEDIA_URL and MEDIA_ROOT in settings.py
        canonical_name - Model family canonical name
        language_code - RFC5646 language code
        name - Model family informal name
        description - Text description of the model Family
        clinical_domain - A concatenation of 2 character abbreviations of localized
            clinical domains
        anatomical_region - A localized string representing the primary anatomical region
            of images suitable for processing by this model family.
        primary_structure - The localized primary structure segmented by this model family.
        modalities - A concatenation of abbreviations of localized modalities used
            by this model family
    '''

    # Protobuf message file disk location
    pb = models.FileField(upload_to='modelfamily/', blank=True, null=True)

    # Top-level fields
    canonical_name = models.CharField(max_length=200, blank=True)
    language_code = models.CharField(max_length=200, blank=True)

    # Model Family Description
    name = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=200, blank=True)
    clinical_domain = models.CharField(max_length=200, blank=True)
    anatomical_region = models.CharField(max_length=200, blank=True)
    primary_structure = models.CharField(max_length=200, blank=True)
    modalities = models.CharField(max_length=200, blank=True)

    class GenderType(models.IntegerChoices):
        '''
        Django field enumeration for gender type.
        '''
        Male = 0
        Female = 1
        Any = 2

    # Model Constraints
    gender = models.IntegerField(choices=GenderType.choices, null=True, blank=True)

    def pb_to_model(self, pb_str):
        '''
        Converts a protobuf message into attributes for the model.
        DoubleValues are just stored as their values within the database.

        Parameters:
        pb_str - (bytestring) - protobuf message to interpret into django db model

        Returns: none
        '''
        model_family = Model_pb2.ModelFamily()
        model_family.ParseFromString(pb_str)

        # Protobuf top-level fields
        self.canonical_name = model_family.CanonicalName
        self.language_code = model_family.LanguageCode

        # Model family description
        self.name = model_family.FamilyDescription.Name
        self.description = model_family.FamilyDescription.Description
        self.clinical_domain = model_family.FamilyDescription.ClinicalDomain
        self.anatomical_region = model_family.FamilyDescription.AnatomicalRegion
        self.primary_structure = model_family.FamilyDescription.PrimaryStructure
        self.modalities = model_family.FamilyDescription.Modalities
        self.gender = model_family.FamilyDescription.Constraints.Gender

        # Model family constraints body parts examined
        for body_part in model_family.FamilyDescription.Constraints.BodyPartsExamined:
            self.bodypartexamined_set.create(
                part_type=body_part
                )

        # Model channel descriptions
        for model_channel in model_family.FamilyDescription.InputChannels:
            self.modelchanneldescription_set.create(
                channel_id=model_channel.ChannelID,
                spacing_min_x=model_channel.Constraints.SpacingMinInMillimeters.X,
                spacing_min_y=model_channel.Constraints.SpacingMinInMillimeters.Y,
                spacing_min_z=model_channel.Constraints.SpacingMinInMillimeters.Z,
                spacing_max_x=model_channel.Constraints.SpacingMaxInMillimeters.X,
                spacing_max_y=model_channel.Constraints.SpacingMaxInMillimeters.Y,
                spacing_max_z=model_channel.Constraints.SpacingMaxInMillimeters.Z,
                dimensions_min_x=model_channel.Constraints.DimensionsMinInPixels.X,
                dimensions_min_y=model_channel.Constraints.DimensionsMinInPixels.Y,
                dimensions_min_z=model_channel.Constraints.DimensionsMinInPixels.Z,
                dimensions_max_x=model_channel.Constraints.DimensionsMaxInPixels.X,
                dimensions_max_y=model_channel.Constraints.DimensionsMaxInPixels.Y,
                dimensions_max_z=model_channel.Constraints.DimensionsMaxInPixels.Z,
                req_original=model_channel.Constraints.OriginalDataRequired,
                is_axial=model_channel.Constraints.IsAxial,
                accepted_modalities_pb=model_channel.Constraints.AcceptedModalities
                )

        # Model Versions
        for model_version in model_family.ModelVersions:
            # Create model version in db
            db_mv = self.modelversion_set.create(
                model_version_id=model_version.ID,
                model_version_desc=model_version.VersionDescription,
                created_time=model_version.CreatedOn.ToDatetime().replace(tzinfo=pytz.utc),
                credits_req=model_version.NumberOfCreditsRequired,
                major_version=model_version.MajorVersion,
                minor_version=model_version.MinorVersion,
                language_code=model_version.LanguageCode
                )
            # Iterative add structures
            for struc in model_version.Structures:
                db_mv.structure_set.create(
                    name=struc.Name,
                    color_r=struc.Color.R,
                    color_g=struc.Color.G,
                    color_b=struc.Color.B,
                    structure_type=struc.Type,
                    FMA_code=struc.FMACode,
                    input_channel_id=struc.InputChannelID,
                    structure_id=struc.StructureID
                    )

    def model_to_pb(self, filename=None): # Not implemented
        '''
        Converts the db model into a protobuf message.

        Parameters: None

        Returns:
            m_f - protobuf message for a model family.
        '''
        m_f = Model_pb2.ModelFamily()

        # Protobuf top-level fields
        m_f.CanonicalName = self.canonical_name
        m_f.LanguageCode = self.language_code

        # Family Description fields
        m_f.FamilyDescription.Name = self.name
        m_f.FamilyDescription.Description = self.description
        m_f.FamilyDescription.ClinicalDomain = self.clinical_domain
        m_f.FamilyDescription.AnatomicalRegion = self.anatomical_region
        m_f.FamilyDescription.PrimaryStructure = self.primary_structure
        m_f.FamilyDescription.Modalities = self.modalities

        # Family Description Input Channels
        for chan_desc in self.modelchanneldescription_set.all():

            model_channel = Model_pb2.ModelChannelDescription()
            model_channel.ChannelID = chan_desc.channel_id

            for mode in ast.literal_eval(chan_desc.accepted_modalities_pb):
                model_channel.Constraints.AcceptedModalities.append(mode)

            model_channel.Constraints.OriginalDataRequired = chan_desc.req_original
            model_channel.Constraints.IsAxial = chan_desc.is_axial

            model_channel.Constraints.SpacingMinInMillimeters.X = chan_desc.spacing_min_x
            model_channel.Constraints.SpacingMinInMillimeters.Y = chan_desc.spacing_min_y
            model_channel.Constraints.SpacingMinInMillimeters.Z = chan_desc.spacing_min_z

            model_channel.Constraints.SpacingMaxInMillimeters.X = chan_desc.spacing_max_x
            model_channel.Constraints.SpacingMaxInMillimeters.Y = chan_desc.spacing_max_y
            model_channel.Constraints.SpacingMaxInMillimeters.Z = chan_desc.spacing_max_z

            model_channel.Constraints.DimensionsMinInPixels.X = chan_desc.dimensions_min_x
            model_channel.Constraints.DimensionsMinInPixels.Y = chan_desc.dimensions_min_y
            model_channel.Constraints.DimensionsMinInPixels.Z = chan_desc.dimensions_min_z

            model_channel.Constraints.DimensionsMaxInPixels.X = chan_desc.dimensions_max_x
            model_channel.Constraints.DimensionsMaxInPixels.Y = chan_desc.dimensions_max_y
            model_channel.Constraints.DimensionsMaxInPixels.Z = chan_desc.dimensions_max_z

            m_f.FamilyDescription.InputChannels.append(model_channel)

        # Family Description Constraint fields
        m_f.FamilyDescription.Constraints.Gender = self.gender
        for bpe in self.bodypartexamined_set.all():
            m_f.FamilyDescription.Constraints.BodyPartsExamined.append(bpe.part_type)

        # Model Version fields
        for m_v in self.modelversion_set.all():
            model_version = Model_pb2.ModelVersion()
            model_version.ID = m_v.model_version_id
            model_version.VersionDescription = m_v.model_version_desc

            timestamp = Timestamp()
            timestamp.FromDatetime(m_v.created_time)
            model_version.CreatedOn.seconds = timestamp.seconds
            model_version.CreatedOn.nanos = timestamp.nanos

            model_version.NumberOfCreditsRequired = m_v.credits_req
            model_version.MajorVersion = m_v.major_version
            model_version.MinorVersion = m_v.minor_version
            model_version.LanguageCode = m_v.language_code

            for m_struct in m_v.structure_set.all():
                model_structure = Model_pb2.Structure()
                model_structure.Name = m_struct.name
                model_structure.Color.R = m_struct.color_r
                model_structure.Color.G = m_struct.color_g
                model_structure.Color.B = m_struct.color_b
                model_structure.Type = m_struct.structure_type
                model_structure.FMACode = m_struct.FMA_code
                model_structure.InputChannelID = m_struct.input_channel_id
                model_structure.StructureID = m_struct.structure_id

                model_version.Structures.append(model_structure)

            m_f.ModelVersions.append(model_version)

        return m_f

class BodyPartExamined(models.Model):
    '''
    Bodypart Examined database model for segmentation API

    Fields:
        model_family - Related Model Family database entry.
        part_type - Enumerated Integer choice. See BodyPartExaminedType
    '''

    class BodyPartExaminedType(models.IntegerChoices):
        '''
        Django field enumeration for body part examined type.
        '''
        Abdomen = 0
        AbdomenPelvis = 1
        Adrenal = 2
        Ankle = 3
        Aorta = 4
        Axilla = 5
        Back = 6
        Bladder = 7
        Brain = 8
        Breast = 9
        Bronchus = 10
        Buttock = 11
        Calcaneus = 12
        Calf = 13
        Carotid = 14
        Cerebellum = 15
        Cspine = 16
        CtSpine = 17
        Cervix = 18
        Cheek = 19
        Chest = 20
        ChestAbdomen = 21
        ChestAbdomenPelvis = 22
        CircleOfWillis = 23
        Clavicle = 24
        Coccyx = 25
        Colon = 26
        Cornea = 27
        CoronaryArtery = 28
        Duodenum = 29
        Ear = 30
        Elbow = 31
        WholeBody = 32
        Esophagus = 33
        Extremity = 34
        Eye = 35
        Eyelid = 36
        Face = 37
        Femur = 38
        Finger = 39
        Foot = 40
        Gallbladder = 41
        Hand = 42
        Head = 43
        HeadNeck = 44
        Heart = 45
        Hip = 46
        Humerus = 47
        Ileum = 48
        Ilium = 49
        IAC = 50
        Jaw = 51
        Jejunum = 52
        Kidney = 53
        Knee = 54
        Larynx = 55
        Liver = 56
        Leg = 57
        LSpine = 58
        LSSpine = 59
        Lung = 60
        Maxilla = 61
        Mediastinum = 62
        Mouth = 63
        Neck = 64
        NeckChest = 65
        NeckChestAbdomen = 66
        NeckChestAbdomenPelvis = 67
        Nose = 68
        Orbit = 69
        Ovary = 70
        Pancreas = 71
        Parotid = 72
        Patella = 73
        Pelvis = 74
        Penis = 75
        Pharynx = 76
        Prostate = 77
        Rectum = 78
        Rib = 79
        SSPine = 80
        Scalp = 81
        Scapula = 82
        Sclera = 83
        Scrotum = 84
        Shoulder = 85
        Skull = 86
        Spine = 87
        Spleen = 88
        Sternum = 89
        Stomach = 90
        SumMandibular = 91
        TMJoint = 92
        Testis = 93
        Thigh = 94
        TSpine = 95
        TLSpine = 96
        Thumb = 97
        Thymus = 98
        Thyroid = 99
        Toe = 100
        Tongue = 101
        Trachea = 102
        Arm = 103
        Ureter = 104
        Urethra = 105
        Uterus = 106
        Vagina = 107
        Vulva = 108
        Wrist = 109
        Zygoma = 110

    model_family = models.ForeignKey(ModelFamily, on_delete=models.CASCADE, \
        null=True)
    part_type = models.IntegerField(choices=BodyPartExaminedType.choices, \
        blank=True, null=True)

class ModelChannelDescription(models.Model):
    '''
    Model Channel Description database model for segmentation API

    Fields:
        model_family - Related Model Family database entry
        channel_id - Unique id for the channel
        spacing_min: Minimum spacing channel constraints, _x, _y, _z
        spacing_max: Maximum spacing channel constraints, _x, _y, _z
        dimensions_min: Minimum dimensions channel constraints, _x, _y, _z
        dimensions_max: Maximum dimensions channel constraints, _x, _y, _z
        req_original - Boolean field for requiring the original
        is_axial - Boolean field for axial information
        accepted_modalities_pb - Text field for the pb message
    '''

    model_family = models.ForeignKey(ModelFamily, on_delete=models.CASCADE, \
        null=True)

    channel_id = models.CharField(max_length=200, blank=True)

    spacing_min_x = models.FloatField(default=0)
    spacing_min_y = models.FloatField(default=0)
    spacing_min_z = models.FloatField(default=0)
    spacing_max_x = models.FloatField(default=0)
    spacing_max_y = models.FloatField(default=0)
    spacing_max_z = models.FloatField(default=0)

    dimensions_min_x = models.FloatField(default=0)
    dimensions_min_y = models.FloatField(default=0)
    dimensions_min_z = models.FloatField(default=0)
    dimensions_max_x = models.FloatField(default=0)
    dimensions_max_y = models.FloatField(default=0)
    dimensions_max_z = models.FloatField(default=0)

    req_original = models.BooleanField(default=True)
    is_axial = models.BooleanField(default=True)

    accepted_modalities_pb = models.CharField(max_length=1000, null=True)

class ModelVersion(models.Model):
    '''
    Model Version database model for the segmentation API

    Fields:
        model_family - Related Model Family database entry.
        model_version_id - Unique Identifier for the model
        model_version_desc - A localized description of this version of the model
        model_file - Localized file containing relevant model file
        model_module - Localized file containing support classes for the model
        model_type - Descriptor of ML library for the model e.g. PyTorch, Tensorflow
        created_time - DateTime when the model was created
        credits_req - Number of credits required to execute this model
        major_version - The major version of this model
        minor_version - The minor version of this model
        language_code - The RFC5646 language code of the translation of this ModelVersion
    '''

    class ModelVersionType(models.IntegerChoices):
        '''
        Django field enumeration for body part examined type.
        '''
        Phantom = 0
        Pytorch = 1
        Tensorflow = 2

    model_family = models.ForeignKey(ModelFamily, on_delete=models.CASCADE, \
        null=True)
    model_version_id = models.CharField(max_length=200, null=True)
    model_version_desc = models.CharField(max_length=200, null=True)
    model_file = models.FileField(upload_to='models/', null=True, blank=True)
    model_module = models.FileField(upload_to='models/', null=True, blank=True)
    model_type = models.IntegerField(choices=ModelVersionType.choices, \
        blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    credits_req = models.FloatField(default=0.0)
    major_version = models.IntegerField(default=0)
    minor_version = models.IntegerField(default=0)
    language_code = models.CharField(max_length=200, default='en')

class Structure(models.Model):
    '''
    Structure database model for segmentation API

    Fields:
        model_version - Related Model Version database entry.
        name - Localized name of the structure.
        color_r, _g, _b - Color of the structure.
        structure_type - The type of the structure.
        FMA_code - The unique FMA (Foundational Model of Anatomy) code for this
            structure.
        input_channel_id - The input channel identifier this structure is linked to.
        structure_id - The unique identifier for this structure.
    '''
    class StructureType(models.IntegerChoices):
        '''
        Django field enumeration for structure type.
        '''
        External = 0
        Organ = 1
        Unknown = 2

    model_version = models.ForeignKey(ModelVersion, on_delete=models.CASCADE, \
        null=True)
    name = models.CharField(max_length=200)
    color_r = models.IntegerField(default=0)
    color_g = models.IntegerField(default=0)
    color_b = models.IntegerField(default=0)
    structure_type = models.IntegerField(choices=StructureType.choices, \
        null=True, blank=True)
    FMA_code = models.IntegerField(default=0)
    input_channel_id = models.CharField(max_length=200)
    structure_id = models.CharField(max_length=200)

    def model_to_pb(self):
        '''
        Converts the db model into a protobuf message.

        Parameters: None

        Returns: 
            structure - protobuf message for a structure.
        '''
        structure = Model_pb2.Structure()
        structure.Name = self.name
        structure.Color.R = self.color_r
        structure.Color.G = self.color_g
        structure.Color.B = self.color_b
        structure.Type = self.structure_type
        structure.FMACode = self.FMA_code
        structure.InputChannelID = self.input_channel_id
        structure.StructureID = self.structure_id
        return structure

class SegmentationJob(models.Model):
    '''
    Segmentation Task database model for segmentation API

    Fields:
        segmentation_id - UUID - Internal ID for segmentation job.
        model_id - str - ID for requested model
        model_input - File - File object representation of input protobuf message location on disk.
            Generally, within the /media/segmentation directory.
            See MEDIA_URL and MEDIA_ROOT in settings.py
        time_field - datetime - Generated upon job instantiation to record start date/time.
        model_ouput - File - File object representation of output protobuf message location on disk.
            Field is empty until job is completed.
    '''

    # Class Fields
    segmentation_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    model_id = models.CharField(max_length=60)
    model_input = models.FileField(upload_to='segmentation/')
    time_field = models.DateTimeField(blank=True, null=True, unique=True)
    model_output = models.FileField(upload_to='results/', blank=True)
    error = models.CharField(max_length=60, blank=True, null=True)

    def get_task_response(self):
        '''
        Generates Segmentation Task response protobuf message from the stored Segmentation Job.

        Parameters: none

        Returns:
            response - Model_pb2.SegmentationTask - Protobuf Segmentation Task object ready for
            serialization.
        '''
        timestamp = Timestamp()
        timestamp.FromDatetime(self.time_field)
        response = Model_pb2.SegmentationTask()
        response.SegmentationID = str(self.segmentation_id)
        response.StartTime.seconds = timestamp.seconds
        response.StartTime.nanos = timestamp.nanos
        return response

    def get_job_progress(self):
        '''
        Generates Segmentation Progress response protobuf message from the stored Segmentation Job.

        Parameters: none

        Returns:
            response - Model_pb2.Segmentationprogress - Protobuf Segmentation Progress object.
        '''
        response = Model_pb2.SegmentationProgress()
        if self.model_output != "":
            # 100 progress
            response.Progress = 100
            response.Errors = ""
            response.ErrorCode = 0
            return response
        # Mock response with 0 progress
        response.Progress = 0
        response.Errors = ""
        response.ErrorCode = 0
        return response
    ## REMINDER: For error cases, add enum ErrorCode.Value



class SegmentationTelemetry(models.Model):
    '''
    Segmentation Telemetry database model for segmentation API

    Fields:
        client_software_version - str - Software version for Velocity client
        upload_time_ms - int - Upload time in ms
        segmentation_wait_ms - int - segmentation time in ms
        segmentation_down_ms - int - segmentation result download time in ms
        segmentation_retries - int - number of retries for segmentation job
        segmentation_model_id - str - segmentation task model ID
        segmentation_id - str - segmentation task ID
        client_error - enum - error enumeration for the client software
        client_error_info - str - verbose HTML info for errors
    '''

    # Class Fields
    client_software_version = models.CharField(max_length=200)
    upload_time_ms = models.IntegerField()
    segmentation_wait_ms = models.IntegerField()
    segmentation_down_ms = models.IntegerField()
    segmentation_retries = models.IntegerField()
    segmentation_model_id = models.CharField(max_length=200)
    segmentation_id = models.CharField(max_length=200)
    client_error = models.IntegerField()
    client_error_info = models.TextField()

    def pb_to_model(self, pb_str):
        '''
        Converts a protobuf message into attributes for the model.
        DoubleValues are just stored as their values within the database.

        Parameters:
        pb_str - (bytestring) - protobuf message to interpret into django db model

        Returns: none
        '''

        # Parse protobuf message
        telemetry_pb = Model_pb2.SegmentationTelemetry()
        telemetry_pb.ParseFromString(pb_str)
        assert telemetry_pb.IsInitialized(), \
            "Protobuf SegmentationTelemetry model not initialized after parsing Protobuf input"

        # Assign class fields
        self.client_software_version = telemetry_pb.ClientInformation.SoftwareVersion
        self.upload_time_ms = telemetry_pb.UploadTimeInMilliseconds
        self.segmentation_wait_ms = telemetry_pb.SegmentationWaitInMilliseconds
        self.segmentation_down_ms = telemetry_pb.SegmentationDownloadInMilliseconds
        self.segmentation_retries = telemetry_pb.NumberOfRetries
        self.segmentation_model_id = telemetry_pb.ModelID
        self.segmentation_id = telemetry_pb.SegmentationID
        self.client_error = telemetry_pb.ClientError
        self.client_error_info = telemetry_pb.ClientErrorInformation
