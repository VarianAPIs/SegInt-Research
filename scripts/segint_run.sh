# Copyright 2021 Varian Medical Systems, Inc.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
# and associated documentation files (the "Software"), to deal in the Software without 
# restriction, including without limitation the rights to use, copy, modify, merge, publish, 
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or 
# substantial portions of the Software.
# The Software shall be used for non-clinical use only and shall not be used to enable, provide, 
# or support patient treatment. "Non-clinical" or "non-clinical use" means usage not involving: 
# (i) the direct observation of patients; (ii) the diagnoses of disease or other conditions in 
# humans or other animals; or (iii) the cure, mitigation, therapy, treatment, treatment planning,
# or prevention of disease in humans or other animals to affect the structure or function thereof.  
# The Software is NOT U.S. FDA 510(k) cleared for use on humans and shall not be used on humans.
# Any use of the Software outside of its intended use (“off-label”) could lead to physical harm
# or death of patients. 
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING 
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY NON-CLINICAL OR OFF-LABEL 
# USE OF THE SOFTWARE AND ANY PERSON THAT USES, COPIES, MODIFIES, MERGES, PUBLISHES, DISTRIBUTES, 
# SUBLICENSES, AND/OR SELLS COPIES OF THE SOFTWARE UNDER THIS PERMISSION NOTICE HEREBY AGREES TO 
# INDEMNIFY AND HOLD HARMLESS THE AUTHORS AND COPYRIGHT HOLDERS FOR ANY LIABILITY, DEMAND, DAMAGE,
# COST OR EXPENSE ARISING FROM OR RELATING TO SUCH NON-CLINICAL OR OFF-LABEL USE OF THE SOFTWARE.

#!/bin/bash
# A Simple Shell Script To Run All Necessary Child Instances of the ATS service
# 08/05/2020

# Activate virtual environment
source segint_venv/bin/activate
cd segint_research_django/

# Run server using local ip, with necessary celery threads
python manage.py runserver 0.0.0.0:8000 &
celery -A segint_research_django worker -l info &
celery -A segint_research_django beat -l info