import json,re
from pprint import pprint
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

def load_file(file_name: str):
    with open(file_name,"rb") as f:
        data=json.loads(f.read().decode())
    return data


class Airbnb(BaseModel):

    name: Optional[str] = None
    location: Optional[str] = None
    about: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    review_count: Optional[int] = None
    ratings: Dict[str, Any]
    images: List[Dict[str, Optional[str]]] = Field(default_factory=list)
    allAmenities: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    max_guests: Optional[int] = None

    host: Dict[str, Any]

    @field_validator("max_guests", mode="before")
    @classmethod
    def extract_guest_number(cls, v):
        if isinstance(v, str):
            match = re.search(r"\d+", v)
            if match:
                return int(match.group())
        return v


def parser(data, result):

    if isinstance(data, dict):
        
        #name
        if "listingTitle" in data:
            result["name"] = data["listingTitle"]

        #location
        if data.get("__typename") == "LocationSection" :
            result["location"] = data["subtitle"]

        #about
        if data.get("pluginPointId") == "DESCRIPTION_MODAL":

            section = data.get("section", {})
            items = section.get("items", [])
            main_title = section.get("title", "About this space")

            about_dict = {}

            for item in items:

                title = item.get("title")
                html_text = item.get("html", {}).get("htmlText", "")

                if html_text:
                    clean_desc = re.sub(r"<br\s*/?>", "\n", html_text)
                    clean_desc = re.sub("<.*?>", "", clean_desc)
                    clean_desc = clean_desc.replace("\u202f", " ")
                    clean_desc = clean_desc.replace("\xa0", " ")
                    clean_desc = re.sub(r"\s+", " ", clean_desc).strip()

                    if title is None:
                        about_dict[main_title] = {
                            "title": main_title,
                            "description": clean_desc
                        }
                    else:
                        about_dict[title] = {
                            "title": title,
                            "description": clean_desc
                        }

            result["about"] = about_dict

        #review count
        if "reviewCount" in data:
            result["review_count"] = data["reviewCount"]

        
        #images url
        if "mediaItems" in data and isinstance(data["mediaItems"], list):

            for item in data["mediaItems"]:

                if isinstance(item, dict):

                    label = item.get("accessibilityLabel")
                    url = item.get("baseUrl")

                    if url:  
                        result["images"].append({
                            "label": label,
                            "url": url
                    })
        #ratings
        if "ratings" in data and isinstance(data["ratings"], list):
            for item in data["ratings"]:
                if isinstance(item, dict):

                    category = item.get("categoryType")
                    rating = item.get("localizedRating")

                    if category and rating:
                        result["ratings"]["categories"].append({
                            "category": category,
                            "rating": float(rating)
                        })

        #overall rating
        if data.get("__typename") == "StayEmbedData":

            if "starRating" in data and data["starRating"] is not None:
                result["ratings"]["overall"] = float(data["starRating"])


        #amenities
        if "seeAllAmenitiesGroups" in data :
            for group in data["seeAllAmenitiesGroups"]:

                if isinstance(group, dict):

                    category = group.get("title")
                    amenities_list = group.get("amenities", [])

                    if category and isinstance(amenities_list, list):
                        result["allAmenities"].setdefault(category, {
                            "amenities": []
                        })

                        for amenity in amenities_list:

                            if isinstance(amenity, dict):

                                title = amenity.get("title")

                                if title:
                                    result["allAmenities"][category]["amenities"].append(title)

        #host information
        if data.get("__typename") == "MeetYourHostSection":

            card = data.get("cardData", {})
            if card.get("name"):
                result["host"]["name"] = card["name"]

            if card.get("ratingAverage") is not None:
                result["host"]["rating"] = float(card["ratingAverage"])

            if card.get("ratingCount") is not None:
                result["host"]["review_count"] = card["ratingCount"]

            years = card.get("timeAsHost", {}).get("years")
            if years is not None:
                result["host"]["hosting_year"] = f"{years} year"

            highlights = data.get("hostHighlights", [])

            for item in highlights:
                title = item.get("title", "")

                if title.startswith("My work:"):
                    result["host"]["about"]["work"] = title.replace("My work:", "").strip()

                elif title.startswith("Fun fact:"):
                    result["host"]["about"]["fun_fact"] = title.replace("Fun fact:", "").strip()

                elif title.startswith("For guests, I always:"):
                    result["host"]["about"]["for_guests"] = title.replace("For guests, I always:", "").strip()

                elif title.startswith("Pets:"):
                    result["host"]["about"]["pets"] = title.replace("Pets:", "").strip()

        #check-in, check-out, max guests
        if "houseRules" in data and isinstance(data["houseRules"], list):
            for rule in data["houseRules"]:
                title = rule.get("title", "")
                if "Check-in" in title:
                    result["check_in"] = title
                if "Checkout" in title: 
                    result["check_out"] = title
                if "guests" in title.lower():
                    result["max_guests"] = title


        for value in data.values():
            parser(value, result)

    elif isinstance(data, list):
        for item in data:           
            parser(item, result)
    return result

            
def dump_file(validated_data: dict):
    with open(f"air_bnb_{datetime.now().date()}.json","wb") as f:
        f.write(json.dumps(validated_data, indent=4,ensure_ascii=False).encode())



file="air_bnb.json"
json_data=load_file(file)
result = {
        "name": None,
        "location": None,
        "about": {},
        "review_count": None,
        "ratings":{            
            "overall": None,
            "categories": []
        },
        "images": [],
        "allAmenities": {},
        "check_in": None,
        "check_out": None,
        "max_guests": None,
        "host": {
            "name": None,
            "rating": None,
            "review_count": None,
            "hosting_year": None,
            "about": {}
        }
    }
extracted=parser(json_data,result)
try:
    validated = Airbnb(**extracted)
    dump_file(validated.model_dump())

except Exception as e:
    print("Validation error:", e)

