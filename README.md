# rest-api-sensor-data-flask
This project is a Flask REST API application to store and retrieve sensor data to/from a PostgreSQL database.
The API exposes 2 endpoints; one to store sensor data and one to retrieve aggregated data for a given sensor.
Measurement data is stored and retrieved from a PostgreSQL database using the Python adapter `psycopg2`.

### Installation Guide
This project uses Python version 3.9 and a locally installed PostgreSQL database.
To set up your database, run the following commands:
* `createdb -U postgres sensor_data`
* `psql -U postgres *your_database_name*`
* `CREATE SCHEMA measurements;`
* `DROP SCHEMA public;`
* `CREATE ROLE rest_api_role WITH LOGIN PASSWORD '*role_password*';`
* `GRANT CREATE, USAGE ON SCHEMA measurements TO rest_api_role;`
* `GRANT INSERT, SELECT ON ALL TABLES IN SCHEMA measurements TO rest_api_role;`

To set up the application:
* Clone this repository [here](https://github.com/NicolasLeBail/rest-api-sensor-data-flask.git).
* Run `pip install -r requirements.txt`
* To work with your locally installed PostgreSQL database configure an `.env` file. See `.env.sample` for assistance.

### Usage
* Run `flask run` to start the application

### API  Endpoints
| HTTP Verbs | Endpoints                    | Action                                           |
| --- |------------------------------|--------------------------------------------------|
| POST | /sensorMeasurement           | To create a new sensor measurement               |
| GET | /sensorMeasurement/:sensorId | To retrieve aggregated measurements for a sensor |

### Examples
#### Storing measurement values
To create a new measurement sensor, all the parameters from the following JSON request body are needed.
```
{
    "sensorId": "sensorA_id",
    "timestamp": "2022-05-01T11:23:24+02:00",
    "type": "temperature",
    "value": 25
}
```
Using CURL:
```
curl -X POST http://local_db_address:your_db_port/sensorMeasurement -H 'Content-Type: application/json' -d '{"sensorId":"sensorA","timestamp":"2022-12-02T11:23:24+02:00","type":"temperature","value":15.5}'
```

#### Retrieving measurement values
To retrieve measurement aggregates, the http request requires at least the parameter `measType`.
In addition, the user can use the following parameters:
* `aggregate` (`5min` or `1h`, only intervals available), 
* `timeFrameStart` (e.g. `2022-10-10T19%3A20%3A13%2B02%3A00`),
* `timeFrameStop` (e.g. `2022-12-11T19%3A20%3A13%2B02%3A00`)
Using CURL using only `measType`:
```
curl 'http://local_db_address:your_db_port/sensorMeasurement/sensorA?measType=rel_humidity'
```
Using CURL with all possible parameters:
```
curl 'http://local_db_address:your_db_port/sensorMeasurement/sensorA?measType=temperature&aggregate=5min&timeFrameStart=2022-12-01T19%3A20%3A13%2B02%3A00&timeFrameStop=2022-12-11T19%3A20%3A13%2B02%3A00'
```
Sample from the results of the previous http request:
```
{
    "aggregatedData": [
        {
            "max": 17.42,
            "mean": 17.42,
            "min": 17.42,
            "timestamp": "Thu, 01 Dec 2022 17:30:00 GMT"
        },
        {
            "max": 39.38,
            "mean": 39.38,
            "min": 39.38,
            "timestamp": "Thu, 01 Dec 2022 17:55:00 GMT"
        },
        ...
        {
            "max": 26.93,
            "mean": 26.93,
            "min": 26.93,
            "timestamp": "Sun, 11 Dec 2022 13:15:00 GMT"
        }
    ],
    "interval": "5min",
    "message": "Measurement aggregates for device sensorA",
    "startDate": "2022-12-01T19:20:13+02:00",
    "stopDate": "2022-12-11T19:20:13+02:00"
}
```
Measurement data in the examples above has been generated using Postman Runner.

### Assumptions
To develop this application, the following assumptions were made:
* Sensors send only one measurement at a time.
* A sensor measurement always contains an ID, a timestamp, a measurement type and a numerical measurement value.
* When retrieving aggregated data, if the following parameters are missing, their default values are:
  * `aggregate` => `1h`
  * `timeFrameStart` => `timeFrameStop` - 1 day
  * `timeFrameStop` => the current date and time
* When retrieving aggregated data, `timeFrameStart` can be later than `timeFrameStop`. If so, the timestamps will be programmatically switched.

