from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse,HttpResponseForbidden, JsonResponse
from django.contrib.auth.hashers import make_password,check_password
from .models import AdminDb,FacultyDb,StudentDb,Subject,FacultySubject,Department,Semester,Class,Division
import csv,io
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import AdminDb, FacultyDb, StudentDb, TimeTable, Class  # Ensure you have models for faculty and students
import pandas as pd
######################################## LOGIN AND REGISTRATION START ######################################################
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        fullname = request.POST.get("fullname")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")
        
        if AdminDb.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")
        
        user = AdminDb(username=username, fullname=fullname, password=password)
        user.save()
        
        messages.success(request, "User registered successfully!")
        return redirect("login")  
    
    return render(request, 'register.html')
def login(request):
    if request.method == 'POST':
        user_id = request.POST.get("id").strip()  # Strip spaces to avoid errors
        password = request.POST.get("password").strip()
        user_type = request.POST.get("user_type")

        try:
            # 🔹 Use the correct fields for each user type
            if user_type == 'admin':
                user = AdminDb.objects.get(username=user_id)  # Use 'username' for Admin
            elif user_type == 'faculty':
                user = FacultyDb.objects.get(facid=user_id)  # Use 'facid' for Faculty
            elif user_type == 'student':
                user = StudentDb.objects.get(studentid=user_id)  # Use 'studentid' for Student
            else:
                messages.error(request, "Invalid user type selected.")
                return redirect('login')

            # 🔹 Check password
            if password == user.password:  
                messages.success(request, "Login successful!")
                request.session['user_type'] = user_type
                request.session['id'] = user_id  
                request.session['full_name'] = user.fullname

                # 🔹 Redirect based on user type
                if user_type == 'admin':
                    return redirect('faculty')  
                elif user_type == 'faculty':
                    return redirect('profilefac')  
                elif user_type == 'student':
                    return redirect('profilestu')  
            else:
                messages.error(request, "Invalid username or password.")
        except (AdminDb.DoesNotExist, FacultyDb.DoesNotExist, StudentDb.DoesNotExist):
            messages.error(request, "User does not exist.")

    return render(request, 'login.html')

def logout(request):
    # Clear the session
    request.session.flush()  # This will clear all session data
    messages.success(request, "You have been logged out.")
    return redirect('login')  # Redirect to the login page
######################################## LOGIN AND REGISTRATION COMPLETE ######################################################

######################################## ADMINDB VIEWS START ######################################################
def faculty(request):
    if request.session.get('user_type') == 'admin':
        departments = Department.objects.all()
        return render(request, "Admin/faculty.html", {"departments": departments})
    else:
        messages.error(request, "You are not authorized to access this page.")
        return redirect('login')

def upload_faculty(request):
    if request.method == 'POST' and request.FILES.get('faculty_file'):
        faculty_file = request.FILES['faculty_file']
        department_code = request.POST.get('department')

        if not department_code:
            messages.error(request, "Department is missing.")
            return redirect('faculty')

        try:
            department = Department.objects.get(code=department_code)
        except Department.DoesNotExist:
            messages.error(request, "Invalid department selected.")
            return redirect('faculty')

        # Save file
        fs = FileSystemStorage()
        filename = fs.save(f'uploads/{department.code}/{faculty_file.name}', faculty_file)
        uploaded_file_url = fs.url(filename)

        # Read the uploaded file
        try:
            if faculty_file.name.endswith('.csv'):
                df = pd.read_csv(faculty_file)
            elif faculty_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(faculty_file)
            else:
                messages.error(request, "Invalid file format. Upload CSV or Excel.")
                return redirect('faculty')
        except Exception as e:
            messages.error(request, f"File error: {str(e)}")
            return redirect('faculty')

        # Validate Required Columns
        required_columns = {'facid', 'fullname', 'password'}
        if not required_columns.issubset(df.columns):
            messages.error(request, "Invalid file structure. Must contain: facid, fullname, password.")
            return redirect('faculty')

        # Save to FacultyDb
        for _, row in df.iterrows():
            FacultyDb.objects.create(
                id=row['facid'],
                fullname=row['fullname'],
                password=row['password'],  # Hash this in production
                Dept=department
            )

        messages.success(request, f"Faculty uploaded successfully for {department.name.upper()}.")
        return render(request, 'Admin/faculty.html', {
            'uploaded_file': {'url': uploaded_file_url, 'name': faculty_file.name},
            "departments": Department.objects.all()
        })

    return redirect('faculty')

def faculty_registration(request):
    departments = Department.objects.all()
    return render(request, 'Admin/faculty.html', {"departments": departments})
#---------------------------------------------------------------------------------------#
def student(request):
    return render(request,"Admin/student.html")
def upload_students(request):
    uploaded_file_url = None
    if request.method == "POST" and request.FILES.get("student_file"):
        student_file = request.FILES["student_file"]

        # Save the file temporarily
        fs = FileSystemStorage()
        filename = fs.save(f"uploads/{student_file.name}", student_file)
        file_path = fs.path(filename)
        uploaded_file_url = fs.url(filename)

        try:
            # Read the uploaded file (CSV or Excel)
            if student_file.name.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif student_file.name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file_path)
            else:
                messages.error(request, "Invalid file format. Please upload a CSV or Excel file.")
                return redirect("upload_students")

            # Check required columns
            required_columns = {"Student ID", "Full Name", "Department", "Semester", "Division", "Password"}
            if not required_columns.issubset(df.columns):
                messages.error(request, "File must have columns: Student ID, Full Name, Department, Semester, Division, Password")
                return redirect("upload_students")

            # Process the data
            for _, row in df.iterrows():
                student_id = row["Student ID"].strip()
                full_name = row["Full Name"].strip()
                department_name = row["Department"].strip()
                semester = str(row["Semester"]).strip()
                division = str(row["Division"]).strip()
                raw_password = row["Password"].strip()  # Password in plain text

                # 🔹 Ensure department exists (No Creation, Only Lookup)
                department = Department.objects.filter(code__iexact=department_name).first()
                if not department:
                    messages.error(request, f"Department '{department_name}' not found. Skipping student '{full_name}'.")
                    continue  # Skip this row if department is missing

                # 🔹 Get or create the student record
                student, created = StudentDb.objects.get_or_create(
                    id=student_id,
                    defaults={
                        "fullname": full_name,
                        "password": raw_password,  # 🔹 Save as plain text
                        "Dept": department.name,  # Store department name
                        "sem": semester,
                        "div": division,
                    },
                )

                # 🔹 Update student if already exists
                if not created:
                    student.fullname = full_name
                    student.password = raw_password  # 🔹 Update password
                    student.Dept = department.name
                    student.sem = semester
                    student.div = division
                    student.save()

            messages.success(request, "Students uploaded successfully.")
            return redirect("upload_students")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect("upload_students")

    return render(request, "Admin/student.html",{"uploaded_file_url": uploaded_file_url})
#---------------------------------------------------------------------------------------#
def subject(request):
    return render(request,"Admin/subject.html")

def upload_subjects(request):
    if request.method == "POST" and request.FILES.get("subject_file"):
        subject_file = request.FILES["subject_file"]

        # Save the file temporarily
        fs = FileSystemStorage()
        filename = fs.save(f"uploads/{subject_file.name}", subject_file)
        file_path = fs.path(filename)

        try:
            # Read the uploaded file (CSV or Excel)
            if subject_file.name.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif subject_file.name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file_path)
            else:
                messages.error(request, "Invalid file format. Please upload a CSV or Excel file.")
                return redirect("upload_subjects")

            # Check required columns
            required_columns = {"Subject", "Subject Code", "Department", "Semester", "Faculty IDs"}
            if not required_columns.issubset(df.columns):
                messages.error(request, "File must have columns: Subject, Subject Code, Department, Semester, Faculty IDs")
                return redirect("upload_subjects")

            # Process the data
            for _, row in df.iterrows():
                subject_name = row["Subject"].strip()
                subject_code = row["Subject Code"].strip()
                department_code = row["Department"].strip().lower()  # Department column contains the department code
                semester_number = int(row["Semester"])
                faculty_ids = row["Faculty IDs"].split(",")  # Split faculty IDs

                # Get the department using the department code (case insensitive)
                department = Department.objects.filter(code__iexact=department_code).first()
                if not department:
                    messages.error(request, f"Department with code '{department_code}' not found. Skipping subject '{subject_name}'.")
                    continue  # Skip this row if department is missing

                # Get or create the semester
                semester, _ = Semester.objects.get_or_create(number=semester_number)

                # Get or create two classes (Div A & B)
                division_a, _ = Division.objects.get_or_create(name="A")
                division_b, _ = Division.objects.get_or_create(name="B")

                class_a, _ = Class.objects.get_or_create(department=department, semester=semester, division=division_a)
                class_b, _ = Class.objects.get_or_create(department=department, semester=semester, division=division_b)

                # Create subject with subject code and assign it to both classes
                subject_a, _ = Subject.objects.get_or_create(name=subject_name, code=subject_code, class_info=class_a)
                subject_b, _ = Subject.objects.get_or_create(name=subject_name, code=subject_code, class_info=class_b)

                # Assign faculty members
                for fac_id in faculty_ids:
                    fac_id = fac_id.strip()
                    faculty = FacultyDb.objects.filter(facid=fac_id).first()
                    if faculty:
                        FacultySubject.objects.get_or_create(faculty=faculty, subject=subject_a)
                        FacultySubject.objects.get_or_create(faculty=faculty, subject=subject_b)
                    else:
                        messages.warning(request, f"Faculty ID {fac_id} not found, skipping.")

            messages.success(request, "Subjects and faculty assignments uploaded successfully.")
            return redirect("upload_subjects")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect("upload_subjects")

    return render(request, "Admin/subject.html")
#---------------------------------------------------------------------------------------#
def timetable(request):
    classes = Class.objects.all()
    return render(request, "Admin/timetable.html", {"classes": classes})

def save_timetable(request):
    if request.method == "POST" and request.FILES.get("timetable_file"):
        uploaded_file = request.FILES["timetable_file"]
        class_id = request.POST.get("class_info")

        # Validate class selection
        try:
            class_info = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            messages.error(request, "Selected class does not exist.")
            return redirect("timetable")

        try:
            # Read the Excel file
            df = pd.read_excel(uploaded_file)

            # Check required columns
            required_columns = {"Day", "Period", "Subject Code", "Faculty ID"}
            if not required_columns.issubset(df.columns):
                messages.error(request, "Invalid file format. Please follow the given structure.")
                return redirect("timetable")

            # Process each row in the file
            for index, row in df.iterrows():
                day = row["Day"]
                period = row["Period"]
                subject_code = row["Subject Code"]
                faculty_id = row["Faculty ID"]

                # Fetch subject and faculty
                try:
                    subject = Subject.objects.get(code=subject_code)
                    faculty = FacultyDb.objects.get(facid=faculty_id)

                    # Save to Timetable model
                    TimeTable.objects.create(
                        class_info=class_info,
                        day=day,
                        period=period,
                        subject=subject,
                        faculty=faculty
                    )
                except Subject.DoesNotExist:
                    messages.error(request, f"Subject {subject_code} not found.")
                except FacultyDb.DoesNotExist:
                    messages.error(request, f"Faculty {faculty_id} not found.")

            messages.success(request, "Timetable uploaded successfully!")
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")

    return redirect("timetable")
######################################## ADMINDB VIEWS COMPLETE ######################################################
######################################## FACULTY VIEWS START ######################################################
def profilefac(request):
    """Faculty Profile View"""
    if request.session.get('user_type') == 'faculty':
        faculty_id = request.session.get('id')
        try:
            faculty = FacultyDb.objects.get(facid=faculty_id)
            return render(request, 'Faculty/profilefac.html', {
                'fullname': faculty.fullname,
                'facultyid': faculty.facid,
                'department': faculty.department if faculty.department else "N/A",

            })
        except FacultyDb.DoesNotExist:
            messages.error(request, "Faculty profile not found.")
            return redirect('login')
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')
#---------------------------------------------------------------------------------------#
######################################## FACULTY VIEWS COMPLETE ######################################################
######################################## STUDENT VIEWS START ######################################################
def profilestu(request):
    """Student Profile View"""
    if request.session.get('user_type') == 'student':
        student_id = request.session.get('id')
        try:
            student = StudentDb.objects.get(studentid=student_id)
            return render(request, 'Student/profilestu.html', {
                'fullname': student.fullname,
                'studentid': student.studentid,
                'department': student.department.name.upper() if student.department else "N/A",
                'semester': student.semester,
                'division': student.division
            })
        except StudentDb.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('login')
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')
#---------------------------------------------------------------------------------------#
def stutimetable(request):
    return render(request,"Student/stutimetable.html")
#---------------------------------------------------------------------------------------#
def stuattendance(request):
    return render(request,"Student/stuattendance.html")
######################################## STUDENT VIEWS COMPLETE ######################################################
