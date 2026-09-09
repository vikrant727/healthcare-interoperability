from config.config_loader import load_intake_config
from intake.intake_router import route_intake


def main():
    config = load_intake_config()

    print("En-Route starting...")
    print(
        f"Configured source format: "
        f"{config['conversion']['source_format']}"
    )

    route_intake(config)


if __name__ == "__main__":
    main()