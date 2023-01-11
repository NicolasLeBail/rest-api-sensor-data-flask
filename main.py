import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request
from http import HTTPStatus
from datetime import datetime, timezone, timedelta

load_dotenv()

app = Flask(__name__)
db_name = os.getenv('LOCAL_DB_NAME')
role_username = os.getenv('LOCAL_DB_USERNAME')
role_pwd = os.getenv('LOCAL_DB_PWD')
connection = psycopg2.connect(dbname=db_name, user=role_username, password=role_pwd)

# CONSTANTS
PROP_HTTP_MSG = 'message'
# DB QUERIES
CREATE_MEAS_TABLE = """CREATE TABLE IF NOT EXISTS measurements.sensor_measurements
                    (sensor_id TEXT NOT NULL, timestamp TIMESTAMPTZ NOT NULL, type TEXT NOT NULL, value REAL NOT NULL);"""
INSERT_MEAS = """INSERT into measurements.sensor_measurements 
              (sensor_id, timestamp, type, value) VALUES (%s, %s, %s, %s);"""
MEAS_AGGR_1H = """SELECT DATE_TRUNC('hour', timestamp) as alias_interval, MIN(value), AVG(value), MAX(value)
               FROM measurements.sensor_measurements
               WHERE sensor_id = (%s) AND type = (%s) AND timestamp BETWEEN (%s)::timestamp AND (%s)::timestamp
               GROUP BY alias_interval ORDER BY alias_interval;"""
MEAS_AGGR_5MIN = """SELECT TIMESTAMP WITH TIME ZONE 'epoch' +
                 INTERVAL '1second' * round(extract('epoch' from timestamp) / 300) * 300 as timestamp,
                 MIN(value), AVG(value), MAX(value)
                 FROM measurements.sensor_measurements 
                 WHERE sensor_id = (%s) AND type = (%s) AND timestamp BETWEEN (%s)::timestamp AND (%s)::timestamp
                 GROUP BY round(extract('epoch' from timestamp) / 300), value ORDER BY timestamp;"""


@app.post('/sensorMeasurement')
def create_measurement():
    data = request.get_json()
    if data is not None:
        try:
            sensor_id = data['sensorId']
            ts = data['timestamp']
            meas_type = data['type']
            meas_val = data['value']
        except KeyError:
            return {PROP_HTTP_MSG: 'Malformed request body.'}, HTTPStatus.BAD_REQUEST
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_MEAS_TABLE)
                cursor.execute(INSERT_MEAS, (sensor_id, ts, meas_type, meas_val))
                return {PROP_HTTP_MSG: 'Sensor measurement created.'}, HTTPStatus.CREATED
    return {PROP_HTTP_MSG: 'Issue with body format and/or mimetype. Only JSON is accepted.'}, HTTPStatus.BAD_REQUEST


def get_aggr_interval(aggr_param):
    if aggr_param == '5min':
        return MEAS_AGGR_5MIN, '5min'
    else:
        return MEAS_AGGR_1H, '1h'


def get_time_frame(tf_start, tf_stop):
    if tf_stop is None:
        tf_stop = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if tf_start is None:
        tf_start = (datetime.fromisoformat(tf_stop) - timedelta(days=1)).isoformat()
    if datetime.fromisoformat(tf_start) > datetime.fromisoformat(tf_stop):
        return tf_stop, tf_start
    return tf_start, tf_stop


def parse_aggr_from_db(aggr_from_db):
    aggr_data = []
    for aggr_el in aggr_from_db:
        new_el = {'timestamp': aggr_el[0], 'min': round(aggr_el[1], 2), 'mean': round(aggr_el[2], 2),
                  'max': round(aggr_el[3], 2)}
        aggr_data.append(new_el)
    return aggr_data


@app.get('/sensorMeasurement/<string:sensor_id>')
def retrieve_meas_aggregates(sensor_id):
    meas_type = request.args.get('measType')
    if sensor_id is None or meas_type is None:
        return {PROP_HTTP_MSG: 'Malformed request, missing sensor id and/or measurement type.'}, HTTPStatus.BAD_REQUEST
    meas_aggr_query, interval = get_aggr_interval(request.args.get('aggregate'))
    tf_start, tf_stop = get_time_frame(request.args.get('timeFrameStart'), request.args.get('timeFrameStop'))
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(meas_aggr_query, (sensor_id, meas_type, tf_start, tf_stop))
            aggr_data = parse_aggr_from_db(cursor.fetchall())
            return {PROP_HTTP_MSG: f'Measurement aggregates for device {sensor_id}', 'aggregatedData': aggr_data,
                    'interval': interval, 'startDate': tf_start, 'stopDate': tf_stop}, HTTPStatus.OK
