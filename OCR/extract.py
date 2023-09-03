import cv2
import pytesseract
import re
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import pandas as pd
import json
import csv


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
        match = re.search(r"ARMED|Dhaka Cantonment Bangladesh|Recipient|Tel:|Fax|HAEMATOLOGY REPORT",line,re.IGNORECASE)
        if match:
            header.append(line)
    print(header,"\n")
    header_dict = {}

    for index, string in enumerate(header):
        header_dict[index] = string

    print(header_dict,"\n")

lines = text.split("\n")
header(lines)

# Find the lines that contain the patient information
def patient_information(lines):
    patient_info = {}

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

        match = re.search(r"Patient Name : (.*)",line)
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
    # Create a CSV file
    with open("patient_info.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=patient_info.keys())

        # Write the key and value pairs to the CSV file
        writer.writeheader()
        writer.writerow(patient_info)
    # Print the dictionary
    print(patient_info)
lines = text.split("\n")
patient_information(lines)


def test_results(lines):
    test_results=[]
    for line in lines:
        # print(line)
        match = re.search(r"Test|Haemoglobin|Total Red Blood Cells|HCT|MCV|MCH|MCHC|RDW|Total White Blood Cells",line,re.IGNORECASE)
        if match:
            test_results.append(line)
    print("_"*10,"\n")
    print("List of test results : ",test_results,"\n")

    # Create a regular expression to extract the test name, result, and normal range
    regex = r"^([a-zA-Z\sa-zA-Z]+) (.*[\%$]|.*[\w$]) (.+)$"
   

    # Create a dictionary to store the extracted information
    test_info_dict = {}

    # Iterate over the test results
    for test_result in test_results:
        match = re.match(regex, test_result,re.IGNORECASE)
        if match:
            test_name = match.group(1)
            result = match.group(2)
            normal_range = match.group(3)
            

            # Add the extracted information to the dictionary
            test_info_dict[test_name] = {
                "result": result,
                "normal_range": normal_range

            }

    # Print the dictionary
    print("Test restuls : ",test_info_dict,"\n")

    pd.set_option('display.max_columns', None)
    df_test =pd.DataFrame(test_info_dict)
    df_test.to_csv('test_results.csv')

lines = text.split("\n")
test_results(lines)

def leucocyte_count(lines):
    leucocyte_results=[]
    for line in lines:
        match = re.search(r"leucocyte_count|Neutrophils|Eosinophils|Basophils|Lymphocytes|Monocytes|Other Cells|Platelets|MPV|ESR",line,re.IGNORECASE)
        if match:
            leucocyte_results.append(line)
    print('-'*10,"\n")
    print("List of leucocyte count results : ",leucocyte_results,"\n")
   

    # Create a regular expression to extract the test name, result, and normal range
    regex = r"^([a-zA-Z\sa-zA-Z]+) (.*[\%$]|.*[\w$]) (.+)$"
    leucocyte_count_dict={}
    # Iterate over the leucocyte results
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

    # Print the dictionary
    print("leucocyte count : ", leucocyte_count_dict,"\n")
    df_leu = pd.DataFrame(leucocyte_count_dict)
    df_leu.to_csv('leucocyte_count.csv')
lines = text.split("\n")
leucocyte_count(lines)