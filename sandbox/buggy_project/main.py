from utils.calculator import compute_total


def main():
    print("--- Invoice Total Calculator ---")
    items = [12.5, 8.0, 3.75]
    total = compute_total(items)
    print(f"The total is: {total:.2f}")


if __name__ == "__main__":
    main()
