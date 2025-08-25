import json, re

# ----------------------------------------------------------------------
#  Set the paths that make sense on your machine
# ----------------------------------------------------------------------
input_path  = r"c:\Users\omarh\OneDrive\Documents\GitHub\NewsScraper\user_extras.json"
output_path = r"c:\Users\omarh\OneDrive\Documents\GitHub\NewsScraper\lookup_worthy.json"

# ----------------------------------------------------------------------
#  Helper: decide if the string is "lookup-worthy"
# ----------------------------------------------------------------------
def is_lookup_worthy(s: str) -> bool:
    s = s.strip()
    if not s:
        return False

    # 1. KEEP short ALL-CAPS abbreviations (≤ 4 letters)
    if re.fullmatch(r"[A-Z\s]+", s):
        return len(s.replace(" ", "")) <= 4

    # 2. DROP obvious connective fragments (tweak if these matter to you)
    stop_prefixes = (
        "In ", "By ", "On ", "When ", "While ", "If ", "During ", "Since ",
        "Until ", "Because ", "After ", "For ", "From ", "Between ", "Among "
    )
    if s.startswith(stop_prefixes):
        return False

    words = s.split()

    # 3. KEEP embedded abbreviations (NASA, WHO, GDP …)
    if any(w.isupper() and 2 <= len(w) <= 5 for w in words):
        return True

    # 4. KEEP proper-noun phrases with ≥ 2 capitalised words
    if len(words) >= 2 and sum(w[0].isupper() for w in words) >= 2:
        return True

    # 5. KEEP a single capitalised word (likely a person or brand)
    if len(words) == 1 and re.match(r"[A-Z][a-z]{2,}", words[0]):
        return True

    # 6. KEEP if it mentions an organisation keyword
    org_keywords = (
        "University", "College", "Institute", "Hospital", "Association",
        "Ministry", "Council", "Committee", "Bank", "Federation", "Board",
        "Court", "Museum", "Academy", "Press", "Service", "Department",
        "Agency", "Company", "Group", "Party", "Center", "Centre"
    )
    if any(k in s for k in org_keywords):
        return True

    # 7. KEEP if it has a title keyword (President, Dr …, Professor …, etc.)
    title_keywords = (
        "President", "Prime Minister", "Senator", "Secretary", "Justice",
        "Minister", "Governor", "Mayor", "Chancellor", "Chief", "Judge",
        "King", "Queen", "Emperor", "General", "Professor", "Dr", "Ambassador"
    )
    if any(k in s for k in title_keywords):
        return True

    # 8. KEEP if it contains a famous tech-brand keyword
    brand_keywords = (
        # ––– US “Big Tech” & FAANG/MANA –––
        "Apple", "Google", "Alphabet", "Microsoft", "Amazon", "Meta", "Facebook",
        "Instagram", "WhatsApp", "Nvidia", "Intel", "AMD", "IBM", "Oracle",
        "Cisco", "Dell", "HP", "Hewlett-Packard", "Lenovo", "Qualcomm",
        "Broadcom", "Salesforce", "Adobe", "PayPal", "Stripe", "Square", "Block",
        "Shopify", "Snap", "Spotify", "Netflix", "Uber", "Lyft", "Airbnb",
        "Zoom", "Atlassian", "Slack", "GitHub", "Red Hat", "DigitalOcean",
        "Cloudflare", "Snowflake", "Databricks", "Twilio", "MongoDB",
        # ––– Social media / comms –––
        "TikTok", "ByteDance", "X", "Twitter", "Reddit", "Discord", "Telegram",
        "Signal", "WeChat",
        # ––– Asian & global giants –––
        "Samsung", "LG", "Sony", "Panasonic", "Fujitsu", "SoftBank",
        "Tencent", "Alibaba", "Baidu", "JD.com", "Meituan", "Xiaomi", "Huawei",
        "ZTE", "Oppo", "Vivo", "Mahindra", "Infosys", "TCS", "Wipro", "Reliance",
        # ––– Chip / semi & EDA –––
        "TSMC", "ASML", "Arm", "Imagination", "GlobalFoundries", "Cadence",
        "Synopsys", "Raspberry Pi",
        # ––– Cloud & infra –––
        "AWS", "Azure", "Google Cloud", "GCP", "Oracle Cloud", "IBM Cloud",
        "Alibaba Cloud", "Linode", "OVH",
        # ––– Fintech & payments –––
        "Coinbase", "Robinhood", "Binance", "Kraken", "Payoneer", "Wise",
        "Ant Group", "Adyen", "Revolut", "Nubank",
        # ––– Hardware / EV / aerospace crossovers –––
        "Tesla", "SpaceX", "Neuralink", "The Boring Company", "Blue Origin",
        "Virgin Galactic", "DJI", "Boston Dynamics",
        # ––– Enterprise SaaS & dev tools –––
        "Confluent", "Elastic", "HashiCorp", "Kubernetes", "Docker", "Grafana",
        "New Relic", "Datadog", "Sentry", "Jira", "Bitbucket", "PagerDuty",
        "Okta", "Auth0", "MuleSoft", "Zendesk", "ServiceNow",
        # ––– Gaming & XR –––
        "Valve", "Steam", "Epic Games", "Unity", "Unreal Engine", "Roblox",
        "Nintendo", "PlayStation", "Xbox", "HTC Vive", "Oculus", "Quest",
        # ––– AI / deep-tech specialist firms –––
        "OpenAI", "Anthropic", "DeepMind", "Stability AI", "Hugging Face",
        "Midjourney", "Runway", "Character AI", "Graphcore", "Cerebras",
    )
    if any(k in s for k in brand_keywords):
        return True

    # 9. KEEP if the whole string is exactly a recognised country name
    countries = {
        # UN members + observers (+ Taiwan)  – alphabetical
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
        "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
        "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
        "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia",
        "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
        "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon",
        "Canada", "Central African Republic", "Chad", "Chile", "China",
        "Colombia", "Comoros", "Congo", "Costa Rica", "Côte d'Ivoire",
        "Croatia", "Cuba", "Cyprus", "Czechia", "Democratic Republic of the Congo",
        "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador",
        "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia",
        "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon",
        "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada",
        "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras",
        "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
        "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya",
        "Kiribati", "Korea (North)", "Korea (South)", "Kuwait", "Kyrgyzstan",
        "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
        "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi",
        "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
        "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco",
        "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
        "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua",
        "Niger", "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan",
        "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru",
        "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia",
        "Rwanda", "Saint Kitts and Nevis", "Saint Lucia",
        "Saint Vincent and the Grenadines", "Samoa", "San Marino",
        "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
        "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
        "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain",
        "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
        "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo",
        "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan",
        "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
        "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu",
        "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe", "Hong Kong",
        "Macau", "Kosovo", "Palau", "Sahrawi Arab Democratic Republic", "Taiwan","Puerto Rico"
    }
    if s in countries:
        return True

    return False

# ----------------------------------------------------------------------
#  MAIN: read, filter, write
# ----------------------------------------------------------------------
with open(input_path, "r") as f:
    data = json.load(f)

filtered = [s for s in data if is_lookup_worthy(s)]

with open(output_path, "w") as f:
    json.dump(filtered, f, indent=2)