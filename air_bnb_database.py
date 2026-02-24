import json
import mysql.connector

# Load JSON file
input_file = "air_bnb_2026-02-22.json"

def load_file(file_name: str):
    with open(file_name, "rb") as f:
        data = json.loads(f.read().decode())
    return data

extracted = load_file(input_file)

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="actowiz",
    database="flight_db"
)
cursor = conn.cursor()

# Create Airbnb table
create_query = """
CREATE TABLE IF NOT EXISTS Airbnb_Data (
    Name VARCHAR(255),
    Location VARCHAR(255),
    About TEXT,
    ReviewCount INT,
    OverallRating FLOAT,
    Rating_Cleanliness FLOAT,
    Rating_Accuracy FLOAT,
    Rating_Checkin FLOAT,
    Rating_Communication FLOAT,
    Rating_Location FLOAT,
    Rating_Value FLOAT,
    Images JSON,
    AllAmenities JSON,
    CheckIn VARCHAR(50),
    CheckOut VARCHAR(50),
    MaxGuests INT,
    HostName VARCHAR(100),
    HostRating FLOAT,
    HostReviewCount INT,
    HostingYear VARCHAR(50),
    HostAbout JSON
);
"""
cursor.execute(create_query)

# Extract host info
host = extracted.get("host", {})
host_name = host.get("name")
host_rating = host.get("rating")
host_review_count = host.get("review_count")
hosting_year = host.get("hosting_year")
host_about = json.dumps(host.get("about"))

# Extract ratings
ratings = extracted.get("ratings", {})
overall_rating = ratings.get("overall", None)

# Initialize category ratings
cleanliness = accuracy = checkin = communication = location_rating = value = None
for cat in ratings.get("categories", []):
    category = cat.get("category", "").upper()
    rating_val = cat.get("rating")
    if category == "CLEANLINESS":
        cleanliness = rating_val
    elif category == "ACCURACY":
        accuracy = rating_val
    elif category == "CHECKIN":
        checkin = rating_val
    elif category == "COMMUNICATION":
        communication = rating_val
    elif category == "LOCATION":
        location_rating = rating_val
    elif category == "VALUE":
        value = rating_val

# Convert nested fields to JSON strings
images = json.dumps(extracted.get("images", []))
all_amenities = json.dumps(extracted.get("allAmenities", {}))
about = json.dumps(extracted.get("about", {}))

# Prepare record
record = (
    extracted.get("name"),
    extracted.get("location"),
    about,
    extracted.get("review_count"),
    overall_rating,
    cleanliness,
    accuracy,
    checkin,
    communication,
    location_rating,
    value,
    images,
    all_amenities,
    extracted.get("check_in"),
    extracted.get("check_out"),
    extracted.get("max_guests"),
    host_name,
    host_rating,
    host_review_count,
    hosting_year,
    host_about
)

# Insert into database
insert_query = """
INSERT INTO Airbnb_Data (
    Name, Location, About, ReviewCount, OverallRating,
    Rating_Cleanliness, Rating_Accuracy, Rating_Checkin, Rating_Communication,
    Rating_Location, Rating_Value, Images, AllAmenities, CheckIn, CheckOut,
    MaxGuests, HostName, HostRating, HostReviewCount, HostingYear, HostAbout
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

cursor.execute(insert_query, record)
conn.commit()
conn.close()
