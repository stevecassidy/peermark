# README

This project provides a web application to allow students to peer-mark 
HTML web design assignments.  Student authenticate and are shown up to
20 randomly selected submissions from other students and can mark them. 
Students can also preview their own work. 

## Running

This is a Python server side application.  Install the required packages with:

```bash
pip install -r requirements.txt
```

To initialise the database run:

```bash
python database.py
```

(this can also be run at any time to reset the database to a blank state).

The application can then be run as:

```bash
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

```bash
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

### Importing from Github Classroom

If the students are using Github Classroom then the import process is slightly different.

First use the Github Classroom Desktop tool to export all repositories.  Then, download
the grading file from the Github Classroom assignment (Green Download button, select download
grades).

If you wish to add a password for each student, add a column `password` to the CSV file before
running the import script.

Now run:

```bash
python ./import-github.py web-portal-design-grades-1679872201.csv Web\ Portal\ Design-03-27-2023-07-13-27/
```

Any student who has no commits will be left out. Similarly any Github ID that doesn't have a student
email will be left out.

You can re-run this later after adding missing students, existing entries will not be modified.
