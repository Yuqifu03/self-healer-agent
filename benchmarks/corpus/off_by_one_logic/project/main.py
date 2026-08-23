def main():
    items = [1, 2, 3, 4]
    count = 0
    for item in items:
        if item < 4:
            count += 1
    print(f"count: {count}")


if __name__ == "__main__":
    main()
