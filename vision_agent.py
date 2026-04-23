from ultralytics import YOLO

# 🔹 Load model (MAKE SURE PATH IS CORRECT)
model = YOLO("runs/detect/train/weights/best.pt")


def map_class_to_output(class_name):
    name = class_name.lower()

    # DAMAGE TYPE
    if "scratch" in name:
        damage = "Scratch"
    elif "dent" in name:
        damage = "Dent"
    elif "crack" in name or "broken" in name:
        damage = "Crack"
    elif "damage" in name:
        damage = "General Damage"
    else:
        damage = "Unknown"

    # PART TYPE
    if "bumper" in name:
        part = "Bumper"
    elif "door" in name:
        part = "Door"
    elif "hood" in name or "bonnet" in name:
        part = "Hood"
    elif "light" in name:
        part = "Light"
    elif "wind" in name or "window" in name:
        part = "Windshield"
    elif "mirror" in name:
        part = "Side Mirror"
    elif "fender" in name:
        part = "Fender"
    elif "roof" in name:
        part = "Roof"
    elif "pillar" in name:
        part = "Pillar"
    else:
        part = "Car Body"

    return part, damage


def analyze_damage(image_path):
    print("Running analysis...")  # DEBUG

    results = model(image_path)

    if len(results[0].boxes) == 0:
        return {
            "part_damaged": "Unknown",
            "damage_type": "No Damage",
            "severity_score": 0.0,
            "estimated_repair_cost": 0
        }

    # Take most confident detection
    box = max(results[0].boxes, key=lambda x: x.conf[0])

    class_id = int(box.cls[0])
    class_name = model.names[class_id]

    part, damage = map_class_to_output(class_name)

    severity = round(float(box.conf[0]), 2)

    cost_map = {
        "Dent": 3000,
        "Scratch": 1500,
        "Crack": 5000,
        "General Damage": 2500,
        "Unknown": 2000
    }

    estimated_cost = int(cost_map.get(damage, 2000) * severity)

    return {
        "part_damaged": part,
        "damage_type": damage,
        "severity_score": severity,
        "estimated_repair_cost": estimated_cost
    }


# 🔹 TEST BLOCK
if __name__ == "__main__":
    result = analyze_damage("dataset/test/images/test.jpg")  # 👈 CHANGE THIS
    print(result)