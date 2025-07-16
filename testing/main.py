import os

gpio_sysfs_path = "/sys/class/gpio"

if os.path.exists(gpio_sysfs_path):
    for chip_dir in os.listdir(gpio_sysfs_path):
        if chip_dir.startswith("gpiochip"):
            chip_path = os.path.join(gpio_sysfs_path, chip_dir)
            try:
                with open(os.path.join(chip_path, "label"), "r") as f:
                    label = f.read().strip()
                with open(os.path.join(chip_path, "base"), "r") as f:
                    base = int(f.read().strip())
                with open(os.path.join(chip_path, "ngpio"), "r") as f:
                    num_gpios = int(f.read().strip())

                print(f"Chip: {label} (Base: {base}, Number of GPIOs: {num_gpios})")

            except FileNotFoundError:
                print(f"Could not get info for {chip_dir}")
            except Exception as e:
                print(f"Error processing {chip_dir}: {e}")
else:
    print("`/sys/class/gpio` not found. This method might not be supported or is deprecated.")



