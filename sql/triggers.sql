-- =========================================
-- 1. AUTO-UPDATE STOPS GEOMETRY
-- =========================================

CREATE OR REPLACE FUNCTION update_stop_geom()
RETURNS trigger AS $$
BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.stop_lon, NEW.stop_lat), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_stop_geom ON stops;

CREATE TRIGGER trg_update_stop_geom
BEFORE INSERT OR UPDATE OF stop_lat, stop_lon
ON stops
FOR EACH ROW
EXECUTE FUNCTION update_stop_geom();

-- =========================================
-- 2. AUTO-REFRESH SHAPE_GEOMS
-- =========================================

CREATE OR REPLACE FUNCTION refresh_shape_geom()
RETURNS trigger AS $$
DECLARE
    affected_shape_id text;
BEGIN
    affected_shape_id := COALESCE(NEW.shape_id, OLD.shape_id);

    DELETE FROM shape_geoms
    WHERE shape_id = affected_shape_id;

    INSERT INTO shape_geoms (shape_id, geom)
    SELECT
        s.shape_id,
        ST_MakeLine(
            ST_SetSRID(ST_MakePoint(s.shape_pt_lon, s.shape_pt_lat), 4326)
            ORDER BY s.shape_pt_sequence
        ) AS geom
    FROM shapes s
    WHERE s.shape_id = affected_shape_id
    GROUP BY s.shape_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_refresh_shape_geom ON shapes;

CREATE TRIGGER trg_refresh_shape_geom
AFTER INSERT OR UPDATE OR DELETE
ON shapes
FOR EACH ROW
EXECUTE FUNCTION refresh_shape_geom();

-- =========================================
-- 3. AUTO-REFRESH VEHICLE TRAJECTORIES
-- =========================================

CREATE OR REPLACE FUNCTION refresh_vehicle_trajectory()
RETURNS trigger AS $$
BEGIN
    DELETE FROM vehicle_trajectories
    WHERE vehicle_id = NEW.vehicle_id
      AND route_id = NEW.route_id;

    INSERT INTO vehicle_trajectories (vehicle_id, route_id, traj)
    SELECT
        rv.vehicle_id,
        rv.route_id,
        tgeompointseq(
            array_agg(
                tgeompointinst(
                    ST_SetSRID(ST_MakePoint(rv.longitude, rv.latitude), 4326),
                    rv."timestamp"
                )
                ORDER BY rv."timestamp"
            )
        )
    FROM realtime_vehicles rv
    WHERE rv.vehicle_id = NEW.vehicle_id
      AND rv.route_id = NEW.route_id
    GROUP BY rv.vehicle_id, rv.route_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_refresh_vehicle_trajectory ON realtime_vehicles;

CREATE TRIGGER trg_refresh_vehicle_trajectory
AFTER INSERT OR UPDATE
ON realtime_vehicles
FOR EACH ROW
EXECUTE FUNCTION refresh_vehicle_trajectory();