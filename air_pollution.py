import tkinter as tk
from tkinter import ttk, messagebox
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time
from collections import deque

# ----------------------------
# Configuration
# ----------------------------


MAX_DATA_POINTS = 50

time_data = deque(maxlen=MAX_DATA_POINTS)
pm25_data = deque(maxlen=MAX_DATA_POINTS)   
pm10_data = deque(maxlen=MAX_DATA_POINTS)
co_data = deque(maxlen=MAX_DATA_POINTS)
no2_data = deque(maxlen=MAX_DATA_POINTS)
o3_data = deque(maxlen=MAX_DATA_POINTS)

# ----------------------------
# Fetch Real Data from OpenWeather API
# ----------------------------
def fetch_real_air_quality():
    try:
        TOKEN = "00e300a3b1608cc92397280d36b19cfa88922512"
        CITY = "chandigarh"
        url = f"https://api.waqi.info/feed/{CITY}/?token={TOKEN}"
        response = requests.get(url)
        data = response.json()

        if data["status"] != "ok":
            print("API error:", data)
            return None

        iaqi = data["data"]["iaqi"]
        return {
            "PM2.5": iaqi.get("pm25", {}).get("v", 0),
            "PM10": iaqi.get("pm10", {}).get("v", 0),
            "CO": iaqi.get("co", {}).get("v", 0),
            "SO2": iaqi.get("so2", {}).get("v", 0),
            "NO2": iaqi.get("no2", {}).get("v", 0),
            "O3": iaqi.get("o3", {}).get("v", 0),
            "AQI": data["data"]["aqi"],
            "Timestamp": time.strftime("%H:%M:%S")
        }
    except Exception as e:
        print("Error fetching data:", e)
        return None

# ----------------------------
# Tkinter GUI Setup
# ----------------------------
root = tk.Tk()
root.title("🌍 Real-Time Air Quality Monitoring System (Live Data)")
root.geometry("1100x650")
root.configure(bg="#f0f8ff")

title_label = tk.Label(root, text="🌍 Real-Time Air Quality Monitoring Dashboard (Live from ACQIN)",
                       font=("Arial", 18, "bold"), bg="#f0f8ff", fg="#2c3e50")
title_label.pack(pady=10)

# ----------------------------
# Data Table
# ----------------------------
frame_table = tk.Frame(root, bg="#f0f8ff")
frame_table.pack(pady=10)

columns = ("Pollutant", "Value")
tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=6)
tree.heading("Pollutant", text="Pollutant")
tree.heading("Value", text="Value (µg/m³)")
tree.column("Pollutant", width=100, anchor=tk.CENTER)
tree.column("Value", width=100, anchor=tk.CENTER)
tree.pack()

# ----------------------------
# Graph Setup
# ----------------------------
fig, ax = plt.subplots(figsize=(8, 4))
plt.style.use("seaborn-v0_8")

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(pady=10)

def update_graph():
    ax.clear()
    ax.plot(time_data, pm25_data, label="PM2.5", marker='o')
    ax.plot(time_data, pm10_data, label="PM10", marker='o')
    ax.plot(time_data, co_data, label="CO", marker='o')
    ax.plot(time_data, no2_data, label="NO2", marker='o')
    ax.plot(time_data, o3_data, label="O3", marker='o')
    ax.set_title("Air Quality Over Time (Live)")
    ax.set_xlabel("Time (HH:MM:SS)")
    ax.set_ylabel("Concentration (µg/m³)")
    ax.legend(loc="upper right")
    ax.grid(True)
    plt.tight_layout()
    canvas.draw()

# ----------------------------
# Statistics Calculation
# ----------------------------
def calculate_statistics():
    if len(pm25_data) == 0:
        return None
    df = pd.DataFrame({
        "PM2.5": list(pm25_data),
        "PM10": list(pm10_data),
        "CO": list(co_data),
        "NO2": list(no2_data),
        "O3": list(o3_data)
    })
    stats = df.describe().loc[['mean', 'max', 'min']].to_dict()
    return stats

# ----------------------------
# Live Update Loop
# ----------------------------
def update_data():
    data = fetch_real_air_quality()
    if data:
        time_data.append(data["Timestamp"])
        pm25_data.append(data["PM2.5"])
        pm10_data.append(data["PM10"])
        co_data.append(data["CO"])
        no2_data.append(data["NO2"])
        o3_data.append(data["O3"])

        for row in tree.get_children():
            tree.delete(row)
        for pollutant, value in data.items():
            if pollutant != "Timestamp":
                tree.insert("", tk.END, values=(pollutant, round(value, 2)))

        update_graph()

        stats = calculate_statistics()
        if stats:
            avg_label.config(text=f"Avg PM2.5: {stats['PM2.5']['mean']:.2f} | "
                                  f"PM10: {stats['PM10']['mean']:.2f} | "
                                  f"CO: {stats['CO']['mean']:.2f} | "
                                  f"NO2: {stats['NO2']['mean']:.2f} | "
                                  f"O3: {stats['O3']['mean']:.2f}")

    root.after(60000, update_data)  # Fetch every 1 mins

# ----------------------------
# Average Label
# ----------------------------
avg_label = tk.Label(root, text="Fetching live air quality data...",
                     font=("Arial", 12), bg="#f0f8ff", fg="#2c3e50")
avg_label.pack(pady=10)

# ----------------------------
# Export Data to CSV
# ----------------------------
def export_data():
    if len(time_data) == 0:
        messagebox.showwarning("No Data", "No air quality data to export yet!")
        return

    df = pd.DataFrame({
        "Time": list(time_data),
        "PM2.5": list(pm25_data),
        "PM10": list(pm10_data),
        "CO": list(co_data),
        "NO2": list(no2_data),
        "O3": list(o3_data)
    })

    # Save only current session's data when button clicked
    filename = f"air_quality_data_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)

    messagebox.showinfo("✅ Export Successful", f"Data saved as '{filename}'")

export_btn = tk.Button(root, text="💾 Export Data to CSV", command=export_data,
                       bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
export_btn.pack(pady=10)
def on_close():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
# ----------------------------
# Start Monitoring
# ----------------------------
update_data()
root.mainloop()
