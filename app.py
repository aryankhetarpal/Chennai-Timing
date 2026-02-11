from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

MM2_TO_IN2 = 645.16

# ---------------------------------------------------
# MACHINE DATA (Min values exactly from your sheet)
# ---------------------------------------------------

machine_data = [
    {
        "Machine Name": "BHE-1300-G",
        "Capacity": (1500, 610),
        "mins": {
            "2714/2711/2367/HIPERDIE": 508.33,
            "2316/Nitro-B/annealed": 457.5,
            "2311/2312/2083/EXSTAHL": 415.91,
            "2738/2083HT/2797/2085/2790/2738HH": 366,
            "TSHH/HG/7225/HHH": 305
        }
    },
    {
        "Machine Name": "ITM-1500",
        "Capacity": (1500, 600),
        "mins": {
            "2714/2711/2367/HIPERDIE": 600,
            "2316/Nitro-B/annealed": 450,
            "2311/2312/2083/EXSTAHL": 450,
            "2738/2083HT/2797/2085/2790/2738HH": 450,
            "TSHH/HG/7225/HHH": 360
        }
    },
    {
        "Machine Name": "V5",
        "Capacity": (1500, 610),
        "mins": {
            "2714/2711/2367/HIPERDIE": 508.33,
            "2316/Nitro-B/annealed": 457.5,
            "2311/2312/2083/EXSTAHL": 415.91,
            "2738/2083HT/2797/2085/2790/2738HH": 366,
            "TSHH/HG/7225/HHH": 305
        }
    },
    {
        "Machine Name": "V4",
        "Capacity": (1500, 610),
        "mins": {
            "2714/2711/2367/HIPERDIE": 610,
            "2316/Nitro-B/annealed": 457.5,
            "2311/2312/2083/EXSTAHL": 457.5,
            "2738/2083HT/2797/2085/2790/2738HH": 457.5,
            "TSHH/HG/7225/HHH": 415.91
        }
    },
    {
        "Machine Name": "2000",
        "Capacity": None,
        "mins": {
            "ALL": None  # Special case → 1 sq.in/min
        }
    }
]

# ---------------------------------------------------
# CALCULATE MACHINE FEED FROM SHEET
# ---------------------------------------------------

def calculate_machine_feed(machine, grade):
    if machine["Machine Name"] == "2000":
        return 1  # 1 sq.in/min as defined

    capacity_w, capacity_h = machine["Capacity"]
    full_area_mm2 = capacity_w * capacity_h
    full_area_in2 = full_area_mm2 / MM2_TO_IN2

    min_value = machine["mins"][grade]

    feed_sq_in_min = full_area_in2 / min_value
    return feed_sq_in_min


# ---------------------------------------------------
# CUTTING TIME ENGINE (Chennai Logic)
# ---------------------------------------------------

def calculate_cutting_time(block_dimensions, cut_type, grade, machine, num_cuts=1):
    width, height, length = block_dimensions

    if cut_type == "height":
        area_mm2 = width * length
    elif cut_type == "length":
        area_mm2 = width * height
    elif cut_type == "width":
        area_mm2 = height * length
    elif cut_type == "dia":
        area_mm2 = math.pi * (width / 2) ** 2
    else:
        raise ValueError("Invalid cut type")

    area_in2 = area_mm2 / MM2_TO_IN2

    feed_rate = calculate_machine_feed(machine, grade)

    time_min = (area_in2 / feed_rate) * num_cuts

    return round(time_min, 2), round(area_in2 * num_cuts, 2)


# ---------------------------------------------------
# ROUTES
# ---------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json

    height_input = str(data['height']).strip()

    if height_input.lower() == 'dia':
        cut_type = 'dia'
        height = None
    else:
        height = int(height_input)
        cut_type = data['cut_type']

    width = int(data['width'])
    length = int(data['length'])
    steel_grade = data['steel_grade']
    final_dim = int(data['final_dimension'])
    num_cuts = int(data.get('num_cuts', 1))

    # Update dimension based on cut
    if cut_type == 'length':
        length = final_dim
        block_dimensions = (width, height, length)
        selected_dims = (width, height)
    elif cut_type == 'height':
        height = final_dim
        block_dimensions = (width, height, length)
        selected_dims = (width, length)
    elif cut_type == 'width':
        width = final_dim
        block_dimensions = (width, height, length)
        selected_dims = (height, length)
    elif cut_type == 'dia':
        diameter = width
        block_dimensions = (diameter, diameter, length)
        selected_dims = (diameter, diameter)
    else:
        raise ValueError("Invalid cut type")

    results = []

    for machine in machine_data:

        if machine["Capacity"] is None:
            can_cut = True
        else:
            cap_w, cap_h = machine["Capacity"]
            can_cut = (
                (selected_dims[0] <= cap_w and selected_dims[1] <= cap_h) or
                (selected_dims[0] <= cap_h and selected_dims[1] <= cap_w)
            )

        if machine["Machine Name"] == "2000":
            grade_key = "ALL"
        else:
            grade_key = steel_grade

        cutting_time, sq_inches = calculate_cutting_time(
            block_dimensions,
            cut_type,
            grade_key,
            machine,
            num_cuts
        )

        results.append({
            'machine_name': machine['Machine Name'],
            'cutting_time': cutting_time,
            'sq_inches': sq_inches,
            'can_cut': can_cut
        })

    return jsonify(results)


# ---------------------------------------------------
# LOCAL RUN (Render ignores this)
# ---------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
