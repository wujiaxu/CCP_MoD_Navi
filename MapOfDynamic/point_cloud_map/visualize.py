import pandas as pd

def vis_sensor(config_file):
    df = pd.read_excel(config_file,header=1)
    print(df.head(5))
    return

if __name__ == "__main__":

    vis_sensor("raw_data/atc-sensors.xlsx")