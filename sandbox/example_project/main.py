from utils.math_utils import calculate_average

def main():
    print("--- Starting Average Calculation ---")
    test_data = [10, 20, 30, 40]
    
    result = calculate_average(test_data)
    print(f"The calculated average is: {result}")

if __name__ == "__main__":
    main()