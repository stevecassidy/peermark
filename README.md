# README #

This project provides a web application to allow students to peer-mark 
HTML web design assignments.  Student authenticate and are shown up to
20 randomly selected submissions from other students and can mark them. 
Students can also preview their own work. 


## Running

This is a Python server side application.  Install the required packages with:

```
pip install -r requirements.txt
```

The application can then be run as:

```
python main.py
```

### Admin Login

There is an admin user with the username 'admin' and a password stored in the environment 
variable `ADMIN_PASSWORD`.   If the environment variable is not set then no admin login will 
be possible.

### Importing student submissions

The assumption behind this application is that students submit a zip file containing a file 
`index.html` and any associated files needed to display it (css, images etc).  These are 
uploaded to an iLearn assignment submission and then the unit staff download all submissions
as a zip file (a zip file containing many zip files).  

The script `importsubmissions.py` unpacks the zip file downloaded from iLearn and populates
the database.  The script also requires a CSV file containing student details 
(email, Student ID), this can be downloaded from the iLearn assignment page.  The third argument
to this script is the directory that the submissions will be unpacked into. Eg. 

```
python importsubmissions.py "COMP249_FHFYR_2019_ALL-Assignment Web Design-5019016.zip" "Grades-COMP249_FHFYR_2019_ALL-Assignment Web Design--5019016.csv" submissions
```

The script will create a folder in the target directory named for the student id
containing the unpacked submission.

Note that the script knows how to unpack zip files and some other archive formats but
can get stuck if students have uploaded something odd.  It will show a message at 
the end of the run for any problem files.   To resolve this you can try to manually unpack
the failed submission into the target folder (the failed file will have been copied there). 
If you then re-run the script it will not try to unpack the files a second time if it
sees that they are already there and the failed files will be properly ingested. 

Once the submissions have been imported, students can login with their email and student
id and begin marking submissions.  

