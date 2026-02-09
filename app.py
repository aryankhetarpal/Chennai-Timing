from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

# =========================================================
# MACHINE DATA (EXACTLY AS YOU STRUCTURED IT)
# =========================================================

machine_data = [
    {
        'Machine Name': 'BHE-1300-G',
        'Capacity': (1500, 610),
        'Feed 2714/2711/2367/HIPERDIE (mm/min)': 1.2,
        'Feed 2316/Nitro-B/annealed (mm/min)': 1.33,
        'Feed 2311/2312/2083/EXSTAHL (mm/min)': 1.47,
        'Feed 2738/2083HT/2797/2085/2790/2738HH (mm/min)': 1.67,
        'Feed TSHH/HG/7225/HHH (mm/min)': 2
    },
    {
        'Machine Name': 'ITM-1500',
        'Capacity': (1500, 600),
        'Feed 2714/2711/2367/HIPERDIE (mm/min)': 1.02,
        'Feed 2316/Nitro-B/annealed (mm/min)': 1.36,
        'Feed 2311/2312/2083/EXSTAHL (mm/min)': 1.36,
        'Feed 2738/2083HT/2797/2085/2790/2738HH (mm/min)': 1.36,
        'Feed TSHH/HG/7225/HHH (mm/min)': 1.69
    },
    {
        'Machine Name': 'V5',
        'Capacity': (1500, 610),
        'Feed 2714/2711/2367/HIPERDIE (mm/min)': 2.95,
        'Feed 2316/Nitro-B/annealed (mm/min)': 3.28,
        'Feed 2311/2312/2083/EXSTAHL (mm/min)': 3.61,
        'Feed 2738/2083HT/2797/2085/2790/2738HH (mm/min)': 4.1,
        'Feed TSHH/HG/7225/HHH (mm/min)': 4.92
    },
    {
        'Machine Name': 'V4',
        'Capacity': (1500, 610),
        'Feed 2714/2711/2367/HIPERDIE (mm/min)': 2.46,
        'Feed 2316/Nitro-B/annealed (mm/min)': 3.28,
        'Feed 2311/2312/2083/EXSTAHL (mm/min)': 3.28,
        'Feed 2738/2083HT/2797/2085/2790/2738HH (mm/min)': 3.28,
        'Feed TSHH/HG/7225/HHH (mm/min)': 3.61
    },
    {
        'Machine Name': '2000',
        'Capacity': None,
        'Feed All Sections (mm/min)': 1
    }
]

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def calculate_sq_inches(w, h, l, cut_type, num_cuts):
    if cut_type == "length":
        area_mm = w * h
    elif cut_type == "width":
        area_mm = h * l
    elif cut_type == "height":
        area_mm = w * l
    elif cut_type == "dia":
        area_mm = math.pi * (w / 2) ** 2
    else:
        area_mm = 0

    area_in2 = area_mm / 645.16
    return round(area_in2 * num_cuts, 2)


def calculate_time(feed, w, h, l, cut_type, num_cuts):
    if cut_type == "length":
        travel = min(w, h)
    elif cut_type == "width":
        travel = min(h, l)
    elif cut_type == "height":
        travel = min(w, l)
    elif cut_type == "dia":
        travel = w
    else:
        travel = 0

    return round((travel / feed) * num_cuts, 2)


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.json

        height_input = str(data["height"]).strip()
        width = float(data["width"])
        length = float(data["length"])
        steel_grade = data["steel_grade"].strip()
        cut_type = data["cut_type"]
        num_cuts = int(data.get("num_cuts", 1))

        # Handle DIA
        if cut_type == "dia":
            w = width
            h = width
        else:
            w = width
            h = float(height_input)

        l = length

        sq_inches = calculate_sq_inches(w, h, l, cut_type, num_cuts)

        results = []

        for machine in machine_data:

            machine_name = machine["Machine Name"]

            # ==========================
            # FEED SELECTION (DYNAMIC)
            # ==========================

            if machine_name == "2000":
                feed = machine["Feed All Sections (mm/min)"]
            else:
                feed_key = f"Feed {steel_grade} (mm/min)"
                feed = machine.get(feed_key)

                if feed is None:
                    # If grade not found for that machine, skip safely
                    continue

            # ==========================
            # CAPACITY CHECK
            # ==========================

            can_cut = True

            if machine["Capacity"]:
                cap1, cap2 = machine["Capacity"]

                if cut_type == "length":
                    required = sorted([w, h])
                elif cut_type == "width":
                    required = sorted([h, l])
                elif cut_type == "height":
                    required = sorted([w, l])
                else:
                    required = sorted([w, h])

                if not (cap1 >= required[1] and cap2 >= required[0]):
                    can_cut = False

            # ==========================
            # TIME CALCULATION
            # ==========================

            time = calculate_time(feed, w, h, l, cut_type, num_cuts)

            results.append({
                "machine_name": machine_name,
                "cutting_time": time,
                "sq_inches": sq_inches,
                "can_cut": can_cut
            })

        return jsonify(results)

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"error": "Invalid input. Please check dimensions."}), 500


if __name__ == "__main__":
    app.run(debug=True)
