--create indexes

CREATE INDEX IF NOT EXISTS stops_geom_gix ON stops USING GIST (geom);
CREATE INDEX IF NOT EXISTS shape_geoms_geom_gix ON shape_geoms USING GIST (geom);
CREATE INDEX IF NOT EXISTS trips_route_id_idx ON trips(route_id);
CREATE INDEX IF NOT EXISTS trips_shape_id_idx ON trips(shape_id);
CREATE INDEX IF NOT EXISTS stop_times_trip_id_idx ON stop_times(trip_id);
CREATE INDEX IF NOT EXISTS stop_times_stop_id_idx ON stop_times(stop_id);
CREATE INDEX IF NOT EXISTS routes_short_name_idx ON routes(route_short_name);
CREATE INDEX IF NOT EXISTS shape_geoms_shape_id_idx ON shape_geoms(shape_id);
CREATE INDEX IF NOT EXISTS trips_service_id_idx ON trips(service_id);
CREATE INDEX transit_edges_source_idx ON transit_edges(source);
CREATE INDEX transit_edges_target_idx ON transit_edges(target);
CREATE INDEX transit_edges_geom_gix ON transit_edges USING GIST (geom);
CREATE INDEX transit_edges_from_stop_idx ON transit_edges(from_stop_id);
CREATE INDEX transit_edges_to_stop_idx ON transit_edges(to_stop_id);
----