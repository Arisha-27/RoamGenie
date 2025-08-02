import streamlit as st
import json
import os
import requests
import pandas as pd
import base64
from PIL import Image
import io
import cv2
import numpy as np
from serpapi import GoogleSearch
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from twilio.rest import Client
from datetime import datetime
import pytesseract
import re

# Twilio SMS Notification setup
try:
    twilio_sid = st.secrets["TWILIO_ACCOUNT_SID"]
    twilio_token = st.secrets["TWILIO_AUTH_TOKEN"]
    twilio_number = st.secrets["TWILIO_PHONE_NUMBER"]
    client = Client(twilio_sid, twilio_token)
except KeyError:
    st.warning("Twilio secrets not found. Please configure them in .streamlit/secrets.toml for full functionality.")
    # Fallback dummy values to prevent app crash if secrets are not configured for local dev
    twilio_sid = "ACa84b12a3d81d88e62b1d06d29cfd4f18"
    twilio_token = "10fce4b0ecc25047497dbbbdd485e8a4"
    twilio_number = "+14439988287"
    client = None

def make_voice_call(to_number, message):
    if client:
        try:
            call = client.calls.create(
                to=to_number,
                from_=twilio_number,
                twiml=f"<Response><Say>{message}</Say></Response>"
            )
            return call.sid
        except Exception as e:
            st.error(f"Error making call: {e}")
            return None
    else:
        st.error("Twilio client not initialized. Please configure Twilio secrets.")
        return None

st.set_page_config(page_title="RoamGenie - AI Travel Planner", layout="wide")
st.markdown("""
    <style>
        .title-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .main-title {
            font-size: 48px;
            font-weight: bold;
            color: #4A4A6A;
            margin-bottom: 5px;
        }
        .subtitle {
            font-size: 24px;
            color: #777;
            margin-top: 0;
        }
        .stSlider > div { background-color: #f9f9f9; padding: 10px; border-radius: 10px; }
        .passport-scan { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin: 20px 0; }
        .visa-free-card {
            background: #f8f9fa;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .country-name {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .visa-status {
            font-size: 12px;
            color: #28a745;
            font-weight: 500;
        }
        .top-navigation {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            gap: 20px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .top-navigation button {
            background-color: transparent;
            color: #667eea;
            border: none;
            padding: 10px 15px;
            font-size: 18px;
            cursor: pointer;
            transition: color 0.3s, border-bottom 0.3s;
        }
        .top-navigation button:hover {
            color: #764ba2;
            border-bottom: 2px solid #764ba2;
        }
        .top-navigation button.active {
            color: #764ba2;
            font-weight: bold;
            border-bottom: 2px solid #764ba2;
        }
        .flight-card {
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            background-color: #f9f9f9;
            margin-bottom: 20px;
        }
        .flight-card img {
            max-width: 100px;
            margin-bottom: 10px;
        }
        .flight-card h3 {
            margin: 10px 0;
        }
        .flight-card p {
            margin: 5px 0;
        }
        .flight-card .price {
            color: #008000;
            font-size: 24px;
            font-weight: bold;
            margin-top: 10px;
        }
        .flight-card .book-now-link {
            display: inline-block;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            color: #fff;
            background-color: #007bff;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
        }
        .hotel-card {
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            background-color: #f9f9f9;
            margin-bottom: 20px;
            min-height: 400px;
        }
        .hotel-card img {
            width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .hotel-card h3 {
            margin: 10px 0;
            color: #2c3e50;
        }
        .hotel-card .rating {
            color: #f39c12;
            font-size: 18px;
            margin: 10px 0;
        }
        .hotel-card .reviews {
            color: #7f8c8d;
            font-size: 14px;
        }
        .hotel-card .amenities {
            color: #34495e;
            font-size: 12px;
            margin: 8px 0;
        }
        .hotel-card .price {
            color: #27ae60;
            font-size: 24px;
            font-weight: bold;
            margin: 15px 0 5px 0;
        }
        .hotel-card .per-night {
            color: #7f8c8d;
            font-size: 12px;
        }
        .hotel-card .book-hotel-link {
            display: inline-block;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: bold;
            color: #fff;
            background-color: #e74c3c;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
            transition: background-color 0.3s;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_path = "Roamlogo.png"
logo_base64 = get_base64_image(logo_path)

if 'passport_country' not in st.session_state:
    st.session_state.passport_country = None
if 'visa_free_countries' not in st.session_state:
    st.session_state.visa_free_countries = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Travel Plan"

st.markdown(f"""
    <div class="title-container">
        <img src="data:image/png;base64,{logo_base64}" width="150" style="margin-bottom: 10px;">
        <div class="main-title">RoamGenie</div>
        <p class="subtitle">AI-Powered Travel Planner</p>
    </div>
""", unsafe_allow_html=True)

SERPAPI_KEY = "2d398ac4866275207b7c6d69be063e52f19f68a20226d2b4f7e6dbc1b706406d"
GOOGLE_API_KEY = "AIzaSyDaNY4vgBs5iyp2eGcWfd41mZHB9Rhz1XI"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

OCR_SPACE_API_KEY = "YOUR_OCR_SPACE_API_KEY"
MINDEE_API_KEY = "YOUR_MINDEE_API_KEY"

class PassportScanner:
    def __init__(self):
        self.visa_data = None
        self.country_flags = {}
        self.load_visa_dataset()
        self.load_country_flags()

    def load_visa_dataset(self):
        try:
            url1 = "https://raw.githubusercontent.com/ilyankou/passport-index-dataset/master/passport-index-tidy.csv"
            try:
                self.visa_data = pd.read_csv(url1)
                return
            except Exception as e1:
                st.warning(f"Failed to load primary dataset: {e1}. Attempting secondary...")

            url2 = "https://raw.githubusercontent.com/datasets/passport-index/main/data/passport-index-tidy.csv"
            try:
                self.visa_data = pd.read_csv(url2)
                return
            except Exception as e2:
                st.warning(f"Failed to load secondary dataset: {e2}. Creating comprehensive dataset as fallback...")

            self.create_comprehensive_visa_data()

        except Exception as e:
            st.error(f"Error loading visa dataset: {e}")
            self.create_comprehensive_visa_data()

    def create_comprehensive_visa_data(self):
        visa_data = {
            'India': {
                'visa_free': [
                    'Bhutan', 'Nepal', 'Maldives', 'Mauritius', 'Seychelles', 'Fiji',
                    'Vanuatu', 'Micronesia', 'Samoa', 'Cook Islands', 'Niue', 'Tuvalu',
                    'Indonesia', 'Thailand', 'Malaysia', 'Singapore', 'Philippines',
                    'Cambodia', 'Laos', 'Myanmar', 'Sri Lanka', 'Bangladesh',
                    'South Korea', 'Japan', 'Qatar', 'UAE', 'Oman', 'Kuwait',
                    'Bahrain', 'Jordan', 'Iran', 'Armenia', 'Georgia', 'Kazakhstan',
                    'Kyrgyzstan', 'Tajikistan', 'Uzbekistan', 'Mongolia', 'Turkey',
                    'Serbia', 'Albania', 'North Macedonia', 'Bosnia and Herzegovina',
                    'Montenegro', 'Moldova', 'Belarus', 'Madagascar', 'Comoros',
                    'Cape Verde', 'Guinea-Bissau', 'Mozambique', 'Zimbabwe', 'Zambia',
                    'Uganda', 'Rwanda', 'Burundi', 'Tanzania', 'Kenya', 'Ethiopia',
                    'Djibouti', 'Somalia', 'Sudan', 'Egypt', 'Morocco', 'Tunisia',
                    'Barbados', 'Dominica', 'Grenada', 'Haiti', 'Jamaica',
                    'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines',
                    'Trinidad and Tobago', 'El Salvador', 'Honduras', 'Nicaragua',
                    'Bolivia', 'Ecuador', 'Suriname'
                ]
            },
            'United States': {
                'visa_free': [
                    'Canada', 'Mexico', 'United Kingdom', 'Ireland', 'France', 'Germany',
                    'Italy', 'Spain', 'Netherlands', 'Belgium', 'Luxembourg', 'Austria',
                    'Switzerland', 'Portugal', 'Greece', 'Denmark', 'Sweden', 'Norway',
                    'Finland', 'Iceland', 'Estonia', 'Latvia', 'Lithuania', 'Poland',
                    'Czech Republic', 'Slovakia', 'Hungary', 'Slovenia', 'Croatia',
                    'Malta', 'Cyprus', 'Japan', 'South Korea', 'Singapore', 'Australia',
                    'New Zealand', 'Chile', 'Uruguay', 'Argentina', 'Brazil', 'Israel',
                    'Taiwan', 'Hong Kong', 'Macau', 'Brunei', 'Malaysia', 'Thailand'
                ]
            },
            'Germany': {
                'visa_free': [
                    'European Union Countries', 'United States', 'Canada', 'Australia',
                    'New Zealand', 'Japan', 'South Korea', 'Singapore', 'Malaysia',
                    'Thailand', 'Philippines', 'Indonesia', 'Vietnam', 'Cambodia',
                    'Israel', 'United Arab Emirates', 'Qatar', 'Kuwait', 'Bahrain',
                    'Chile', 'Argentina', 'Brazil', 'Uruguay', 'Paraguay', 'Mexico',
                    'Costa Rica', 'Nicaragua', 'Honduras', 'El Salvador', 'Guatemala',
                    'Panama', 'Colombia', 'Ecuador', 'Peru', 'Bolivia', 'Venezuela',
                    'Guyana', 'Suriname', 'South Africa', 'Botswana', 'Namibia',
                    'Mauritius', 'Seychelles', 'Morocco', 'Tunisia', 'Turkey',
                    'Serbia', 'Montenegro', 'Albania', 'North Macedonia', 'Bosnia and Herzegovina'
                ]
            },
            'Singapore': {
                'visa_free': [
                    'Malaysia', 'Thailand', 'Indonesia', 'Philippines', 'Vietnam',
                    'Cambodia', 'Laos', 'Myanmar', 'Brunei', 'Japan', 'South Korea',
                    'Hong Kong', 'Macau', 'Taiwan', 'United States', 'Canada',
                    'United Kingdom', 'Ireland', 'European Union Countries',
                    'Australia', 'New Zealand', 'Chile', 'Argentina', 'Brazil',
                    'Uruguay', 'Israel', 'Turkey', 'United Arab Emirates', 'Qatar',
                    'Kuwait', 'Bahrain', 'Oman', 'Saudi Arabia', 'Jordan'
                ]
            },
            'United Kingdom': {
                'visa_free': [
                    'European Union Countries', 'United States', 'Canada', 'Australia',
                    'New Zealand', 'Japan', 'South Korea', 'Singapore', 'Malaysia',
                    'Thailand', 'Philippines', 'Indonesia', 'Vietnam', 'Hong Kong',
                    'Macau', 'Taiwan', 'Israel', 'United Arab Emirates', 'Qatar',
                    'Kuwait', 'Bahrain', 'Oman', 'Chile', 'Argentina', 'Brazil',
                    'Uruguay', 'Mexico', 'Costa Rica', 'Panama', 'Colombia',
                    'Ecuador', 'Peru', 'Bolivia', 'Venezuela', 'Guyana', 'Suriname'
                ]
            }
        }

        passport_data = []
        destination_data = []
        requirement_data = []

        for passport_country, data in visa_data.items():
            for dest_country in data['visa_free']:
                passport_data.append(passport_country)
                destination_data.append(dest_country)
                requirement_data.append('visa free')
        
        

            
        self.visa_data = pd.DataFrame({
            'Passport': passport_data,
            'Destination': destination_data,
            'Requirement': requirement_data
        })

    def load_country_flags(self):
        self.country_flags = {
            'Thailand': '🇹🇭', 'Singapore': '🇸🇬', 'Malaysia': '🇲🇾', 'Indonesia': '🇮🇩',
            'Philippines': '🇵🇭', 'Cambodia': '🇰🇭', 'Laos': '🇱🇦', 'Myanmar': '🇲🇲',
            'Vietnam': '🇻🇳', 'Brunei': '🇧🇳', 'Nepal': '🇳🇵', 'Bhutan': '🇧🇹',
            'Maldives': '🇲🇻', 'Sri Lanka': '🇱🇰', 'Bangladesh': '🇧🇩', 'India': '🇮🇳',
            'Japan': '🇯🇵', 'South Korea': '🇰🇷', 'China': '🇨🇳', 'Taiwan': '🇹🇼',
            'Hong Kong': '🇭🇰', 'Macau': '🇲🇴', 'Mongolia': '🇲🇳', 'Kazakhstan': '🇰🇿',
            'Kyrgyzstan': '🇰🇬', 'Tajikistan': '🇹🇯', 'Uzbekistan': '🇺🇿',

            'UAE': '🇦🇪', 'Qatar': '🇶🇦', 'Oman': '🇴🇲', 'Kuwait': '🇰🇼',
            'Bahrain': '🇧🇭', 'Saudi Arabia': '🇸🇦', 'Jordan': '🇯🇴', 'Lebanon': '🇱🇧',
            'Syria': '🇸🇾', 'Iraq': '🇮🇶', 'Iran': '🇮🇷', 'Israel': '🇮🇱',
            'Turkey': '🇹🇷', 'Cyprus': '🇨🇾', 'Armenia': '🇦🇲', 'Georgia': '🇬🇪',

            'United Kingdom': '🇬🇧', 'Ireland': '🇮🇪', 'France': '🇫🇷', 'Germany': '🇩🇪',
            'Italy': '🇮🇹', 'Spain': '🇪🇸', 'Portugal': '🇵🇹', 'Netherlands': '🇳🇱',
            'Belgium': '🇧🇪', 'Luxembourg': '🇱🇺', 'Switzerland': '🇨🇭', 'Austria': '🇦🇹',
            'Denmark': '🇩🇰', 'Sweden': '🇸🇪', 'Norway': '🇳🇴', 'Finland': '🇫🇮',
            'Iceland': '🇮🇸', 'Greece': '🇬🇷', 'Malta': '🇲🇹', 'Poland': '🇵🇱',
            'Czech Republic': '🇨🇿', 'Slovakia': '🇸🇰', 'Hungary': '🇭🇺',
            'Slovenia': '🇸🇮', 'Croatia': '🇭🇷', 'Bosnia and Herzegovina': '🇧🇦',
            'Serbia': '🇷🇸', 'Montenegro': '🇲🇪', 'Albania': '🇦🇱',
            'North Macedonia': '🇲🇰', 'Bulgaria': '🇧🇬', 'Romania': '🇷🇴',
            'Moldova': '🇲🇩', 'Ukraine': '🇺🇦', 'Belarus': '🇧🇾', 'Russia': '🇷🇺',
            'Estonia': '🇪🇪', 'Latvia': '🇱🇻', 'Lithuania': '🇱🇹',

            'United States': '🇺🇸', 'Canada': '🇨🇦', 'Mexico': '🇲🇽', 'Guatemala': '🇬🇹',
            'Belize': '🇧🇿', 'El Salvador': '🇸🇻', 'Honduras': '🇭🇳', 'Nicaragua': '🇳🇮',
            'Costa Rica': '🇨🇷', 'Panama': '🇵🇦', 'Colombia': '🇨🇴', 'Venezuela': '🇻🇪',
            'Guyana': '🇬🇾', 'Suriname': '🇸🇷', 'Brazil': '🇧🇷', 'Ecuador': '🇪🇨',
            'Peru': '🇵🇪', 'Bolivia': '🇧🇴', 'Paraguay': '🇵🇾', 'Uruguay': '🇺🇾',
            'Argentina': '🇦🇷', 'Chile': '🇨🇱', 'Cuba': '🇨🇺', 'Jamaica': '🇯🇲',
            'Haiti': '🇭🇹', 'Dominican Republic': '🇩🇴', 'Puerto Rico': '🇵🇷',
            'Trinidad and Tobago': '🇹🇹', 'Barbados': '🇧🇧', 'Saint Lucia': '🇱🇨',
            'Grenada': '🇬🇩', 'Saint Vincent and the Grenadines': '🇻🇨',
            'Saint Kitts and Nevis': '🇰🇳', 'Dominica': '🇩🇲',

            'Morocco': '🇲🇦', 'Algeria': '🇩🇿', 'Tunisia': '🇹🇳', 'Libya': '🇱🇾',
            'Egypt': '🇪🇬', 'Sudan': '🇸🇩', 'Ethiopia': '🇪🇹', 'Kenya': '🇰🇪',
            'Uganda': '🇺🇬', 'Tanzania': '🇹🇿', 'Rwanda': '🇷🇼', 'Burundi': '🇧🇮',
            'Somalia': '🇸🇴', 'Djibouti': '🇩🇯', 'Madagascar': '🇲🇬', 'Mauritius': '🇲🇺',
            'Seychelles': '🇸🇨', 'Comoros': '🇰🇲', 'South Africa': '🇿🇦',
            'Namibia': '🇳🇦', 'Botswana': '🇧🇼', 'Zimbabwe': '🇿🇼', 'Zambia': '🇿🇲',
            'Mozambique': '🇲🇿', 'Malawi': '🇲🇼', 'Angola': '🇦🇴', 'Ghana': '🇬🇭',
            'Nigeria': '🇳🇬', 'Senegal': '🇸🇳', 'Mali': '🇲🇱', 'Burkina Faso': '🇧🇫',
            'Niger': '🇳🇪', 'Chad': '🇹🇩', 'Cameroon': '🇨🇲', 'Central African Republic': '🇨🇫',
            'Democratic Republic of the Congo': '🇨🇩', 'Republic of the Congo': '🇨🇬',
            'Gabon': '🇬🇦', 'Equatorial Guinea': '🇬🇶', 'Sao Tome and Principe': '🇸🇹',
            'Cape Verde': '🇨🇻', 'Guinea-Bissau': '🇬🇼', 'Guinea': '🇬🇳',
            'Sierra Leone': '🇸🇱', 'Liberia': '🇱🇷', 'Ivory Coast': '🇨🇮', 'Togo': '🇹🇬',
            'Benin': '🇧🇯',

            'Australia': '🇦🇺', 'New Zealand': '🇳🇿', 'Fiji': '🇫🇯', 'Papua New Guinea': '🇵🇬',
            'Solomon Islands': '🇸🇧', 'Vanuatu': '🇻🇺', 'New Caledonia': '🇳🇨',
            'French Polynesia': '🇵🇫', 'Samoa': '🇼🇸', 'Tonga': '🇹🇴', 'Tuvalu': '🇹🇻',
            'Kiribati': '🇰🇮', 'Nauru': '🇳🇷', 'Palau': '🇵🇼', 'Marshall Islands': '🇲🇭',
            'Micronesia': '🇫🇲', 'Cook Islands': '🇨🇰', 'Niue': '🇳🇺'
        }

    def extract_passport_info_tesseract(self, image_file):
        try:
            image = Image.open(image_file)
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(thresh, config='--psm 6')
            return self.parse_passport_text(text)

        except Exception as e:
            st.error(f"Tesseract OCR Error: {e}")
            return None

    def parse_passport_text(self, text):
        text = text.upper()

        country_patterns = [
            r'REPUBLIC OF ([A-Z\s]+)',
            r'UNITED STATES OF AMERICA',
            r'UNITED KINGDOM',
            r'PASSPORT\s+([A-Z\s]+)',
            r'NATIONALITY\s+([A-Z\s]+)',
            r'COUNTRY CODE\s+([A-Z]{3})',
        ]

        country_mapping = {
            'INDIA': 'India',
            'UNITED STATES OF AMERICA': 'United States',
            'UNITED KINGDOM': 'United Kingdom',
            'GERMANY': 'Germany',
            'FRANCE': 'France',
            'SINGAPORE': 'Singapore',
            'JAPAN': 'Japan',
            'AUSTRALIA': 'Australia',
            'CANADA': 'Canada',
        }

        for pattern in country_patterns:
            match = re.search(pattern, text)
            if match:
                country = match.group(1) if match.groups() else match.group(0)
                country = country.strip()
                if country in country_mapping:
                    return {'country': country_mapping[country], 'confidence': 0.8}

        for country_key, country_name in country_mapping.items():
            if country_key in text:
                return {'country': country_name, 'confidence': 0.6}

        return None

    def get_visa_free_countries(self, passport_country):
        if self.visa_data is None:
            st.error("Visa dataset not loaded")
            return []

        try:
            passport_country_clean = passport_country.strip()

            visa_free_data = self.visa_data[
                (self.visa_data['Passport'].str.strip().str.lower() == passport_country_clean.lower()) &
                (self.visa_data['Requirement'].str.contains('visa free|visa-free|visa on arrival', case=False, na=False))
            ]

            if visa_free_data.empty:
                visa_free_data = self.visa_data[
                    (self.visa_data['Passport'].str.contains(passport_country_clean, case=False, na=False)) &
                    (self.visa_data['Requirement'].str.contains('visa free|visa-free|visa on arrival', case=False, na=False))
                ]

            countries = sorted(visa_free_data['Destination'].unique().tolist())

            countries = [country for country in countries if country and str(country).strip()]

            st.success(f"Found {len(countries)} visa-free destinations for {passport_country_clean}")

            return countries

        except Exception as e:
            st.error(f"Error fetching visa-free countries: {e}")
            return []

passport_scanner = PassportScanner()

# Navigation Bar
col_nav = st.columns(4)
if col_nav[0].button("Travel Plan", key="nav_travel_plan", help="Plan your next trip"):
    st.session_state.current_page = "Travel Plan"
if col_nav[1].button("Passport", key="nav_passport", help="Find visa-free destinations based on your passport"):
    st.session_state.current_page = "Passport"
if col_nav[2].button("IVR Call", key="nav_ivr_call", help="Initiate a travel IVR call"):
    st.session_state.current_page = "IVR Call"
if col_nav[3].button("Contact Us", key="nav_contact_us", help="Get in touch with us"):
    st.session_state.current_page = "Contact Us"

st.markdown("---")

# Conditional Content Display
if st.session_state.current_page == "Travel Plan":
    st.subheader("Plan Your Adventure")

    col_plan1, col_plan2 = st.columns(2)
    with col_plan1:
        st.markdown("### Where are you headed?")
        destination_default = "DEL"
        if st.session_state.visa_free_countries:
            st.info(f"Tip: You can travel visa-free to {len(st.session_state.visa_free_countries)} countries!")

            popular_destinations = []
            if st.session_state.passport_country == 'India':
                popular_destinations = [country for country in ['Thailand', 'Singapore', 'Malaysia', 'UAE', 'Nepal']
                                          if country in st.session_state.visa_free_countries]
            elif st.session_state.passport_country == 'United States':
                popular_destinations = [country for country in ['United Kingdom', 'France', 'Germany', 'Japan', 'Canada']
                                          if country in st.session_state.visa_free_countries]

            if popular_destinations:
                st.write("Popular visa-free destinations for you:")
                dest_cols = st.columns(len(popular_destinations))
                for idx, dest in enumerate(popular_destinations):
                    with dest_cols[idx]:
                        flag = passport_scanner.country_flags.get(dest, '')
                        st.write(f"{flag} {dest}")

        source = st.text_input("Departure City (IATA Code):", "BOM")
        destination = st.text_input("Destination (IATA Code):", destination_default)

        num_days = st.slider("Trip Duration (days):", 1, 14, 5)
        travel_theme = st.selectbox("Select Your Travel Theme:", ["Couple Getaway", "Family Vacation", "Adventure Trip", "Solo Exploration"])

        activity_preferences = st.text_area("What activities do you enjoy?", "Relaxing on the beach, exploring historical sites")
        departure_date = st.date_input("Departure Date", min_value=datetime.today())
        return_date = st.date_input("Return Date", min_value=datetime.today())

    with col_plan2:
        st.subheader("Your Preferences")
        budget = st.radio("Budget Preference:", ["Economy", "Standard", "Luxury"])
        flight_class = st.radio("Flight Class:", ["Economy", "Business", "First Class"])
        hotel_rating = st.selectbox("Preferred Hotel Rating:", ["Any", "3", "4", "5"])

        # Hotel specific preferences
        num_guests = st.number_input("Number of Guests:", min_value=1, max_value=10, value=2)
        num_rooms = st.number_input("Number of Rooms:", min_value=1, max_value=5, value=1)

        st.subheader("Packing Checklist")
        packing_list = {
            "Clothes": True,
            "Comfortable Footwear": True,
            "Sunglasses & Sunscreen": False,
            "Travel Guidebook": False,
            "Medications & First-Aid": True
        }
        for item, checked in packing_list.items():
            st.checkbox(item, value=checked)

        st.subheader("Travel Essentials")
        visa_required_checkbox = st.checkbox("Check Visa Requirements")
        travel_insurance_checkbox = st.checkbox("Get Travel Insurance")
        currency_converter_checkbox = st.checkbox("Currency Exchange Rates")

    def format_datetime(iso_string):
        try:
            dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
            return dt.strftime("%b-%d, %Y | %I:%M %p")
        except:
            return "N/A"

def fetch_flights(source_iata, destination_iata, departure_date_obj, return_date_obj):
    params = {
        "engine": "google_flights",
        "departure_id": source_iata,
        "arrival_id": destination_iata,
        "outbound_date": str(departure_date_obj),
        "return_date": str(return_date_obj),
        "currency": "INR",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results

# Function to fetch hotel data
def fetch_hotels(destination, check_in_date, check_out_date, guests=2, rooms=1):
    # Map airport codes to actual city names for better hotel search
    airport_to_city = {
        'DEL': 'New Delhi', 'BOM': 'Mumbai', 'BLR': 'Bangalore', 
        'MAA': 'Chennai', 'CCU': 'Kolkata', 'HYD': 'Hyderabad',
        'GOI': 'Goa', 'JAI': 'Jaipur', 'AMD': 'Ahmedabad', 'COK': 'Kochi',
        'BKK': 'Bangkok', 'SIN': 'Singapore', 'KUL': 'Kuala Lumpur',
        'DXB': 'Dubai', 'DOH': 'Doha', 'NRT': 'Tokyo', 'ICN': 'Seoul',
        'LHR': 'London', 'CDG': 'Paris', 'FRA': 'Frankfurt', 'FCO': 'Rome',
        'MAD': 'Madrid', 'AMS': 'Amsterdam', 'ZUR': 'Zurich', 'VIE': 'Vienna',
        'JFK': 'New York', 'LAX': 'Los Angeles', 'YYZ': 'Toronto',
        'SYD': 'Sydney', 'MEL': 'Melbourne', 'AKL': 'Auckland'
    }
    
    # Convert airport code to city name if needed
    if len(destination) == 3 and destination.isupper():
        search_location = airport_to_city.get(destination.upper(), destination)
        st.info(f"Searching hotels in {search_location} (from airport code {destination})")
    else:
        search_location = destination
    
    try:
        # Add error handling and debugging
        st.write(f"🔍 Debug: Searching for hotels in '{search_location}'")
        st.write(f"📅 Check-in: {check_in_date}, Check-out: {check_out_date}")
        
        params = {
            "engine": "google_hotels",
            "q": search_location,
            "check_in_date": str(check_in_date),
            "check_out_date": str(check_out_date),
            "adults": guests,
            "rooms": rooms,
            "currency": "INR",
            "hl": "en",
            "gl": "in",
            "api_key": SERPAPI_KEY
        }
        
        # Debug: Show API parameters (remove API key from display)
        debug_params = params.copy()
        debug_params["api_key"] = "***HIDDEN***"
        st.write(f"🔧 Debug: API Parameters: {debug_params}")
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Debug: Show raw results structure
        st.write(f"📊 Debug: API Response keys: {list(results.keys())}")
        
        # Check for errors in the API response
        if "error" in results:
            st.error(f"SerpAPI Error: {results['error']}")
            return {"properties": []}
        
        # Get properties with better error handling
        properties = results.get("properties", [])
        
        if not properties:
            st.warning(f"⚠️ No properties found in API response for {search_location}")
            # Try alternative search without date restrictions
            fallback_params = {
                "engine": "google_hotels",
                "q": search_location,
                "currency": "INR",
                "hl": "en",
                "gl": "in",
                "api_key": SERPAPI_KEY
            }
            st.info("🔄 Trying fallback search without dates...")
            fallback_search = GoogleSearch(fallback_params)
            fallback_results = fallback_search.get_dict()
            properties = fallback_results.get("properties", [])
        
        # Filter out vacation rentals and keep only hotels
        hotel_properties = []
        
        for prop in properties:
            prop_type = prop.get("type", "").lower()
            # Be more lenient with property types
            if prop_type not in ["vacation rental", "apartment", "house", "condo", "villa"]:
                hotel_properties.append(prop)
        
        # If still no hotels, be even more lenient
        if not hotel_properties and properties:
            st.info("🏨 Using all available properties (including vacation rentals)")
            hotel_properties = properties[:6]  # Limit to first 6
        
        st.success(f"✅ Found {len(hotel_properties)} properties in {search_location}")
        return {"properties": hotel_properties}
        
    except Exception as e:
        st.error(f"❌ Error fetching hotels: {str(e)}")
        st.error(f"🔍 Error type: {type(e).__name__}")
        
        # Return empty but valid structure
        return {"properties": []}

def extract_cheapest_flights(flight_data):
    best_flights = flight_data.get("best_flights", [])
    return sorted(best_flights, key=lambda x: x.get("price", float("inf")))[:3]

def extract_top_hotels(hotel_data):
    """Extract and sort hotels with better error handling"""
    try:
        properties = hotel_data.get("properties", [])
        
        if not properties:
            st.warning("⚠️ No hotel properties found in data")
            return []
        
        st.write(f"🏪 Processing {len(properties)} properties...")
        
        # Filter hotels with valid data
        valid_hotels = []
        
        for i, hotel in enumerate(properties):
            try:
                # Basic validation
                hotel_name = hotel.get("name", f"Property {i+1}")
                
                # Handle different price structures
                price_numeric = 0
                rate_info = hotel.get("rate_per_night", {})
                
                if rate_info:
                    # Try different price fields
                    price_str = (rate_info.get("extracted_lowest") or 
                               rate_info.get("lowest") or 
                               rate_info.get("rate") or "0")
                    
                    try:
                        # Extract numeric value from price string
                        if isinstance(price_str, (int, float)):
                            price_numeric = float(price_str)
                        else:
                            # Remove currency symbols and extract numbers
                            import re
                            numbers = re.findall(r'\d+\.?\d*', str(price_str).replace(',', ''))
                            if numbers:
                                price_numeric = float(numbers[0])
                    except (ValueError, TypeError, IndexError):
                        price_numeric = 0
                
                # Add processed data
                hotel["price_numeric"] = price_numeric
                hotel["processed_name"] = hotel_name
                
                # Only add hotels with names
                if hotel_name and hotel_name != "Property":
                    valid_hotels.append(hotel)
                    
            except Exception as hotel_error:
                st.warning(f"⚠️ Error processing hotel {i}: {hotel_error}")
                continue
        
        st.write(f"✅ {len(valid_hotels)} valid hotels after processing")
        
        if not valid_hotels:
            return []
        
        # Sort by rating (desc) then by price (asc)
        try:
            sorted_hotels = sorted(
                valid_hotels, 
                key=lambda x: (
                    -float(x.get("overall_rating", 0) or 0), 
                    x.get("price_numeric", float("inf"))
                )
            )[:6]  # Get top 6 instead of 3 for better selection
            
            st.success(f"🎯 Returning top {len(sorted_hotels)} hotels")
            return sorted_hotels
            
        except Exception as sort_error:
            st.error(f"❌ Error sorting hotels: {sort_error}")
            # Return first few hotels without sorting
            return valid_hotels[:3]
            
    except Exception as e:
        st.error(f"❌ Error extracting hotels: {str(e)}")
        return []
    
def display_hotels_safely(top_hotels):
    """Display hotels with comprehensive error handling"""
    
    if not top_hotels:
        st.warning("😔 No hotels available to display")
        
        with st.expander("🔧 Troubleshooting Tips"):
            st.write("""
            **Possible reasons:**
            - API quota exceeded
            - Invalid destination
            - Network connectivity issues
            - Date format problems
            
            **Try:**
            - Use city name instead of airport code
            - Check your internet connection
            - Try different dates
            - Contact support if issue persists
            """)
        return
    
    st.subheader(f"🏨 Top {len(top_hotels)} Hotel Recommendations")
    
    # Display hotels in columns
    num_hotels = min(len(top_hotels), 3)
    cols = st.columns(num_hotels)
    
    for idx, hotel in enumerate(top_hotels[:3]):
        with cols[idx]:
            try:
                # Safe data extraction with fallbacks
                hotel_name = hotel.get("processed_name") or hotel.get("name", f"Hotel {idx+1}")
                
                # Image handling
                hotel_images = hotel.get("images", [])
                hotel_image = ""
                if hotel_images and isinstance(hotel_images, list) and len(hotel_images) > 0:
                    first_image = hotel_images[0]
                    if isinstance(first_image, dict):
                        hotel_image = first_image.get("thumbnail", "") or first_image.get("original", "")
                
                # Display image or placeholder
                if hotel_image and hotel_image.startswith("http"):
                    try:
                        st.image(hotel_image, width=300, caption=hotel_name)
                    except:
                        st.info("🏨 Image unavailable")
                else:
                    st.info("🏨 No image available")
                
                # Hotel name
                st.markdown(f"**{hotel_name}**")
                
                # Rating with safe conversion
                rating = hotel.get("overall_rating")
                reviews_count = hotel.get("reviews", 0)
                
                if rating:
                    try:
                        rating_float = float(rating)
                        if rating_float > 0:
                            st.write(f"⭐ **{rating_float}/5** ({reviews_count} reviews)")
                    except (ValueError, TypeError):
                        if reviews_count > 0:
                            st.write(f"📝 {reviews_count} reviews")
                
                # Price display
                price_numeric = hotel.get("price_numeric", 0)
                if price_numeric > 0:
                    st.write(f"💰 **₹{price_numeric:,.0f}** per night")
                else:
                    # Try alternative price fields
                    rate_info = hotel.get("rate_per_night", {})
                    if rate_info:
                        price_display = rate_info.get("extracted_lowest") or rate_info.get("lowest", "Contact for price")
                        st.write(f"💰 **{price_display}**")
                    else:
                        st.write("💰 **Contact for price**")
                
                # Hotel type
                hotel_type = hotel.get("type", "Hotel").title()
                st.write(f"🏢 *{hotel_type}*")
                
                # Amenities
                amenities = hotel.get("amenities", [])
                if amenities and isinstance(amenities, list):
                    amenities_text = ", ".join(amenities[:3])
                    st.write(f"🎯 {amenities_text}")
                
                # Booking link
                hotel_link = hotel.get("link", "")
                if not hotel_link:
                    # Create Google search link as fallback
                    hotel_search_query = hotel_name.replace(" ", "+")
                    hotel_link = f"https://www.google.com/search?q={hotel_search_query}+hotel+booking"
                
                st.link_button("🔗 View Details", hotel_link)
                
                # Additional details in expander
                with st.expander("ℹ️ More Details"):
                    if hotel.get("neighborhood"):
                        st.write(f"📍 **Location:** {hotel.get('neighborhood')}")
                    
                    if len(amenities) > 3:
                        st.write(f"🏨 **All Amenities:** {', '.join(amenities)}")
                    
                    description = hotel.get("description", "")
                    if description:
                        st.write(f"📋 **Description:** {description}")
                    
                    # Debug info (remove in production)
                    if st.checkbox(f"🔧 Debug Hotel {idx+1}", key=f"debug_hotel_{idx}"):
                        st.json(hotel)
                
            except Exception as hotel_display_error:
                st.error(f"❌ Error displaying hotel {idx+1}: {hotel_display_error}")
                st.write("🏨 Hotel information unavailable")

def get_destination_country(iata_code):
    iata_to_country = {
        'DEL': 'India', 'BOM': 'India', 'BLR': 'India', 'MAA': 'India',
        'BKK': 'Thailand', 'SIN': 'Singapore', 'KUL': 'Malaysia',
        'DXB': 'UAE', 'DOH': 'Qatar', 'KTM': 'Nepal', 'CMB': 'Sri Lanka',
        'NRT': 'Japan', 'ICN': 'South Korea', 'TPE': 'Taiwan',
        'LHR': 'United Kingdom', 'CDG': 'France', 'FRA': 'Germany',
        'FCO': 'Italy', 'MAD': 'Spain', 'AMS': 'Netherlands',
        'ZUR': 'Switzerland', 'VIE': 'Austria', 'ARN': 'Sweden',
        'CPH': 'Denmark', 'OSL': 'Norway', 'HEL': 'Finland',
        'JFK': 'United States', 'LAX': 'United States', 'YYZ': 'Canada',
        'SYD': 'Australia', 'MEL': 'Australia', 'AKL': 'New Zealand'
    }
    return iata_to_country.get(iata_code.upper(), 'Unknown')

researcher = Agent(
    name="Researcher",
    instructions=[
        "Identify destination, research climate, safety, top attractions, and activities.",
        "Use reliable sources and summarize results clearly."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[SerpApiTools(api_key=SERPAPI_KEY)],
    add_datetime_to_instructions=True,
)

planner = Agent(
    name="Planner",
    instructions=[
        "Create a detailed itinerary with travel preferences, time estimates, and budget alignment."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

hotel_restaurant_finder = Agent(
    name="Hotel & Restaurant Finder",
    instructions=[
        "Find top-rated hotels and restaurants near main attractions. Include booking links if possible."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[SerpApiTools(api_key=SERPAPI_KEY)],
    add_datetime_to_instructions=True,
)

if st.button("Generate Travel Plan"):
    visa_status = "Unknown"
    destination_country = get_destination_country(destination)

    if st.session_state.passport_country and st.session_state.visa_free_countries:
        if destination_country in st.session_state.visa_free_countries:
            visa_status = "Visa-Free"
        elif destination_country != 'Unknown':
            visa_status = "Visa Required"
        else:
            visa_status = "Check visa requirements"

    if visa_status == "Visa-Free":
        st.success(f"Great news! {visa_status} travel to {destination_country}")
    elif visa_status == "Visa Required":
        st.warning(f"{visa_status} for {destination_country} - Please check visa requirements")
    else:
        st.info(f"{visa_status} for {destination_country}")

    with st.spinner("Fetching best flight options..."):
        flight_data = fetch_flights(source, destination, departure_date, return_date)
        cheapest_flights = extract_cheapest_flights(flight_data)

    with st.spinner("🔍 Searching for the best hotels..."):
        try:
            hotel_data = fetch_hotels(destination, departure_date, return_date, num_guests, num_rooms)
            top_hotels = extract_top_hotels(hotel_data)
            
            # Display hotels using the safe function
            display_hotels_safely(top_hotels)
            
        except Exception as hotel_error:
            st.error(f"❌ Hotel search failed: {hotel_error}")
            st.info("🏨 Please try manual hotel search or contact support")

    with st.spinner("Researching best attractions & activities..."):
        research_prompt = (
            f"Research top attractions in {destination} for a {num_days}-day {travel_theme.lower()} trip. "
            f"Interests: {activity_preferences}. Budget: {budget}. Class: {flight_class}. Rating: {hotel_rating}."
        )
        research_results = researcher.run(research_prompt, stream=False)

    with st.spinner("Searching for hotels & restaurants..."):
        hotel_restaurant_prompt = (
            f"Recommend hotels and restaurants in {destination} for a {travel_theme.lower()} trip. "
            f"Preferences: {activity_preferences}. Budget: {budget}. Hotel Rating: {hotel_rating}."
        )
        hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)

    with st.spinner("Creating itinerary..."):
        planning_prompt = (
            f"Create a {num_days}-day travel itinerary to {destination} for a {travel_theme.lower()} trip. "
            f"Preferences: {activity_preferences}. Budget: {budget}. Class: {flight_class}. Rating: {hotel_rating}. "
            f"Research: {research_results.content}. Flights: {json.dumps(cheapest_flights)}. "
            f"Hotels: {json.dumps(top_hotels)}. Restaurants: {hotel_restaurant_results.content}."
        )
        itinerary = planner.run(planning_prompt, stream=False)

    st.subheader("Cheapest Flight Options")
    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
                airline_logo = flight.get("airline_logo", "")
                airline_name = flight.get("airline", "Unknown Airline")
                price = flight.get("price", "Not Available")
                total_duration_minutes = flight.get("total_duration", "N/A")

                flights_details = flight.get("flights", [{}])
                departure_airport_info = flights_details[0].get("departure_airport", {})
                arrival_airport_info = flights_details[-1].get("arrival_airport", {})

                departure_time = format_datetime(departure_airport_info.get("time", "N/A"))
                arrival_time = format_datetime(arrival_airport_info.get("time", "N/A"))
                
                booking_link = flight.get("link", f"https://www.google.com/flights?q={source}+{destination}")

                st.markdown(
                    f"""
                    <div class="flight-card">
                        <img src="{airline_logo}" alt="Airline Logo" />
                        <h3>{airline_name}</h3>
                        <p><strong>Departure:</strong> {departure_time}</p>
                        <p><strong>Arrival:</strong> {arrival_time}</p>
                        <p><strong>Duration:</strong> {total_duration_minutes} min</p>
                        <div class="price">₹ {price}</div>
                        <a href="{booking_link}" target="_blank" class="book-now-link">Book Now</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("No flight data available.")

    # Enhanced Hotel Display Results - Using Native Streamlit Components
    st.subheader(f"🏨 Top {len(top_hotels)} Hotel Recommendations")
    
    # Display hotels in columns
    num_hotels = min(len(top_hotels), 3)
    cols = st.columns(num_hotels)
    
    for idx, hotel in enumerate(top_hotels[:3]):
        with cols[idx]:
            try:
                # Safe data extraction with fallbacks
                hotel_name = hotel.get("processed_name") or hotel.get("name", f"Hotel {idx+1}")
                
                # Image handling
                hotel_images = hotel.get("images", [])
                hotel_image = ""
                if hotel_images and isinstance(hotel_images, list) and len(hotel_images) > 0:
                    first_image = hotel_images[0]
                    if isinstance(first_image, dict):
                        hotel_image = first_image.get("thumbnail", "") or first_image.get("original", "")
                
                # Display image or placeholder
                if hotel_image and hotel_image.startswith("http"):
                    try:
                        st.image(hotel_image, width=300, caption=hotel_name)
                    except:
                        st.info("🏨 Image unavailable")
                else:
                    st.info("🏨 No image available")
                
                # Hotel name
                st.markdown(f"**{hotel_name}**")
                
                # Rating with safe conversion
                rating = hotel.get("overall_rating")
                reviews_count = hotel.get("reviews", 0)
                
                if rating:
                    try:
                        rating_float = float(rating)
                        if rating_float > 0:
                            st.write(f"⭐ **{rating_float}/5** ({reviews_count} reviews)")
                    except (ValueError, TypeError):
                        if reviews_count > 0:
                            st.write(f"📝 {reviews_count} reviews")
                
                # Price display
                price_numeric = hotel.get("price_numeric", 0)
                if price_numeric > 0:
                    st.write(f"💰 **₹{price_numeric:,.0f}** per night")
                else:
                    # Try alternative price fields
                    rate_info = hotel.get("rate_per_night", {})
                    if rate_info:
                        price_display = rate_info.get("extracted_lowest") or rate_info.get("lowest", "Contact for price")
                        st.write(f"💰 **{price_display}**")
                    else:
                        st.write("💰 **Contact for price**")
                
                # Hotel type
                hotel_type = hotel.get("type", "Hotel").title()
                st.write(f"🏢 *{hotel_type}*")
                
                # Amenities
                amenities = hotel.get("amenities", [])
                if amenities and isinstance(amenities, list):
                    amenities_text = ", ".join(amenities[:3])
                    st.write(f"🎯 {amenities_text}")
                
                # Booking link
                hotel_link = hotel.get("link", "")
                if not hotel_link:
                    # Create Google search link as fallback
                    hotel_search_query = hotel_name.replace(" ", "+")
                    hotel_link = f"https://www.google.com/search?q={hotel_search_query}+hotel+booking"
                
                st.link_button("🔗 View Details", hotel_link)
                
                # Additional details in expander
                with st.expander("ℹ️ More Details"):
                    if hotel.get("neighborhood"):
                        st.write(f"📍 **Location:** {hotel.get('neighborhood')}")
                    
                    if len(amenities) > 3:
                        st.write(f"🏨 **All Amenities:** {', '.join(amenities)}")
                    
                    description = hotel.get("description", "")
                    if description:
                        st.write(f"📋 **Description:** {description}")
                    
                    # Debug info (remove in production)
                    if st.checkbox(f"🔧 Debug Hotel {idx+1}", key=f"debug_hotel_{idx}"):
                        st.json(hotel)
                
            except Exception as hotel_display_error:
                st.error(f"❌ Error displaying hotel {idx+1}: {hotel_display_error}")
                st.write("🏨 Hotel information unavailable")

    st.subheader("Restaurants & Local Experiences")
    st.write(hotel_restaurant_results.content)

    st.subheader("Your Personalized Itinerary")
    st.write(itinerary.content)

    st.success("Travel plan generated successfully!")



elif st.session_state.current_page == "Passport":
    st.markdown("""
        <div class="passport-scan">
            <h2 style="color: white; text-align: center;">Passport Scanner</h2>
            <p style="color: white; text-align: center;">Upload your passport photo to discover visa-free travel destinations!</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Upload Passport Photo")
        uploaded_file = st.file_uploader(
            "Choose passport image...",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear photo of your passport's main page"
        )

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Passport", use_column_width=True)

            if st.button("Scan Passport"):
                with st.spinner("Scanning passport..."):
                    uploaded_file.seek(0)

                    passport_info = passport_scanner.extract_passport_info_tesseract(uploaded_file)

                    if passport_info:
                        st.session_state.passport_country = passport_info['country']
                        st.success(f"Passport detected: {passport_info['country']} (Confidence: {passport_info['confidence']:.1%})")

                        with st.spinner("Finding visa-free destinations..."):
                            visa_free = passport_scanner.get_visa_free_countries(passport_info['country'])
                            st.session_state.visa_free_countries = visa_free

                    else:
                        st.error("Could not extract passport information. Please try a clearer image.")

    with col2:
        st.subheader("Manual Country Selection")
        st.write("Or select your passport country manually:")

        available_countries = []
        if passport_scanner.visa_data is not None:
            available_countries = sorted(passport_scanner.visa_data['Passport'].unique().tolist())
        else:
            available_countries = [
                'India', 'United States', 'United Kingdom', 'Germany', 'France',
                'Singapore', 'Japan', 'Australia', 'Canada', 'Netherlands',
                'Switzerland', 'Sweden', 'Norway', 'Denmark', 'Finland'
            ]

        selected_country = st.selectbox("Select your passport country:", [''] + available_countries)

        if selected_country and st.button("Find Visa-Free Countries"):
            st.session_state.passport_country = selected_country
            with st.spinner("Finding visa-free destinations..."):
                visa_free = passport_scanner.get_visa_free_countries(selected_country)
                st.session_state.visa_free_countries = visa_free

    if st.session_state.passport_country and st.session_state.visa_free_countries:
        st.markdown("---")
        st.subheader(f"Visa-Free Destinations for {st.session_state.passport_country} Passport Holders")

        st.info(f"Great news! You can travel to {len(st.session_state.visa_free_countries)} countries visa-free!")

        search_country = st.text_input("Search countries:", placeholder="Type to filter countries...")

        filtered_countries = st.session_state.visa_free_countries
        if search_country:
            filtered_countries = [country for country in st.session_state.visa_free_countries
                                  if search_country.lower() in country.lower()]
            st.write(f"Found {len(filtered_countries)} countries matching '{search_country}'")

        if filtered_countries:
            cols = st.columns(4)
            for idx, country in enumerate(filtered_countries):
                col_idx = idx % 4
                with cols[col_idx]:
                    flag = passport_scanner.country_flags.get(country, '')

                    st.markdown(f"""
                        <div class="visa-free-card">
                            <div class="country-name">{flag} {country}</div>
                            <div class="visa-status">Visa-Free Entry</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.write("No countries found matching your search.")

        st.markdown("### Regional Breakdown")

        asia_countries = ['Thailand', 'Singapore', 'Malaysia', 'Indonesia', 'Philippines',
                          'Cambodia', 'Laos', 'Myanmar', 'Vietnam', 'Brunei', 'Nepal', 'Bhutan',
                          'South Korea', 'Japan', 'Mongolia', 'Kazakhstan', 'Kyrgyzstan',
                          'Tajikistan', 'Uzbekistan']

        europe_countries = ['Germany', 'France', 'Italy', 'Spain', 'United Kingdom', 'Ireland',
                            'Netherlands', 'Belgium', 'Switzerland', 'Austria', 'Portugal',
                            'Greece', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Iceland',
                            'Poland', 'Czech Republic', 'Slovakia', 'Hungary', 'Slovenia',
                            'Croatia', 'Serbia', 'Montenegro', 'Albania', 'North Macedonia',
                            'Bosnia and Herzegovina', 'Bulgaria', 'Romania', 'Moldova', 'Belarus']

        middle_east_countries = ['UAE', 'Qatar', 'Oman', 'Kuwait', 'Bahrain', 'Saudi Arabia',
                                 'Jordan', 'Turkey', 'Armenia', 'Georgia', 'Iran', 'Israel']

        africa_countries = ['Mauritius', 'Seychelles', 'Madagascar', 'Comoros', 'Cape Verde',
                            'Guinea-Bissau', 'Mozambique', 'Zimbabwe', 'Zambia', 'Uganda',
                            'Rwanda', 'Burundi', 'Tanzania', 'Kenya', 'Ethiopia', 'Djibouti',
                            'Somalia', 'Sudan', 'Egypt', 'Morocco', 'Tunisia', 'South Africa',
                            'Namibia', 'Botswana']

        americas_countries = ['United States', 'Canada', 'Mexico', 'Brazil', 'Argentina',
                              'Chile', 'Uruguay', 'Paraguay', 'Colombia', 'Ecuador', 'Peru',
                              'Bolivia', 'Venezuela', 'Guyana', 'Suriname', 'Jamaica', 'Haiti',
                              'Barbados', 'Trinidad and Tobago', 'Dominica', 'Grenada',
                              'Saint Lucia', 'Saint Vincent and the Grenadines',
                              'Saint Kitts and Nevis', 'El Salvador', 'Honduras', 'Nicaragua']

        oceania_countries = ['Australia', 'New Zealand', 'Fiji', 'Vanuatu', 'Samoa', 'Tonga',
                             'Cook Islands', 'Niue', 'Tuvalu', 'Micronesia', 'Papua New Guinea']

        asia_count = sum(1 for country in st.session_state.visa_free_countries if country in asia_countries)
        europe_count = sum(1 for country in st.session_state.visa_free_countries if country in europe_countries)
        middle_east_count = sum(1 for country in st.session_state.visa_free_countries if country in middle_east_countries)
        africa_count = sum(1 for country in st.session_state.visa_free_countries if country in africa_countries)
        americas_count = sum(1 for country in st.session_state.visa_free_countries if country in americas_countries)
        oceania_count = sum(1 for country in st.session_state.visa_free_countries if country in oceania_countries)

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Asia", asia_count)
        with col2:
            st.metric("Europe", europe_count)
        with col3:
            st.metric("Middle East", middle_east_count)
        with col4:
            st.metric("Africa", africa_count)
        with col5:
            st.metric("Americas", americas_count)
        with col6:
            st.metric("Oceania", oceania_count)

elif st.session_state.current_page == "IVR Call":
    st.subheader("Initiate Travel IVR Call")

    FASTAPI_IVR_URL = "https://7da53dd2a6d8.ngrok-free.app/start-call"

    user_phone = st.text_input("Enter your phone number (with country code)", "+91XXXXXXXXXX")

    if st.button("Start Call"):
        if user_phone.startswith("+91") and len(user_phone) == 13:
            with st.spinner("Calling..."):
                try:
                    response = requests.post(FASTAPI_IVR_URL, json={"to_number": user_phone})
                    result = response.json()
                    if result.get("success"):
                        st.success(f"Call initiated successfully! SID: {result['sid']}")
                    else:
                        st.error("Call initiation failed.")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a valid Indian phone number starting with +91.")

elif st.session_state.current_page == "Contact Us":
    st.header("Save Your Plan / Contact Us")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")

    def send_to_vendasta(first_name, last_name, email, phone):
        payload = {
            "firstName": first_name,
            "secondName": last_name,
            "email": email,
            "phone": phone
        }
        try:
            res = requests.post(
                "https://automations.businessapp.io/start/LCZN/75206877-c089-4a69-a881-9df69c75ff71",
                json=payload
            )
            if res.status_code == 200:
                st.success("Info sent to our CRM!")
            else:
                st.error(f"Failed. Status code: {res.status_code}")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.button("Send My Info"):
        if all([first_name, last_name, email, phone]):
            send_to_vendasta(first_name, last_name, email, phone)
        else:
            st.warning("Please complete all fields.")

# Twilio credentials for Emergency & Offline Support
TWILIO_SID = "ACa84b12a3d81d88e62b1d06d29cfd4f18"
TWILIO_AUTH_TOKEN = "10fce4b0ecc25047497dbbbdd485e8a4"
TWILIO_WHATSAPP = "whatsapp:+14155238886"  # Twilio sandbox number
emergency_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

st.markdown("## 🛡️ Emergency & Offline Support")

user_whatsapp = st.text_input("📱 Enter your WhatsApp number (with +91)", "+91")

col1, col2 = st.columns(2)

with col1:
    if st.button("🚨 Simulate Flight Cancellation Alert"):
        if user_whatsapp.startswith("+91") and len(user_whatsapp) == 13:
            try:
                message = emergency_client.messages.create(
                    from_=TWILIO_WHATSAPP,
                    to=f"whatsapp:{user_whatsapp}",
                    body="🚨 [Emergency] Your flight AI302 has been CANCELLED. Please check your email for rebooking or call +91-9999999999 for help."
                )
                st.success("Emergency WhatsApp alert sent successfully!")
            except Exception as e:
                st.error(f"Error sending WhatsApp message: {e}")
        else:
            st.warning("Please enter a valid WhatsApp number.")

with col2:
    if st.button("📴 Simulate Offline Fallback"):
        st.info("It seems you're offline or unable to access live assistance.")
        try:
            message = emergency_client.messages.create(
                from_=TWILIO_WHATSAPP,
                to=f"whatsapp:{user_whatsapp}",
                body="📴 [Fallback] Our systems are temporarily offline. For urgent help, call +91-9999999999 or visit your nearest airline office."
            )
            st.success("Offline fallback message sent to WhatsApp!")
        except Exception as e:
            st.error(f"Could not send fallback message: {e}")
