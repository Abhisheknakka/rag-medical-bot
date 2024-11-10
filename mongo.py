import pymongo
from pymongo import MongoClient

# MongoDB URI from your credentials
MONGODB_URI = "mongodb+srv://nakkaabhishek99:HMWDUttqlH4ZCKAu@cluster0.lnmlz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB
client = MongoClient(MONGODB_URI)

# Select the database and collection
db = client["medical_bot"]
collection = db["feedback"]

# Sample feedback data to be uploaded
sample_data = {
    "patient_name": "John Doe",
    "prescription_summary": "Take 500mg Paracetamol twice a day for 5 days. Drink plenty of water.",
    "doctor_comments": "Patient is recovering well. No complications.",
    "feedback": "The prescription was clear and easy to follow. Would recommend.",
    "rating": 4,  # Rating out of 5
    "timestamp": "2024-11-10 10:00:00"
}


# Insert the sample data into the feedback collection
insert_result = collection.insert_one(sample_data)

# Confirm insertion
if insert_result.acknowledged:
    print(f"Sample data inserted with ID: {insert_result.inserted_id}")
else:
    print("Data insertion failed.")
