from yaml import Loader
import yaml


def get_booking_config(config_path):
    with open(config_path) as f:
        config = yaml.load(f, Loader=Loader)

    return config["bookings"]
