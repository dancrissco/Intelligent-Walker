import tkinter as tk
from tkinter import messagebox
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import osmnx as ox
import networkx as nx
import folium
import webbrowser
import pyttsx3
import math
import time

# Predefined address list
address_list = [
    "Empire State Building, New York, NY",
    "Grand Central Terminal, New York, NY",
    "Times Square, New York, NY",
    "Central Park, New York, NY",
    "Wall Street, New York, NY"
]

# Setup text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# Function to calculate bearing between two lat/lon points
def calculate_bearing(p1, p2):
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

# Convert bearing to direction name
def direction_from_bearing(bearing):
    dirs = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
    idx = round(bearing / 45) % 8
    return dirs[idx]

# Route generation and voice navigation
def generate_route():
    from_address = start_var.get()
    to_address = end_var.get()

    if from_address == to_address:
        messagebox.showerror("Input Error", "Please choose two different locations.")
        return

    try:
        # Geocode
        geolocator = Nominatim(user_agent="walker_navigator_gui", timeout=10)
        from_location = geolocator.geocode(from_address)
        to_location = geolocator.geocode(to_address)

        if not from_location or not to_location:
            messagebox.showerror("Geocoding Error", "Could not find one of the addresses.")
            return

        start_coords = (from_location.latitude, from_location.longitude)
        end_coords = (to_location.latitude, to_location.longitude)

        # Build walkable graph and route
        G = ox.graph_from_point(start_coords, dist=1500, network_type='walk')
        orig_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
        dest_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
        route = nx.shortest_path(G, orig_node, dest_node, weight='length')
        route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]

        # Create map
        m = folium.Map(location=start_coords, zoom_start=15)
        folium.Marker(start_coords, tooltip='Start', popup=from_address).add_to(m)
        folium.Marker(end_coords, tooltip='End', popup=to_address).add_to(m)
        folium.PolyLine(route_coords, color='blue', weight=5).add_to(m)

        # Save and open map
        map_filename = "walker_turn_by_turn_route.html"
        m.save(map_filename)
        webbrowser.open(map_filename)

        # Simulated turn-by-turn directions
        engine.say(f"Starting route from {from_address} to {to_address}.")
        for i in range(len(route_coords)-1):
            p1, p2 = route_coords[i], route_coords[i+1]
            distance = geodesic(p1, p2).meters
            if distance > 5:
                bearing = calculate_bearing(p1, p2)
                direction = direction_from_bearing(bearing)
                engine.say(f"Walk {int(distance)} meters towards {direction}.")
                engine.runAndWait()
                time.sleep(0.5)

        engine.say("You have reached your destination.")
        engine.runAndWait()

    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI
root = tk.Tk()
root.title("Walker Navigator with Turn-by-Turn Voice")

tk.Label(root, text="From:").grid(row=0, column=0, sticky="e")
tk.Label(root, text="To:").grid(row=1, column=0, sticky="e")

start_var = tk.StringVar(root)
end_var = tk.StringVar(root)
start_var.set(address_list[0])
end_var.set(address_list[1])

start_menu = tk.OptionMenu(root, start_var, *address_list)
end_menu = tk.OptionMenu(root, end_var, *address_list)
start_menu.grid(row=0, column=1, padx=10, pady=5)
end_menu.grid(row=1, column=1, padx=10, pady=5)

tk.Button(root, text="Generate Route", command=generate_route).grid(row=2, column=0, columnspan=2, pady=10)

root.mainloop()
