// ==================== API CONFIGURATION ====================
const API_BASE_URL = 'http://127.0.0.1:8000';

// ==================== MAP INITIALIZATION ====================
let map;
let layers = { stops: null, results: null, paths: null, network: null };
let currentPathLayers = [];
let isDrawingArea = false;
let areaStartPoint = null;

let nearestStopMode = false;
let pickStartMode = false;
let pickEndMode = false;

let selectedStartStop = null;
let selectedEndStop = null;

let allStopsCache = [];
let allRoutesCache = [];

const DEFAULT_CENTER = [41.01, 28.97];
const DEFAULT_ZOOM = 11;

function initMap() {
    map = L.map('map').setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', onMapClick);

    map.on('mousemove', e => {
        const lat = e.latlng.lat.toFixed(4);
        const lon = e.latlng.lng.toFixed(4);
        document.getElementById('coordDisplay').textContent = `Lat: ${lat}, Lon: ${lon}`;
    });

    layers.stops = L.layerGroup().addTo(map);
    layers.results = L.layerGroup().addTo(map);
    layers.paths = L.layerGroup().addTo(map);
    layers.network = L.layerGroup().addTo(map);
}

// ==================== UTILITY FUNCTIONS ====================
function showSpinner(show = true) {
    document.getElementById('loadingSpinner').style.display = show ? 'flex' : 'none';
}

function setResult(html) {
    document.getElementById('resultBox').innerHTML = html;
}

function clearResults() {
    document.getElementById('resultBox').innerHTML = 'Ready';
}

function clearMap() {
    layers.stops.clearLayers();
    layers.results.clearLayers();
    layers.paths.clearLayers();
    layers.network.clearLayers();
    clearResults();
    clearAllInteractiveModes();
}

function clearAllInteractiveModes() {
    nearestStopMode = false;
    pickStartMode = false;
    pickEndMode = false;
    isDrawingArea = false;
    areaStartPoint = null;
}

function onMapClick(e) {
    if (isDrawingArea) {
        if (!areaStartPoint) {
            areaStartPoint = e.latlng;
            setResult('Click to complete area selection...');
        } else {
            completeAreaSelection(e.latlng);
        }
        return;
    }

    if (nearestStopMode) {
        document.getElementById('nearLat').value = e.latlng.lat.toFixed(6);
        document.getElementById('nearLon').value = e.latlng.lng.toFixed(6);
        nearestStopMode = false;
        findNearestStops();
        return;
    }

    if (pickStartMode) {
        pickStartMode = false;
        pickNearestStopForPath(e.latlng.lat, e.latlng.lng, 'start');
        return;
    }

    if (pickEndMode) {
        pickEndMode = false;
        pickNearestStopForPath(e.latlng.lat, e.latlng.lng, 'end');
        return;
    }
}

function getPathInputValues() {
    const rawStart = document.getElementById('pathStart')?.value?.trim() || '';
    const rawEnd = document.getElementById('pathEnd')?.value?.trim() || '';

    const start = rawStart || (selectedStartStop ? selectedStartStop.stop_id : '');
    const end = rawEnd || (selectedEndStop ? selectedEndStop.stop_id : '');

    return { start, end };
}

// ==================== TAB NAVIGATION ====================
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    initMap();
    loadMetroStations();
    loadMetroNetwork();
    updateSelectedStopBoxes();
    populateRouteDropdown();
});

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });

    const activeTab = document.getElementById(tabName + '-tab');
    if (activeTab) activeTab.style.display = 'block';

    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeBtn) activeBtn.classList.add('active');
}

// ==================== FRIENDLY SEARCH / PICK HELPERS ====================
async function loadAllStopsForSearch() {
    if (allStopsCache.length > 0) return allStopsCache;

    const res = await fetch(`${API_BASE_URL}/stops`);
    if (!res.ok) throw new Error('Failed to load stops for search');

    allStopsCache = await res.json();
    return allStopsCache;
}

async function searchStopsByName() {
    const query = document.getElementById('stopNameSearch')?.value?.trim().toLowerCase();
    if (!query) return setResult('Enter a stop name.');

    showSpinner(true);
    try {
        const stops = await loadAllStopsForSearch();

        const matches = stops
            .filter(stop => stop.stop_name && stop.stop_name.toLowerCase().includes(query))
            .slice(0, 15);

        layers.results.clearLayers();

        if (!matches.length) {
            setResult('No matching stops found.');
            return;
        }

        let html = `<h4>Matching Stops</h4>`;

        matches.forEach(stop => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6,
                color: '#2980b9',
                weight: 2,
                fillOpacity: 0.8
            }).bindPopup(`<b>${stop.stop_name}</b><br>ID: ${stop.stop_id}`).addTo(layers.results);

            html += `
                <div style="padding: 6px; border-bottom: 1px solid #ddd; cursor: pointer;"
                     onclick="zoomToStop('${String(stop.stop_id).replace(/'/g, "\\'")}', '${String(stop.stop_name).replace(/'/g, "\\'")}', ${stop.stop_lat}, ${stop.stop_lon})">
                    <b>${stop.stop_name}</b><br>
                    ID: ${stop.stop_id}
                </div>
            `;
        });

        setResult(html);

        const bounds = L.latLngBounds(matches.map(s => [s.stop_lat, s.stop_lon]));
        if (bounds.isValid()) map.fitBounds(bounds);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function zoomToStop(stopId, stopName, lat, lon) {
    layers.results.clearLayers();

    L.circleMarker([lat, lon], {
        radius: 8,
        color: '#e74c3c',
        weight: 2,
        fillOpacity: 0.9
    }).bindPopup(`<b>${stopName}</b><br>ID: ${stopId}`).addTo(layers.results);

    map.setView([lat, lon], 15);
    setResult(`<b>${stopName}</b><br>ID: ${stopId}<br>Lat: ${lat}<br>Lon: ${lon}`);
}

async function populateRouteDropdown() {
    try {
        const res = await fetch(`${API_BASE_URL}/gtfs/routes`);
        if (!res.ok) throw new Error('Failed to load routes');

        const raw = await res.json();
        const routes = Array.isArray(raw) ? raw : (raw.routes || raw.data || []);
        allRoutesCache = routes;

        const select = document.getElementById('routeSelect');
        if (!select) return;

        select.innerHTML = `<option value="">Choose a route...</option>`;

        routes.forEach(route => {
            const option = document.createElement('option');
            option.value = route.route_id;
            option.textContent = `${route.route_short_name || route.route_id} - ${route.route_long_name || 'N/A'}`;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Failed to populate route dropdown:', err);
    }
}

function showSelectedRouteFromDropdown() {
    const routeId = document.getElementById('routeSelect')?.value;
    if (!routeId) return setResult('Please choose a route first.');
    showRouteWithStops(routeId);
}

function updateSelectedStopBoxes() {
    const startBox = document.getElementById('selectedStartBox');
    const endBox = document.getElementById('selectedEndBox');

    if (startBox) {
        startBox.innerHTML = selectedStartStop
            ? `<b>Start:</b> ${selectedStartStop.stop_name}<br>ID: ${selectedStartStop.stop_id}`
            : 'No start stop selected.';
    }

    if (endBox) {
        endBox.innerHTML = selectedEndStop
            ? `<b>End:</b> ${selectedEndStop.stop_name}<br>ID: ${selectedEndStop.stop_id}`
            : 'No end stop selected.';
    }
}

function syncSelectedStopsToRawInputs() {
    const rawStart = document.getElementById('pathStart');
    const rawEnd = document.getElementById('pathEnd');

    if (rawStart) rawStart.value = selectedStartStop ? selectedStartStop.stop_id : '';
    if (rawEnd) rawEnd.value = selectedEndStop ? selectedEndStop.stop_id : '';
}

function enableNearestStopMode() {
    clearAllInteractiveModes();
    nearestStopMode = true;
    setResult('Click on the map to find nearest stops.');
}

function enablePickStartMode() {
    clearAllInteractiveModes();
    pickStartMode = true;
    setResult('Click on the map to choose the START stop.');
}

function enablePickEndMode() {
    clearAllInteractiveModes();
    pickEndMode = true;
    setResult('Click on the map to choose the END stop.');
}

async function pickNearestStopForPath(lat, lon, type) {
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/nearest?lat=${lat}&lon=${lon}&radius=500`);
        if (!res.ok) throw new Error('Failed to find nearby stops');

        const stops = await res.json();
        if (!stops.length) throw new Error('No nearby stop found');

        const stop = stops[0];

        if (type === 'start') selectedStartStop = stop;
        else selectedEndStop = stop;

        updateSelectedStopBoxes();
        syncSelectedStopsToRawInputs();

        layers.results.clearLayers();
        L.circleMarker([stop.stop_lat, stop.stop_lon], {
            radius: 8,
            color: type === 'start' ? '#27ae60' : '#c0392b',
            weight: 2,
            fillOpacity: 0.9
        }).bindPopup(`<b>${type.toUpperCase()}</b><br>${stop.stop_name}`).addTo(layers.results);

        map.setView([stop.stop_lat, stop.stop_lon], 15);
        setResult(`Selected ${type} stop: <b>${stop.stop_name}</b>`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function searchStartStop() {
    await searchStopForPath('pathStartName', 'start');
}

async function searchEndStop() {
    await searchStopForPath('pathEndName', 'end');
}

async function searchStopForPath(inputId, type) {
    const query = document.getElementById(inputId)?.value?.trim().toLowerCase();
    if (!query) return setResult('Enter a stop name.');

    showSpinner(true);
    try {
        const stops = await loadAllStopsForSearch();
        const matches = stops
            .filter(stop => stop.stop_name && stop.stop_name.toLowerCase().includes(query))
            .slice(0, 10);

        if (!matches.length) {
            setResult('No matching stops found.');
            return;
        }

        let html = `<h4>Select ${type} stop</h4>`;

        matches.forEach(stop => {
            html += `
                <div style="padding: 6px; border-bottom: 1px solid #ddd; cursor: pointer;"
                     onclick="chooseStopForPath('${type}', '${String(stop.stop_id).replace(/'/g, "\\'")}', '${String(stop.stop_name).replace(/'/g, "\\'")}', ${stop.stop_lat}, ${stop.stop_lon})">
                    <b>${stop.stop_name}</b><br>ID: ${stop.stop_id}
                </div>
            `;
        });

        setResult(html);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function chooseStopForPath(type, stopId, stopName, lat, lon) {
    const stopObj = {
        stop_id: stopId,
        stop_name: stopName,
        stop_lat: lat,
        stop_lon: lon
    };

    if (type === 'start') selectedStartStop = stopObj;
    else selectedEndStop = stopObj;

    updateSelectedStopBoxes();
    syncSelectedStopsToRawInputs();

    layers.results.clearLayers();
    L.circleMarker([lat, lon], {
        radius: 8,
        color: type === 'start' ? '#27ae60' : '#c0392b',
        weight: 2,
        fillOpacity: 0.9
    }).bindPopup(`<b>${type.toUpperCase()}</b><br>${stopName}`).addTo(layers.results);

    map.setView([lat, lon], 15);
    setResult(`Selected ${type} stop: <b>${stopName}</b>`);
}

// ==================== STOPS FUNCTIONS ====================
async function getStopById() {
    const stopId = document.getElementById('stopId')?.value;
    if (!stopId) return setResult('Enter a stop ID');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/${stopId}`);
        if (!res.ok) throw new Error('Stop not found');

        const stop = await res.json();

        layers.results.clearLayers();
        L.circleMarker([stop.stop_lat, stop.stop_lon], {
            radius: 8,
            color: '#e74c3c',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).bindPopup(`<b>${stop.stop_name}</b><br>ID: ${stop.stop_id}`).addTo(layers.results);

        map.setView([stop.stop_lat, stop.stop_lon], 14);
        setResult(`<b>${stop.stop_name}</b><br>ID: ${stop.stop_id}<br>Lat: ${stop.stop_lat}<br>Lon: ${stop.stop_lon}`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function getStopByCode() {
    const code = document.getElementById('stopCode')?.value;
    if (!code) return setResult('Enter a stop code');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/by-code/${code}`);
        if (!res.ok) throw new Error('Stop code not found');

        const stops = await res.json();

        layers.results.clearLayers();
        let html = `<h4>Found ${stops.length} stop(s)</h4>`;

        stops.forEach(stop => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6,
                color: '#3498db',
                weight: 2,
                fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>Code: ${stop.stop_code}`).addTo(layers.results);

            html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
                <b>${stop.stop_name}</b><br>
                Code: ${stop.stop_code} | ID: ${stop.stop_id}
            </div>`;
        });

        setResult(html);
        if (stops.length > 0) map.setView([stops[0].stop_lat, stops[0].stop_lon], 13);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadAllStops() {
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops`);
        if (!res.ok) throw new Error('Failed to load stops');

        const stops = await res.json();

        layers.stops.clearLayers();
        const mcg = L.markerClusterGroup();

        stops.forEach(stop => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 5,
                color: '#27ae60',
                weight: 1,
                fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>ID: ${stop.stop_id}`);
            mcg.addLayer(marker);
        });

        layers.stops.addLayer(mcg);
        setResult(`Loaded ${stops.length} stops`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}
async function findNearestStops() {
    const lat = document.getElementById('nearLat')?.value;
    const lon = document.getElementById('nearLon')?.value;
    const radius = document.getElementById('nearRadius')?.value || 500;
    const k = parseInt(document.getElementById('nearLimit')?.value || 5);

    if (!lat || !lon) return setResult('Enter latitude and longitude');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/nearest?lat=${lat}&lon=${lon}&radius=${radius}&k=${k}`);
        if (!res.ok) throw new Error('No stops found');

        const stops = await res.json();
        const limitedStops = stops.slice(0, k);

        layers.results.clearLayers();

        L.circleMarker([lat, lon], {
            radius: 8,
            color: '#f39c12',
            weight: 2,
            fillOpacity: 0.9
        }).addTo(layers.results);

        L.circle([lat, lon], {
            radius: radius,
            color: '#95a5a6',
            fill: false
        }).addTo(layers.results);

        let html = `<h4>Nearest ${limitedStops.length} Stops</h4>`;

        limitedStops.forEach((stop, i) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 8,
                color: '#9b59b6',
                weight: 1,
                fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>Distance: ${Math.round(stop.distance_m)}m`).addTo(layers.results);

            html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
                ${i + 1}. <b>${stop.stop_name}</b><br>
                Distance: ${Math.round(stop.distance_m)}m
            </div>`;
        });

        map.setView([parseFloat(lat), parseFloat(lon)], 13);
        setResult(html);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function enableAreaSelection() {
    clearAllInteractiveModes();
    isDrawingArea = true;
    areaStartPoint = null;
    setResult('Click on map to start area selection...');
}

async function completeAreaSelection(endPoint) {
    isDrawingArea = false;

    const minLat = Math.min(areaStartPoint.lat, endPoint.lat);
    const maxLat = Math.max(areaStartPoint.lat, endPoint.lat);
    const minLon = Math.min(areaStartPoint.lng, endPoint.lng);
    const maxLon = Math.max(areaStartPoint.lng, endPoint.lng);

    areaStartPoint = null;

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/inarea?min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}`);
        if (!res.ok) throw new Error('No stops found');

        const stops = await res.json();

        layers.results.clearLayers();
        L.rectangle([[minLat, minLon], [maxLat, maxLon]], {
            color: '#3498db',
            weight: 2,
            fill: false
        }).addTo(layers.results);

        stops.forEach(stop => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 5,
                color: '#9b59b6',
                weight: 1,
                fillOpacity: 0.7
            }).bindPopup(stop.stop_name).addTo(layers.results);
        });

        setResult(`Found ${stops.length} stops in area`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function useCurrentMapWindow() {
    const bounds = map.getBounds();

    const minLat = bounds.getSouth();
    const maxLat = bounds.getNorth();
    const minLon = bounds.getWest();
    const maxLon = bounds.getEast();

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/inarea?min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}`);
        if (!res.ok) throw new Error('No stops found in current map window');

        const stops = await res.json();

        layers.results.clearLayers();

        L.rectangle([[minLat, minLon], [maxLat, maxLon]], {
            color: '#3498db',
            weight: 2,
            fill: false
        }).addTo(layers.results);

        stops.forEach(stop => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 5,
                color: '#9b59b6',
                weight: 1,
                fillOpacity: 0.7
            }).bindPopup(stop.stop_name).addTo(layers.results);
        });

        setResult(`Found ${stops.length} stops in the current map window.`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== ROUTES FUNCTIONS ====================
async function loadTopRoutes() {
    const limit = document.getElementById('topRoutesLimit')?.value || 10;
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/top-routes?limit=${limit}`);
        if (!res.ok) throw new Error('Failed to load routes');

        const data = await res.json();

        let html = `<h4>Top ${limit} Routes by Trips</h4>`;
        data.top_routes.forEach(route => {
            html += `<div style="padding: 8px; background: #ecf0f1; margin: 5px 0; border-radius: 4px; cursor: pointer;" onclick="showRouteWithStops('${route.route_id}')">
                <b>${route.route_short_name}</b> - ${route.route_long_name || 'N/A'}<br>
                <small>Trips: ${route.trip_count} | Stops: ${route.stop_count}</small>
            </div>`;
        });

        setResult(html);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function showRouteWithStops(routeId = null) {
    const id = routeId || document.getElementById('routeId')?.value;
    if (!id) return setResult('Enter a route ID');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/route/${id}`);
        if (!res.ok) throw new Error('Route not found');

        const data = await res.json();

        layers.results.clearLayers();

        const latlngs = data.stops.map(s => [s.stop_lat, s.stop_lon]);

        L.polyline(latlngs, {
            color: '#e74c3c',
            weight: 3,
            opacity: 0.7
        }).addTo(layers.results);

        data.stops.forEach((stop, i) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6,
                color: '#27ae60',
                weight: 2,
                fillOpacity: 0.9
            }).bindPopup(`${i + 1}. ${stop.stop_name}`).addTo(layers.results);
        });

        let html = `<h4>Route: ${data.route.route_short_name}</h4>
            <b>Name:</b> ${data.route.route_long_name || 'N/A'}<br>
            <b>Stops:</b> ${data.stop_count}<br>
            <b>Trips:</b> ${data.route.trip_count}<br>
            <h5>Stops in Order:</h5>`;

        data.stops.forEach((stop, i) => {
            html += `<div style="padding: 4px 0; border-bottom: 1px solid #ddd;">
                ${i + 1}. <b>${stop.stop_name}</b> (${stop.stop_id})
            </div>`;
        });

        setResult(html);

        if (data.stops.length > 0) {
            const bounds = L.latLngBounds(latlngs);
            map.fitBounds(bounds);
        }
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== PATHFINDING FUNCTIONS ====================
async function runDijkstra() {
    const { start, end } = getPathInputValues();
    if (!start || !end) return setResult('Choose start and end stops.');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/dijkstra?start=${start}&end=${end}`);
        if (!res.ok) throw new Error('Path not found');

        const data = await res.json();

        const pathData = {
            algorithm: 'Dijkstra',
            path: (data.stops || []).map(stop => ({
                stop_id: stop.stop_id,
                stop_name: stop.stop_name,
                lat: stop.stop_lat,
                lon: stop.stop_lon,
                distance_from_start: stop.agg_cost ?? stop.cost ?? 0
            })),
            total_distance: data.summary?.total_distance ?? data.summary?.total_cost ?? 0,
            hops: (data.stops || []).length
        };

        drawPath(pathData, 'Dijkstra', '#3498db');
        displayPathInfo(pathData);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function runAStar() {
    const { start, end } = getPathInputValues();
    if (!start || !end) return setResult('Choose start and end stops.');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/astar?start=${start}&end=${end}`);
        if (!res.ok) throw new Error('Path not found');

        const data = await res.json();

        const pathData = {
            algorithm: 'A*',
            path: (data.stops || []).map(stop => ({
                stop_id: stop.stop_id,
                stop_name: stop.stop_name,
                lat: stop.stop_lat,
                lon: stop.stop_lon,
                distance_from_start: stop.agg_cost ?? stop.cost ?? 0
            })),
            total_distance: data.summary?.total_distance ?? data.summary?.total_cost ?? 0,
            hops: (data.stops || []).length
        };

        drawPath(pathData, 'A*', '#e74c3c');
        displayPathInfo(pathData);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function comparePaths() {
    const { start, end } = getPathInputValues();
    if (!start || !end) return setResult('Choose start and end stops.');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/compare-paths?start=${start}&end=${end}`);
        if (!res.ok) throw new Error('Comparison failed');

        const data = await res.json();

        layers.paths.clearLayers();

        const dijkstraLatlngs = data.dijkstra.path.map(p => [p.lat, p.lon]);
        const astarLatlngs = data.astar.path.map(p => [p.lat, p.lon]);

        L.polyline(dijkstraLatlngs, {
            color: '#3498db',
            weight: 3,
            opacity: 0.6,
            dashArray: '5,5'
        }).addTo(layers.paths);

        L.polyline(astarLatlngs, {
            color: '#e74c3c',
            weight: 3,
            opacity: 0.6
        }).addTo(layers.paths);

        dijkstraLatlngs.forEach(p => {
            L.circleMarker(p, { radius: 4, color: '#3498db', weight: 1 }).addTo(layers.paths);
        });

        astarLatlngs.forEach(p => {
            L.circleMarker(p, { radius: 4, color: '#e74c3c', weight: 1 }).addTo(layers.paths);
        });

        const comparison = data.comparison;
        let html = `<h4>Algorithm Comparison</h4>
            <div style="background: #ecf0f1; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
            <b>Dijkstra:</b> ${Math.round(comparison.dijkstra_distance)}m, ${comparison.dijkstra_hops} hops<br>
            <b>A*:</b> ${Math.round(comparison.astar_distance)}m, ${comparison.astar_hops} hops<br>
            <b>Same Path:</b> ${comparison.same_path ? 'Yes' : 'No'}
            </div>
            <h5>Dijkstra Path:</h5>`;

        data.dijkstra.path.forEach(p => {
            html += `<div style="padding: 3px; font-size: 0.9em;"><b>${p.stop_name}</b> (${Math.round(p.distance_from_start)}m)</div>`;
        });

        html += `<hr><h5>A* Path:</h5>`;

        data.astar.path.forEach(p => {
            html += `<div style="padding: 3px; font-size: 0.9em;"><b>${p.stop_name}</b> (${Math.round(p.distance_from_start)}m)</div>`;
        });

        setResult(html);

        const bounds = L.latLngBounds(dijkstraLatlngs.concat(astarLatlngs));
        if (bounds.isValid()) map.fitBounds(bounds);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

function drawPath(path, algorithm, color) {
    layers.paths.clearLayers();

    const latlngs = path.path.map(p => [p.lat, p.lon]);
    if (!latlngs.length) return;

    L.polyline(latlngs, {
        color: color,
        weight: 3,
        opacity: 0.8
    }).addTo(layers.paths);

    path.path.forEach((stop, i) => {
        L.circleMarker([stop.lat, stop.lon], {
            radius: 5,
            color: color,
            weight: 2,
            fillOpacity: 0.8
        }).bindPopup(`${i + 1}. ${stop.stop_name}`).addTo(layers.paths);
    });

    const bounds = L.latLngBounds(latlngs);
    if (bounds.isValid()) map.fitBounds(bounds);
}

function displayPathInfo(path) {
    let html = `<h4>${path.algorithm} Path</h4>
        Total Distance: ${Math.round(path.total_distance)}m<br>
        Hops: ${path.hops}<br>
        <h5>Route:</h5>`;

    path.path.forEach((stop, i) => {
        html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
            ${i + 1}. <b>${stop.stop_name}</b><br>
            Distance from start: ${Math.round(stop.distance_from_start)}m
        </div>`;
    });

    setResult(html);
}

// ==================== NETWORK FUNCTIONS ====================
function displayFullNetwork() {
    loadAllStops();
}

// ==================== ANALYSIS FUNCTIONS ====================
async function showBusiestStops() {
    const startHour = document.getElementById('busyStart')?.value || 6;
    const endHour = document.getElementById('busyEnd')?.value || 9;

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/busiest-stops?start_hour=${startHour}&end_hour=${endHour}`);
        if (!res.ok) throw new Error('Analysis failed');

        const data = await res.json();

        layers.results.clearLayers();

        let html = `<h4>Busiest Stops: ${data.time_range}</h4>`;

        data.busiest_stops.forEach((stop, i) => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: Math.max(5, Math.min(12, stop.total_visits / 10)),
                color: '#e74c3c',
                weight: 1,
                fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>Visits: ${stop.total_visits}`).addTo(layers.results);

            html += `<div style="padding: 5px; background: #f39c12; color: white; border-radius: 3px; margin: 3px 0;">
                ${i + 1}. <b>${stop.stop_name}</b><br>
                Visits: ${stop.total_visits} | Routes: ${stop.unique_routes}
            </div>`;
        });

        setResult(html);

        if (data.busiest_stops.length > 0) {
            const bounds = L.latLngBounds(data.busiest_stops.map(s => [s.stop_lat, s.stop_lon]));
            if (bounds.isValid()) map.fitBounds(bounds);
        }
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

// ==================== MOBILITYDB FUNCTIONS ====================
function setMobilityTimePreset(value) {
    const input = document.getElementById('mobilityTime');
    if (input) input.value = value;
}

function loadMobilityCurrentWindow() {
    const bounds = map.getBounds();

    document.getElementById('minLon').value = bounds.getWest().toFixed(6);
    document.getElementById('minLat').value = bounds.getSouth().toFixed(6);
    document.getElementById('maxLon').value = bounds.getEast().toFixed(6);
    document.getElementById('maxLat').value = bounds.getNorth().toFixed(6);

    loadMobilityWindow();
}

async function loadMobilityTrajectories() {
    showSpinner(true);
    try {
        layers.results.clearLayers();

        const res = await fetch(`${API_BASE_URL}/mobility/trajectories`);
        if (!res.ok) throw new Error('Failed to load trajectories');

        const data = await res.json();

        const geoLayer = L.geoJSON(data, {
            style: {
                color: '#8e44ad',
                weight: 4,
                opacity: 0.8
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                layer.bindPopup(`
                    <b>Vehicle:</b> ${props.vehicle_id || 'N/A'}<br>
                    <b>Route:</b> ${props.route_id || 'N/A'}
                `);
            }
        }).addTo(layers.results);

        if (data.features && data.features.length > 0) {
            const bounds = geoLayer.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds);
        }

        setResult(`<h4>MobilityDB Trajectories</h4>
            Loaded ${data.features ? data.features.length : 0} trajectory feature(s).`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadMobilityAtTime() {
    const timestamp = document.getElementById('mobilityTime')?.value;
    if (!timestamp) return setResult('Enter a timestamp');

    showSpinner(true);
    try {
        layers.results.clearLayers();

        const res = await fetch(`${API_BASE_URL}/mobility/at-time?timestamp=${encodeURIComponent(timestamp)}`);
        if (!res.ok) throw new Error('Failed to load positions at time');

        const data = await res.json();

        const geoLayer = L.geoJSON(data, {
            pointToLayer: function(feature, latlng) {
                return L.circleMarker(latlng, {
                    radius: 7,
                    color: '#e74c3c',
                    weight: 2,
                    fillOpacity: 0.9
                });
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                layer.bindPopup(`
                    <b>Vehicle:</b> ${props.vehicle_id || 'N/A'}<br>
                    <b>Route:</b> ${props.route_id || 'N/A'}
                `);
            }
        }).addTo(layers.results);

        if (data.features && data.features.length > 0) {
            const bounds = geoLayer.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds);
        }

        setResult(`<h4>MobilityDB Positions</h4>
            Timestamp: ${timestamp}<br>
            Loaded ${data.features ? data.features.length : 0} position(s).`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadMobilityWindow() {
    const minLon = document.getElementById('minLon')?.value;
    const minLat = document.getElementById('minLat')?.value;
    const maxLon = document.getElementById('maxLon')?.value;
    const maxLat = document.getElementById('maxLat')?.value;

    if (!minLon || !minLat || !maxLon || !maxLat) {
        return setResult('Enter all bounding box values');
    }

    showSpinner(true);
    try {
        layers.results.clearLayers();

        const res = await fetch(
            `${API_BASE_URL}/mobility/in-window?min_lon=${minLon}&min_lat=${minLat}&max_lon=${maxLon}&max_lat=${maxLat}`
        );
        if (!res.ok) throw new Error('Failed to load trajectories in window');

        const data = await res.json();

        L.rectangle([[parseFloat(minLat), parseFloat(minLon)], [parseFloat(maxLat), parseFloat(maxLon)]], {
            color: '#3498db',
            weight: 2,
            fill: false
        }).addTo(layers.results);

        const geoLayer = L.geoJSON(data, {
            style: {
                color: '#16a085',
                weight: 4,
                opacity: 0.8
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                layer.bindPopup(`
                    <b>Vehicle:</b> ${props.vehicle_id || 'N/A'}<br>
                    <b>Route:</b> ${props.route_id || 'N/A'}
                `);
            }
        }).addTo(layers.results);

        if (data.features && data.features.length > 0) {
            const bounds = geoLayer.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds);
        }

        setResult(`<h4>MobilityDB Spatial Window</h4>
            Loaded ${data.features ? data.features.length : 0} trajectory feature(s).`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadMetroStations() {
    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/metro-stations`);
        if (!res.ok) throw new Error('Failed to load metro stations');

        const stations = await res.json();

        const startSelect = document.getElementById('metroStartSelect');
        const endSelect = document.getElementById('metroEndSelect');

        if (!startSelect || !endSelect) return;

        startSelect.innerHTML = `<option value="">Choose start station...</option>`;
        endSelect.innerHTML = `<option value="">Choose end station...</option>`;

        stations.forEach(station => {
            const text = `${station.stop_name} (${station.stop_id})`;

            const opt1 = document.createElement('option');
            opt1.value = station.stop_id;
            opt1.textContent = text;
            startSelect.appendChild(opt1);

            const opt2 = document.createElement('option');
            opt2.value = station.stop_id;
            opt2.textContent = text;
            endSelect.appendChild(opt2);
        });

        setResult(`Loaded ${stations.length} metro stations.`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function loadMetroNetwork() {
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/metro-network`);
        if (!res.ok) throw new Error('Failed to load metro network');

        const data = await res.json();

        layers.network.clearLayers();

        L.geoJSON(data, {
            style: {
                color: '#7f8c8d',
                weight: 3,
                opacity: 0.6
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                layer.bindPopup(`
                    <b>${props.route_short_name || 'Metro Line'}</b><br>
                    ${props.route_long_name || ''}
                `);
            }
        }).addTo(layers.network);

    } catch (err) {
        setResult(`Error loading metro network: ${err.message}`);
    }
}
function syncMetroDropdownsToPathInputs() {
    const start = document.getElementById('metroStartSelect')?.value || '';
    const end = document.getElementById('metroEndSelect')?.value || '';

    const rawStart = document.getElementById('pathStart');
    const rawEnd = document.getElementById('pathEnd');

    if (rawStart) rawStart.value = start;
    if (rawEnd) rawEnd.value = end;
}