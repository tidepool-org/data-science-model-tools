import numpy as np
from pytest import approx
from scipy.stats import norm, johnsonsu
from tidepool_data_science_models.models.icgm_sensor_generator import iCGMSensorGenerator
from tidepool_data_science_models.models.icgm_sensor_generator_functions import create_dataset


def test_that_fit_icgm_sensor_has_correct_stats():
    """
    Fit an icgm sensor and then check that resulting sensors have expected characteristics
    """
    df, _ = create_dataset(
        kind="sine",
        N=288 * 10,
        min_value=40,
        max_value=400,
        time_interval=5,
        flat_value=np.nan,
        oscillations=1,
        random_seed=0,
    )

    batch_size = 3
    sensor_generator = iCGMSensorGenerator(
        sc_thresholds=None,  # This is required only for iCGM sensors for now (A-G)
        batch_training_size=batch_size,
        use_g6_accuracy_in_loss=False,
        bias_type="percentage_of_value",
        bias_drift_type="random",
        random_seed=0,
        verbose=False,
    )

    sensor_generator.fit(df["value"].values)

    # check that the sensor values used in the fit are written to the sensor output
    sensor_properties = sensor_generator.individual_sensor_properties
    for s in range(batch_size):
        sensor = sensor_generator.sensors[s]
        sensor_generator.individual_sensor_properties

        # check that the sensor characteristics are being passed properly
        assert (
            sensor.initial_bias == sensor_properties.loc[s, "initial_bias"].values[0]
            and sensor.noise_per_sensor == sensor_properties.loc[s, "noise_per_sensor"].values[0]
            and sensor.phi_drift == sensor_properties.loc[s, "phi_drift"].values[0]
            and sensor.bias_drift_range_start == sensor_properties.loc[s, "bias_drift_range_start"].values[0]
            and sensor.bias_drift_range_end == sensor_properties.loc[s, "bias_drift_range_end"].values[0]
            and sensor.bias_drift_oscillations == sensor_properties.loc[s, "bias_drift_oscillations"].values[0]
            and sensor.bias_norm_factor == sensor_properties.loc[s, "bias_norm_factor"].values[0]
            and sensor.noise_coefficient == sensor_properties.loc[s, "noise_coefficient"].values[0]
            and sensor.delay_minutes == sensor_properties.loc[s, "delay"].values[0]
            and sensor.random_seed == sensor_properties.loc[s, "random_seed"].values[0]
            and sensor.bias_drift_type == sensor_properties.loc[s, "bias_drift_type"].values[0]
        )

        # check that the resulting noise added fits within the toleragnce of the noise per sensor
        assert sensor.noise_per_sensor == approx(np.std(sensor.noise), rel=1e-1)

        # check that the initial bias fits within the fit distribution
        initial_bias_min = johnsonsu.ppf(
            0.001,
            a=sensor_generator.dist_params[0],
            b=sensor_generator.dist_params[1],
            loc=sensor_generator.dist_params[2],
            scale=sensor_generator.dist_params[3],
        )

        initial_bias_max = johnsonsu.ppf(
            0.999,
            a=sensor_generator.dist_params[0],
            b=sensor_generator.dist_params[1],
            loc=sensor_generator.dist_params[2],
            scale=sensor_generator.dist_params[3],
        )

        assert (sensor.initial_bias >= initial_bias_min) and (sensor.initial_bias <= initial_bias_max)