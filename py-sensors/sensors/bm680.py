import bme680
import time
import json
import mqtt
from sensors.sensor_interface import SensorInterface
# import asyncio


class GasTempHum(SensorInterface):
    start_time = time.time()
    curr_time = start_time
    burn_in_time = 60
    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0
    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25
    sensor = None
    gas_baseline = None
    burn_in_data = []

    def __init__(self):
        try:
            self.sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        except IOError:
            self.sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)
        self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self.sensor.set_gas_heater_temperature(320)
        self.sensor.set_gas_heater_duration(150)
        self.sensor.select_gas_heater_profile(0)
        self.collectInitialData()

    def run(self):
        curr_time = time.time()
        print("cenas")
        try:
            while True:
                if self.sensor.get_sensor_data() and self.sensor.data.heat_stable:
                    data = self.calculateAirScore()
                    time.sleep(1)
                    if time.time() - curr_time >= 300:  # 5min
                        print("publishing message:" + data)
                        mqtt.publish("bm680", self.build_json_payload(data))
                        curr_time = time.time()
        except KeyboardInterrupt:
            pass

    def collectInitialData(self):
        while self.curr_time - self.start_time < self.burn_in_time:
            self.curr_time = time.time()
            if self.sensor.get_sensor_data() and self.sensor.data.heat_stable:
                gas = self.sensor.data.gas_resistance
                self.burn_in_data.append(gas)
                # print('Gas: {0} Ohms'.format(round(gas, 2)))
                time.sleep(1)
        self.gas_baseline = sum(self.burn_in_data[-50:]) / 50.0

    def calculateAirScore(self):
        gas = self.sensor.data.gas_resistance
        temp = self.sensor.data.temperature
        gas_offset = self.gas_baseline - gas

        hum = self.sensor.data.humidity
        hum_offset = hum - self.hum_baseline

        # Calculate hum_score as the distance from the hum_baseline.
        if hum_offset > 0:
            hum_score = (100 - self.hum_baseline - hum_offset)
            hum_score /= (100 - self.hum_baseline)
            hum_score *= (self.hum_weighting * 100)
        else:
            hum_score = (self.hum_baseline + hum_offset)
            hum_score /= self.hum_baseline
            hum_score *= (self.hum_weighting * 100)

        # Calculate gas_score as the distance from the gas_baseline.
        if gas_offset > 0:
            gas_score = (gas / self.gas_baseline)
            gas_score *= (100 - (self.hum_weighting * 100))
        else:
            gas_score = 100 - (self.hum_weighting * 100)

        # Calculate air_quality_score.
        air_quality_score = hum_score + gas_score
        return {
            "gas": round(gas, 2),
            "hum": round(hum, 2),
            "air_score": round(air_quality_score, 3),
            "temp": temp
        }

    def print(self, values):
        print('Air Quality: {0} %, Gas: {1} Ohms, Hum: {2}'.format(
            round(values[2], 3),
            round(values[0], 2),
            round(values[1], 2)))

    def build_json_payload(self, sensor_data):
        data = {}
        data['temperature'] = sensor_data['temp']
        data['humidity'] = sensor_data['hum']
        data['air_quality'] = sensor_data['air_score']
        data['gas'] = sensor_data['gas']
        json_data = json.dumps(data)
        return json_data
