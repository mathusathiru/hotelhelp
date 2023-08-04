import requests
import bcrypt
import config


def enter_query(query):
    try:
        if len(query) < 2:
            return None, "Error: query is too short (2+ characters needed)"
        return query, None
    except Exception as e:
        return None, str(e)


def generate_checkboxes():
    try:
        categories_dict = {
            "Arts and Entertainment": 10000,
            "Community": 12000,
            "Dining and Drinking": 13000,
            "Events": 14000,
            "Landmarks and Outdoors": 16000,
            "Retail": 17000,
            "Sports": 18000,
            "Travel and Transportation": 19000,
        }

        checkboxes_str = ''

        for name, id in categories_dict.items():
            checkbox_str = f"<input type='checkbox' name='categories' value='{id}'>{name}<br>"
            checkboxes_str += checkbox_str

        return checkboxes_str
    except Exception as e:
        return str(e)


def get_coordinates(search):
    try:
        base_url = "https://api.opencagedata.com/geocode/v1/json"
        url = base_url + "?q=" + search + "&key=" + config.key1
        response = requests.get(url)
        data = response.json()
        status_code = int(data["status"]["code"])
        if status_code == 200:
            if data["total_results"] == 1:
                result = data["results"][0]
                latitude = result["geometry"]["lat"]
                longitude = result["geometry"]["lng"]
                return latitude, longitude, None
            elif data["total_results"] == 0:
                return None, None, "Error: Location not found. Please use a valid location."
            else:
                return None, None, "Error: Multiple locations or invalid location found. Check for misspellings or provide a more specific location."
        else:
            return None, None, f"Error {status_code}: {data['status']['message']}"
    except Exception as e:
        return None, None, str(e)


def get_destinations(latitude, longitude, categories_str, c, conn, user_id):
    try:
        url = "https://api.foursquare.com/v3/places/search"
        header = {"accept": "application/json", "Authorization": config.key2}
        param_dict = {"ll": str(latitude) + "," + str(longitude),
                      "sort": "DISTANCE",
                      "radius": 5000,
                      "categories": categories_str}
        response = requests.get(url, params=param_dict, headers=header)
        data = response.json()

        filtered_results = []
        if "results" in data:
            for result in data["results"]:
                location = result.get("location", {})
                formatted_address = location.get("formatted_address")
                if formatted_address is not None:
                    filtered_results.append(result)

        if user_id is not None:
            save_search_history(c, conn, user_id, filtered_results)

        if response.status_code == 200:
            return filtered_results
        else:
            return f"Error: {data['message']}"
    except Exception as e:
        return str(e)
    
# Database Functions

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def create_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT NOT NULL,
                 password TEXT NOT NULL
                 )""")

    c.execute("""CREATE TABLE IF NOT EXISTS search_history (
                 search_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 place_name TEXT NOT NULL,
                 address TEXT NOT NULL,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users (user_id)
                 )""")


def save_search_history(c, conn, user_id, results):
    for result in results:
        place_name = result["name"]
        address = result["location"]["formatted_address"]
        c.execute("INSERT INTO search_history (user_id, place_name, address) "
                  "VALUES (?, ?, ?)", (user_id, place_name, address))
    conn.commit()


def get_search_history(c, user_id):
    c.execute("SELECT place_name, address, timestamp FROM search_history "
              "WHERE user_id=?", (user_id,))
    return c.fetchall()


def get_most_popular_searches(c, user_id):
    c.execute("SELECT place_name, address, COUNT(*) as search_count "
              "FROM search_history "
              "WHERE user_id=? "
              "GROUP BY place_name, address "
              "ORDER BY search_count DESC "
              "LIMIT 10",
              (user_id,))
    return c.fetchall()


def search_history(c, user_id, keyword):
    c.execute("SELECT place_name, address, timestamp "
              "FROM search_history "
              "WHERE user_id=? AND (place_name LIKE ? OR address LIKE ?)",
              (user_id, f"%{keyword}%", f"%{keyword}%"))
    search_results = c.fetchall()
    return search_results