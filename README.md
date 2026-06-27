# GTFS Public Transport Explorer

A full-stack public transportation data exploration and analysis system built using **GTFS**, **PostgreSQL**, **PostGIS**, **MobilityDB**, **pgRouting**, **FastAPI**, and **Leaflet**.

The project imports public transportation data in GTFS format, transforms it into spatial and mobility data, and provides an interactive web interface for exploring stops, routes, trips, service schedules, spatial relationships, and routing results.

## Project Overview

The **GTFS Public Transport Explorer** is a web-based system for working with public transportation data.

The application performs the following main tasks:

* Imports GTFS files into PostgreSQL.
* Stores stop coordinates using PostGIS geometries.
* Processes trips, routes, stops, shapes, and service dates.
* Transforms ordinary transportation data into mobility data.
* Executes spatial SQL queries.
* Calculates routes using pgRouting.
* Provides transportation statistics and network summaries.
* Displays query results on an interactive Leaflet map.
* Connects the frontend to the database through a FastAPI REST API.

The project uses public transportation GTFS data published by the Istanbul Metropolitan Municipality.


## Main Features

The application provides several groups of functions:

### GTFS Exploration

* Display public transport stops.
* Display available routes.
* Retrieve trips belonging to a route.
* Show the stops belonging to a selected route.
* View route and trip information in tables.
* Find stops near a selected point.
* Find the nearest stop to a location.
* Calculate distances between stops.
* Search for stops inside a specified area.
* Display spatial query results on the map.
* Calculate paths between selected stops.
* Perform shortest-path calculations using pgRouting.
* Compare different routing algorithms.
* Display the calculated path as a line on the map.
* Count stop visits and unique routes.
* Analyze service activity on a selected date.
* Transform trips into temporal or mobility representations.
* Explore the movement of public transportation vehicles.

---

## Technologies Used

### Backend

* Python
* FastAPI
* Uvicorn
* Psycopg2
* Pandas
* Pydantic
* Python-dotenv

### Database

* PostgreSQL
* PostGIS
* MobilityDB
* pgRouting
* SQL

### Frontend

* HTML
* CSS
* JavaScript
* Leaflet
* Fetch API

### Development Tools

* Git
* GitHub
* pgAdmin
* Visual Studio Code
* Swagger UI

---

## GTFS Data

GTFS stands for **General Transit Feed Specification**.

It is a standard format used by transportation organizations to publish public transport schedules and geographic information.

The main GTFS files used in this project include:

| File                 | Description                                 |
| -------------------- | ------------------------------------------- |
| `agency.txt`         | Information about the transportation agency |
| `stops.txt`          | Stop names, IDs, latitudes, and longitudes  |
| `routes.txt`         | Public transportation route information     |
| `trips.txt`          | Trips belonging to routes and services      |
| `stop_times.txt`     | Stop arrival and departure times            |
| `calendar.txt`       | Weekly service schedules                    |
| `shapes.txt`         | Geographic paths followed by vehicles       |

The files are connected through identifiers such as:

* `stop_id`
* `route_id`
* `trip_id`
* `service_id`
* `shape_id`

---

## Data Sources and References

### Istanbul Metropolitan Municipality GTFS Dataset

Istanbul Metropolitan Municipality Open Data Portal:

```text
https://data.ibb.gov.tr/en/dataset/public-transport-gtfs-data
```

### MobilityDB Workshop

Transforming GTFS Data for MobilityDB:

```text
https://docs.mobilitydb.com/MobilityDB-workshop/master/ch04s02.html
```
