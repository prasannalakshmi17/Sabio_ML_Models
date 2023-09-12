import cv2
import pytesseract
import re
import psycopg2
import json
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Set up PostgreSQL connection
connection = psycopg2.connect(
    database="postgres",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cursor = connection.cursor()

# Load the medical report image
image = cv2.imread("medical report.png")

# Convert the image to grayscale
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply thresholding to binarize the image
thresholded_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)[1]

# Extract the text from the largest contour
text = pytesseract.image_to_string(thresholded_image, lang="eng")

def header(lines):
    header = []
    for line in lines:
        match = re.search(r"ARMED|Dhaka Cantonment Bangladesh|Recipient|Tel:|Fax|HAEMATOLOGY REPORT", line, re.IGNORECASE)
        if match:
            header.append(line)
    print(header, "\n")
    header_dict = {}

    for index, string in enumerate(header):
        header_dict[index] = string

    print(header_dict, "\n")

lines = text.split("\n")
header(lines)

# Initialize patient_info dictionary
patient_info = {}

# Find the lines that contain the patient information
def extract_patient_information(lines):
    # Iterate over the lines
    for line in lines:
        print(line)
        # Extract the voucher number, date, and report number
        match = re.search(r"Voucher No\. : (.*) Date : (.*) Report No : (.*)", line)
        if match:
            voucher_number = match.group(1)
            date = match.group(2)
            report_number = match.group(3)

            # Add the information to the dictionary
            patient_info["voucher_number"] = voucher_number
            patient_info["date"] = date
            patient_info["report_number"] = report_number

        match = re.search(r"Patient Name : (.*)", line)
        if match:
            patient_name = match.group(1)
            patient_info["patient_name"] = patient_name

        # Extract the patient name, referred by, age, and sex
        match = re.search(r"Referred By : (.*) Age :(.*)¥ Sex: (.*)", line)
        if match:
            referred_by = match.group(1)
            age = match.group(2)
            sex = match.group(3)

            # Add the information to the dictionary
            patient_info["referred_by"] = referred_by
            patient_info["age"] = age
            patient_info["sex"] = sex

        # Extract the sample and lab number
        match = re.search(r"Sample : (.*) Lab No : (.*)", line)
        if match:
            sample = match.group(1)
            lab_number = match.group(2)

            # Add the information to the dictionary
            patient_info["sample"] = sample
            patient_info["lab_number"] = lab_number

# Call the extract_patient_information function to extract patient data
extract_patient_information(lines)

# Create a JSON object for patient information
patient_info_json = json.dumps(patient_info)

# Insert patient information into the database
cursor.execute("""
    INSERT INTO medical_reports (
        voucher_number, date, report_number,
        patient_name, referred_by, age, sex,
        sample, lab_number
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    );
""", (
    patient_info.get("voucher_number", ""),
    patient_info.get("date", ""),
    patient_info.get("report_number", ""),
    patient_info.get("patient_name", ""),
    patient_info.get("referred_by", ""),
    patient_info.get("age", ""),
    patient_info.get("sex", ""),
    patient_info.get("sample", ""),
    patient_info.get("lab_number", "")
    # None  # Placeholder for leucocyte_count
))

# Commit the transaction
connection.commit()

# Find the lines that contain the test results
def extract_test_results(lines):
    test_results = []
    for line in lines:
        match = re.search(r"Test|Haemoglobin|Total Red Blood Cells|HCT|MCV|MCH|MCHC|RDW|Total White Blood Cells", line, re.IGNORECASE)
        if match:
            test_results.append(line)

    # Create a regular expression to extract the test name, result, and normal range
    regex = r"^([a-zA-Z\sa-zA-Z]+) (.*[\%$]|.*[\w$]) (.+)$"
    test_info_dict = {}

    # Iterate over the test results
    for test_result in test_results:
        match = re.match(regex, test_result, re.IGNORECASE)
        if match:
            test_name = match.group(1)
            result = match.group(2)
            normal_range = match.group(3)

            # Add the extracted information to the dictionary
            test_info_dict[test_name] = {
                "result": result,
                "normal_range": normal_range
            }

    # Convert the dictionary to JSON
    # test_results_json = json.dumps(test_info_dict)

    # Update test results in the database
    # cursor.execute("""
    #     UPDATE medical_reports
    #     SET test_results = %s
    #     WHERE voucher_number = %s;
    # """, (test_results_json, patient_info.get("voucher_number", "")))

    # Commit the transaction
    # connection.commit()

# Call the extract_test_results function to extract and store test results
# extract_test_results(lines)

# Find the lines that contain the leucocyte count results
def extract_leucocyte_count(lines):
    leucocyte_results = []
    for line in lines:
        match = re.search(r"leucocyte_count|Neutrophils|Eosinophils|Basophils|Lymphocytes|Monocytes|Other Cells|Platelets|MPV|ESR", line, re.IGNORECASE)
        if match:
            leucocyte_results.append(line)

    # Create a regular expression to extract the test name, result, and normal range
    regex = r"^([a-zA-Z\sa-zA-Z]+) (.*[\%$]|.*[\w$]) (.+)$"
    leucocyte_count_dict = {}

    # Iterate over the leucocyte count results
    for result in leucocyte_results:
        match = re.match(regex, result)
        if match:
            test_name = match.group(1)
            result = match.group(2)
            normal_range = match.group(3)

            # Add the extracted information to the dictionary
            leucocyte_count_dict[test_name] = {
                "result": result,
                "normal_range": normal_range
            }

    # Convert the dictionary to JSON
    # leucocyte_count_json = json.dumps(leucocyte_count_dict)

    # Update leucocyte count results in database
    # cursor.execute("""
    #     UPDATE medical_reports
    #     SET leucocyte_count_results = %s
    #     WHERE voucher_number = %s;
    # """, (leucocyte_count_json, patient_info.get("voucher_number", "")))

    # Commit the transaction
    # connection.commit()

# Call the extract_leucocyte_results function to extract and store leucocyte results
# extract_leucocyte_count(lines)





# import cv2
# import pytesseract
# import re
# import psycopg2
# import json
# import pandas as pd

# # Set up PostgreSQL connection
# connection = psycopg2.connect(
#     database="your_database_name",
#     user="your_username",
#     password="your_password",
#     host="your_host",
#     port="your_port"
# )
# cursor = connection.cursor()

# # Load the medical report image
# image = cv2.imread("medical_report.png")

# # Convert the image to grayscale
# gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# # Apply thresholding to binarize the image
# thresholded_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)[1]

# # Extract the text from the largest contour
# text = pytesseract.image_to_string(thresholded_image, lang="eng")

# def patient_information(lines):
#     patient_info = {}
    
#     for line in lines:
#         # Extract the voucher number, date, and report number
#         match = re.search(r"Voucher No\. : (.*) Date : (.*) Report No : (.*)", line)
#         if match:
#             voucher_number = match.group(1)
#             date = match.group(2)
#             report_number = match.group(3)

#             # Add the information to the dictionary
#             patient_info["voucher_number"] = voucher_number
#             patient_info["date"] = date
#             patient_info["report_number"] = report_number

#         match = re.search(r"Patient Name : (.*)", line)
#         if match:
#             patient_name = match.group(1)
#             patient_info["patient_name"] = patient_name

#         # Extract the patient name, referred by, age, and sex
#         match = re.search(r"Referred By : (.*) Age :(.*)¥ Sex: (.*)", line)
#         if match:
#             referred_by = match.group(1)
#             age = match.group(2)
#             sex = match.group(3)

#             # Add the information to the dictionary
#             patient_info["referred_by"] = referred_by
#             patient_info["age"] = age
#             patient_info["sex"] = sex

#         # Extract the sample and lab number
#         match = re.search(r"Sample : (.*) Lab No : (.*)", line)
#         if match:
#             sample = match.group(1)
#             lab_number = match.group(2)

#             # Add the information to the dictionary
#             patient_info["sample"] = sample
#             patient_info["lab_number"] = lab_number
    
#     # Create a JSON object for patient information
#     patient_info_json = json.dumps(patient_info)

#     # Insert patient information into the database
#     cursor.execute("""
#         INSERT INTO medical_reports (
#             voucher_number, date, report_number,
#             patient_name, referred_by, age, sex,
#             sample, lab_number, test_results, leucocyte_count
#         )
#         VALUES (
#             %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
#         );
#     """, (
#         patient_info.get("voucher_number", ""),
#         patient_info.get("date", ""),
#         patient_info.get("report_number", ""),
#         patient_info.get("patient_name", ""),
#         patient_info.get("referred_by", ""),
#         patient_info.get("age", ""),
#         patient_info.get("sex", ""),
#         patient_info.get("sample", ""),
#         patient_info.get("lab_number", ""),
#         patient_info_json,  # JSON representation of test_results
#         None  # You can insert leucocyte count data here in a similar manner
#     ))

#     # Commit the transaction
#     connection.commit()

#     # Close the database connection
#     connection.close()

# def test_results(lines):
#     test_results = []
#     for line in lines:
#         match = re.search(r"Test|Haemoglobin|Total Red Blood Cells|HCT|MCV|MCH|MCHC|RDW|Total White Blood Cells", line, re.IGNORECASE)
#         if match:
#             test_results.append(line)

#     # Create a regular expression to extract the test name, result, and normal range
#     regex = r"^([a-zA-Z\sa-zA-Z]+) (.*[\%$]|.*[\w$]) (.+)$"
#     test_info_dict = {}

#     # Iterate over the test results
#     for test_result in test_results:
#         match = re.match(regex, test_result, re.IGNORECASE)
#         if match:
#             test_name = match.group(1)
#             result = match.group(2)
#             normal_range = match.group(3)

#             # Add the extracted information to the dictionary
#             test_info_dict[test_name] = {
#                 "result": result,
#                 "normal_range": normal_range
#             }

#     # Convert the dictionary to JSON
#     test_results_json = json.dumps(test_info_dict)

#     # Insert test results into the database (you can modify the SQL statement accordingly)
#     cursor.execute("""
#         UPDATE medical_reports
#         SET test_results = %s
#         WHERE voucher_number = %s;
#     """, (test_results_json, patient_info.get("voucher_number", "")))

#     # Commit the transaction
#     connection.commit()

# def leucocyte_count(lines):
#     leucocyte_results = []
#     for line in lines:
#         match = re.search(r"leucocyte_count|Neutrophils|Eosinophils|Basophils|Lymphocytes|Monocytes|Other Cells|Platelets|MPV|ESR", line, re.IGNORECASE)
#         if match:
#             leucocyte_results.append(line)

#     # Create a regular expression to extract the test name, result, and normal range
#     regex = r"^([a-zA-Z\sa-zA-Z]+) (.*[\%$]|.*[\w$]) (.+)$"
#     leucocyte_count_dict = {}

#     # Iterate over the leucocyte results
#     for result in leucocyte_results:
#         match = re.match(regex, result)
#         if match:
#             test_name = match.group(1)
#             result = match.group(2)
#             normal_range = match.group(3)

#             # Add the extracted information to the dictionary
#             leucocyte_count_dict[test_name] = {
#                 "result": result,
#                 "normal_range": normal_range
#             }

#     # Convert the dictionary to JSON
#     leucocyte_count_json = json.dumps(leucocyte_count_dict)

#     # Insert leucocyte count into the database (you can modify the SQL statement accordingly)
#     cursor.execute("""
#         UPDATE medical_reports
#         SET leucocyte_count = %s
#         WHERE voucher_number = %s;
#     """, (leucocyte_count_json, patient_info.get("voucher_number", "")))

#     # Commit the transaction
#     connection.commit()

# # Call the patient_information function to extract patient data
# lines = text.split("\n")
# patient_information(lines)

# # Call the test_results and leucocyte_count functions to extract and store test results
# test_results(lines)
# leucocyte_count(lines)

# # Ensure you close the database connection when done with all operations
# connection.close()

# # Print the extracted patient information (for debugging)
# print("Patient Information:")
# print(json.dumps(patient_info, indent=4))

# #
