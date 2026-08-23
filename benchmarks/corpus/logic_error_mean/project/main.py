def mean(values):
    total = 0
    for value in values:
        total += value
    return total


def main():
    print(f"mean: {mean([10, 20, 30, 40])}")


if __name__ == "__main__":
    main()
