from config.config_loader import load_intake_config


def main():
    config = load_intake_config()

    source_format = config["conversion"]["source_format"]

    print(f"En-Route starting...")
    print(f"Configured source format: {source_format}")


if __name__ == "__main__":
    main()