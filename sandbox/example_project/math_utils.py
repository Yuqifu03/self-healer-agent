def calculate_average(data):
    total = 0
    for item in data:
        total += int(item)
    return total / len(data)