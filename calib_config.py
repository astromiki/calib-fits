'''
This is configuration parser
for calib-fits pipeline.
'''


import configparser
import os

class CalibConfig:
    def __init__(self, config_path):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file '{config_path}' not found.")

        self._parser = configparser.ConfigParser()
        self._parser.optionxform = str  # preserve case sensitivity of keys
        self._parser.read(config_path)

        self.config = self._parse_config()

    def _parse_config(self):
        cfg = {}

        for section in self._parser.sections():
            cfg[section] = {}
            for key, val in self._parser.items(section):
                # Try to infer data type
                if val.lower() in ["true", "false"]:
                    parsed_val = val.lower() == "true"
                elif "," in val:
                    parsed_val = [v.strip() for v in val.split(",")]
                else:
                    try:
                        parsed_val = int(val)
                    except ValueError:
                        try:
                            parsed_val = float(val)
                        except ValueError:
                            parsed_val = val
                cfg[section][key] = parsed_val
        return cfg

    def get(self, section, key, default=None):
        return self.config.get(section, {}).get(key, default)

    def get_section(self, section):
        return self.config.get(section, {})

# For standalone usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python calib_config.py <path/to/config.ini>")
        sys.exit(1)

    config_path = sys.argv[1]
    cfg = CalibConfig(config_path)

    print("Loaded configuration:")
    for section, params in cfg.config.items():
        print(f"[{section}]")
        for key, value in params.items():
            print(f"{key} = {value}")
        print()

