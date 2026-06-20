"""
Query functions for all paths
DONE!
"""

from database_Creation import execute_query, connect_Database
from fastapi import HTTPException

# -----------------------------
# FULL NETWORK
# -----------------------------

def get_full_network_query():
    query = """
    SELECT DISTINCT ON (r.route_id)
        r.route_id,
        r.route_short_name,
        r.route_long_name,
        ST_AsGeoJSON(
            ST_MakeLine(
                ST_MakePoint(s.shape_pt_lon, s.shape_pt_lat)
                ORDER BY s.shape_pt_sequence
            )
        ) AS geojson
    FROM shapes s
    JOIN trips t ON t.shape_id = s.shape_id
    JOIN routes r ON r.route_id = t.route_id
    GROUP BY r.route_id, r.route_short_name, r.route_long_name, s.shape_id;
    """
    return execute_query(query)
# -----------------------------
# DIJKSTRA
# -----------------------------

def get_dijkstra_stop_list_query(start_vertex_id, end_vertex_id):
    query = """
    WITH path AS (
        SELECT *
        FROM pgr_dijkstra(
            'SELECT id, source, target, cost FROM transit_edges',
            %s,
            %s,
            directed := true
        )
    )
    SELECT
        p.seq,
        p.node,
        sv.stop_id,
        s.stop_name,
        s.stop_lat,
        s.stop_lon,
        p.edge,
        p.cost,
        p.agg_cost
    FROM path p
    LEFT JOIN stop_vertices sv
        ON p.node = sv.vertex_id
    LEFT JOIN stops s
        ON sv.stop_id = s.stop_id
    ORDER BY p.seq;
    """
    return execute_query(query, [start_vertex_id, end_vertex_id])


def get_dijkstra_geometry_query(start_vertex_id, end_vertex_id):
    """
    Find shortest path between two vertices using Dijkstra's algorithm.
    """
    query = """
    WITH path AS (
        SELECT *
        FROM pgr_dijkstra(
            'SELECT id, source, target, cost FROM transit_edges',
            %s,
            %s,
            directed := true
        )
    )
    SELECT
        p.seq,
        e.from_stop_id,
        e.to_stop_id,
        e.cost,
        ST_AsGeoJSON(e.geom) AS edge_geojson
    FROM path p
    JOIN transit_edges e
        ON p.edge = e.id
    ORDER BY p.seq;
    """
    return execute_query(query, [start_vertex_id, end_vertex_id])


def get_dijkstra_summary_query(start_vertex_id, end_vertex_id):
    query = """
    WITH path AS (
        SELECT *
        FROM pgr_dijkstra(
            'SELECT id, source, target, cost FROM transit_edges',
            %s,
            %s,
            directed := true
        )
    )
    SELECT
        COUNT(*) AS step_count,
        MAX(agg_cost) AS total_cost
    FROM path;
    """
    return execute_query(query, [start_vertex_id, end_vertex_id])


# -----------------------------
# A* ALGORITHM
# -----------------------------

def get_astar_stop_list_query(start_vertex_id, end_vertex_id):
    """
    Find shortest path using A* algorithm with heuristics.
    Returns sequence of stops visited.
    
    Args:
        start_vertex_id: Starting vertex ID
        end_vertex_id: Ending vertex ID
    """
    query = """
    WITH path AS (
        SELECT *
        FROM pgr_astar(
            'SELECT id, source, target, cost, x1, y1, x2, y2 FROM transit_edges',
            %s,
            %s,
            directed := true
        )
    )
    SELECT
        p.seq,
        p.node,
        sv.stop_id,
        s.stop_name,
        s.stop_lat,
        s.stop_lon,
        p.edge,
        p.cost,
        p.agg_cost
    FROM path p
    LEFT JOIN stop_vertices sv
        ON p.node = sv.vertex_id
    LEFT JOIN stops s
        ON sv.stop_id = s.stop_id
    ORDER BY p.seq;
    """
    return execute_query(query, [start_vertex_id, end_vertex_id])


def get_astar_geometry_query(start_vertex_id, end_vertex_id):
    """
    Find shortest path using A* algorithm.
    Returns GeoJSON geometries of edges.
    
    Args:
        start_vertex_id: Starting vertex ID
        end_vertex_id: Ending vertex ID
    """
    query = """
    WITH path AS (
        SELECT *
        FROM pgr_astar(
            'SELECT id, source, target, cost, x1, y1, x2, y2 FROM transit_edges',
            %s,
            %s,
            directed := true
        )
    )
    SELECT
        p.seq,
        e.from_stop_id,
        e.to_stop_id,
        e.cost,
        ST_AsGeoJSON(e.geom) AS edge_geojson
    FROM path p
    JOIN transit_edges e
        ON p.edge = e.id
    ORDER BY p.seq;
    """
    return execute_query(query, [start_vertex_id, end_vertex_id])


def get_astar_summary_query(start_vertex_id, end_vertex_id):
    """
    Get summary statistics of A* path.
    
    Args:
        start_vertex_id: Starting vertex ID
        end_vertex_id: Ending vertex ID
    """
    query = """
    WITH path AS (
        SELECT *
        FROM pgr_astar(
            'SELECT id, source, target, cost, x1, y1, x2, y2 FROM transit_edges',
            %s,
            %s,
            directed := true
        )
    )
    SELECT
        COUNT(*) AS step_count,
        MAX(agg_cost) AS total_cost
    FROM path;
    """
    return execute_query(query, [start_vertex_id, end_vertex_id])


# -----------------------------
# TSP 
# ----------------------------- 

def get_tsp_selected_stops_query(vertex_ids):
    """
    Get selected stops for TSP.
    
    Args:
        vertex_ids: List of vertex IDs to include in TSP
    """
    query = """
    SELECT *
    FROM stop_vertices
    WHERE vertex_id = ANY(%s);
    """
    return execute_query(query, [vertex_ids])


def get_tsp_cost_matrix_query(vertex_ids):
    """
    Get cost matrix between selected stops.
    
    Args:
        vertex_ids: List of vertex IDs to include in cost matrix
    """
    query = """
    SELECT *
    FROM pgr_dijkstraCostMatrix(
        'SELECT id, source, target, cost, cost AS reverse_cost FROM transit_edges',
        %s,
        directed := false
    );
    """
    return execute_query(query, [vertex_ids])


def get_tsp_order_query(conn, cost_matrix, start_id):

    try:
        conn = connect_Database()
        cur = conn.cursor()
        cur.execute("""
            CREATE TEMP TABLE tsp_matrix AS
            SELECT * FROM pgr_dijkstraCostMatrix(
                 'SELECT id, source, target, cost, cost AS reverse_cost FROM transit_edges',
                  %s,
                   directed := false
             );
        """, [cost_matrix])

        cur.execute("""
            SELECT *
            FROM pgr_TSP(
                $$ SELECT * FROM tsp_matrix $$,
                start_id := %s
                );
            """, [start_id])

        results = cur.fetchall()

        cur.execute("DROP TABLE IF EXISTS tsp_matrix;")
        conn.commit()

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



