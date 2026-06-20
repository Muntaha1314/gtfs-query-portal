// ==================== API CONFIGURATION ====================
const API_BASE_URL = window.location.origin;

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
    const stopId = document.getElementById('stopId')?.value?.trim();
    if (!stopId) return setResult('Enter a stop ID');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/${encodeURIComponent(stopId)}`);
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || 'Stop not found');
        }

        const stop = await res.json();

        layers.results.clearLayers();
        L.circleMarker([stop.stop_lat, stop.stop_lon], {
            radius: 8,
            color: '#e74c3c',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).bindPopup(`<b>${stop.stop_name}</b><br>ID: ${stop.stop_id}<br>Code: ${stop.stop_code || 'N/A'}`).addTo(layers.results);

        map.setView([stop.stop_lat, stop.stop_lon], 14);
        setResult(`<b>${stop.stop_name}</b><br>ID: ${stop.stop_id}<br>Code: ${stop.stop_code || 'N/A'}<br>Lat: ${stop.stop_lat}<br>Lon: ${stop.stop_lon}`);
    } catch (err) {
        setResult(`Error: ${err.message}`);
    } finally {
        showSpinner(false);
    }
}

async function getStopByCode() {
    const code = document.getElementById('stopCode')?.value?.trim();
    if (!code) return setResult('Enter a stop code');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/stops/by-code/${encodeURIComponent(code)}`);
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || 'Stop code not found');
        }

        const stops = await res.json();

        layers.results.clearLayers();
        
        if (!stops || stops.length === 0) {
            setResult('No stops found with that code');
            return;
        }

        let html = `<h4>Found ${stops.length} stop(s)</h4>`;

        stops.forEach(stop => {
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6,
                color: '#3498db',
                weight: 2,
                fillOpacity: 0.7
            }).bindPopup(`${stop.stop_name}<br>Code: ${stop.stop_code}<br>ID: ${stop.stop_id}`).addTo(layers.results);

            html += `<div style="padding: 5px; border-bottom: 1px solid #ddd;">
                <b>${stop.stop_name}</b><br>
                Code: <b>${stop.stop_code}</b> | ID: ${stop.stop_id}<br>
                Coords: ${stop.stop_lat.toFixed(4)}, ${stop.stop_lon.toFixed(4)}
            </div>`;
        });

        setResult(html);
        if (stops.length > 0) {
            const bounds = L.latLngBounds(stops.map(s => [s.stop_lat, s.stop_lon]));
            map.fitBounds(bounds);
        }
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
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || 'Failed to load stops');
        }

        const stops = await res.json();
        if (!stops || stops.length === 0) throw new Error('No stops found in database');

        layers.stops.clearLayers();
        const mcg = L.markerClusterGroup();

        stops.forEach(stop => {
            const marker = L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 8,
                color: '#9b59b6',
                weight: 1,
                fillOpacity: 0.7
            }).bindPopup(`<b>${stop.stop_name}</b><br>ID: ${stop.stop_id}<br>Code: ${stop.stop_code || 'N/A'}`);
            mcg.addLayer(marker);
        });

        layers.stops.addLayer(mcg);
        setResult(` Loaded ${stops.length} stops with clustering enabled. Zoom in to see individual stops.`);
        
        // Fit bounds to all stops
        if (stops.length > 0) {
            const bounds = L.latLngBounds(stops.map(s => [s.stop_lat, s.stop_lon]));
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    } catch (err) {
        setResult(` Error: ${err.message}`);
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
    const limit = document.getElementById('topRoutesLimit')?.value?.trim() || 10;
    
    if (isNaN(limit) || limit < 1) {
        return setResult('Enter a valid number for route limit');
    }

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/top-routes?limit=${encodeURIComponent(limit)}`);
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || 'Failed to load routes');
        }

        const data = await res.json();
        if (!data.top_routes || data.top_routes.length === 0) {
            return setResult('No routes found');
        }

        let html = `<h4>Top ${limit} Routes by Trips</h4>
            <p style="color: #666; margin-bottom: 10px;">Click a route to view all stops</p>`;
        
        data.top_routes.forEach((route, idx) => {
            html += `<div style="padding: 8px; background: #ecf0f1; margin: 5px 0; border-radius: 4px; cursor: pointer; transition: all 0.2s;" 
                         onmouseover="this.style.background='#d5dbdb'" onmouseout="this.style.background='#ecf0f1'"
                         onclick="showRouteWithStops('${String(route.route_id).replace(/'/g, "\\'")}')">
                <b>${idx + 1}. ${route.route_short_name}</b> - ${route.route_long_name || 'N/A'}<br>
                <small style="color: #555;">${route.stop_count} stops | ${route.trip_count} trips</small>
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
    const id = routeId || document.getElementById('routeId')?.value?.trim();
    if (!id) return setResult('Enter a route ID');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/route/${encodeURIComponent(id)}`);
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || 'Route not found');
        }

        const data = await res.json();
        if (!data.stops || data.stops.length === 0) throw new Error('No stops found for this route');

        layers.results.clearLayers();

        const latlngs = data.stops.map(s => [s.stop_lat, s.stop_lon]);

        L.polyline(latlngs, {
            color: '#e74c3c',
            weight: 3,
            opacity: 0.7
        }).addTo(layers.results);

        data.stops.forEach((stop, i) => {
            let markerColor = '#27ae60';
            if (i === 0) markerColor = '#3498db';
            else if (i === data.stops.length - 1) markerColor = '#e74c3c';
            
            L.circleMarker([stop.stop_lat, stop.stop_lon], {
                radius: 6,
                color: markerColor,
                weight: 2,
                fillOpacity: 0.9
            }).bindPopup(`<b>${i + 1}. ${stop.stop_name}</b><br>ID: ${stop.stop_id}`).addTo(layers.results);
        });

        let html = `<h4>Route: ${data.route.route_short_name}</h4>
            <b>Name:</b> ${data.route.route_long_name || 'N/A'}<br>
            <b>Stops:</b> ${data.stop_count}<br>
            <b>Trips:</b> ${data.route.trip_count}<br>
            <hr>
            <h5>Stops in Order:</h5>`;

        data.stops.forEach((stop, i) => {
            html += `<div style="padding: 4px 0; border-bottom: 1px solid #ddd;">
                <b>${i + 1}.</b> ${stop.stop_name} <br>
                <span style="color: #666; font-size: 0.9em;">ID: ${stop.stop_id}</span>
            </div>`;
        });

        setResult(html);

        if (data.stops.length > 0) {
            const bounds = L.latLngBounds(latlngs);
            map.fitBounds(bounds, { padding: [50, 50] });
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
    if (!start || !end) return setResult('Enter start and end stop IDs');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/dijkstra?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || 'Path not found');
        }

        const data = await res.json();
        if (!data.path || data.path.length === 0) throw new Error('No path found between stops');

        const pathData = {
            algorithm: data.algorithm || 'Dijkstra',
            path: (data.path || []).map(stop => ({
                stop_id: stop.stop_id,
                stop_name: stop.stop_name,
                lat: stop.stop_lat,
                lon: stop.stop_lon,
                distance_from_start: stop.distance_from_start ?? 0
            })),
            total_distance: data.total_distance ?? 0,
            hops: data.hops ?? (data.path || []).length
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
    if (!start || !end) return setResult('Enter start and end stop IDs');

    showSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/analysis/astar?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || 'Path not found');
        }

        const data = await res.json();
        if (!data.path || data.path.length === 0) throw new Error('No path found between stops');

        const pathData = {
            algorithm: data.algorithm || 'A*',
            path: (data.path || []).map(stop => ({
                stop_id: stop.stop_id,
                stop_name: stop.stop_name,
                lat: stop.stop_lat,
                lon: stop.stop_lon,
                distance_from_start: stop.distance_from_start ?? 0
            })),
            total_distance: data.total_distance ?? 0,
            hops: data.hops ?? (data.path || []).length
        };

        drawPath(pathData, 'A*', '#e74c3c');
        displayPathInfo(pathData);
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

// Color palette for different vehicles
const vehicleColors = {
    'V101': '#e74c3c',   // Red
    'V102': '#3498db',   // Blue
    'V103': '#2ecc71',   // Green
    'V104': '#f39c12',   // Orange
    'V105': '#9b59b6'    // Purple
};

function getVehicleColor(vehicleId) {
    return vehicleColors[vehicleId] || '#95a5a6'; // Default gray
}

async function loadMobilityTrajectories() {
    showSpinner(true);
    try {
        layers.results.clearLayers();

        const res = await fetch(`${API_BASE_URL}/mobility/trajectories`);
        if (!res.ok) throw new Error('Failed to load trajectories');

        const data = await res.json();
        const vehicleStats = {};

        const geoLayer = L.geoJSON(data, {
            style: function(feature) {
                const vehicleId = feature.properties?.vehicle_id || 'UNKNOWN';
                if (!vehicleStats[vehicleId]) {
                    vehicleStats[vehicleId] = { route: feature.properties?.route_id || 'N/A' };
                }
                return {
                    color: getVehicleColor(vehicleId),
                    weight: 5,
                    opacity: 0.85,
                    lineCap: 'round',
                    lineJoin: 'round'
                };
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                const popup = `
                    <div style="font-family: monospace; font-size: 12px;">
                        <b style="color: ${getVehicleColor(props.vehicle_id)}">▓ ${props.vehicle_id}</b><br>
                        <i>Route:</i> <b>${props.route_id || 'N/A'}</b><br>
                        <i>Path points:</i> ${feature.geometry?.coordinates?.length || '?'}
                    </div>
                `;
                layer.bindPopup(popup);
            }
        }).addTo(layers.results);

        // Create legend
        let legendHTML = '<h4 style="margin: 0 0 8px 0;">Vehicle Trajectories</h4>';
        Object.entries(vehicleStats).forEach(([vid, info]) => {
            legendHTML += `<div style="margin: 4px 0;"><span style="color: ${getVehicleColor(vid)}; font-weight: bold;">▓▓▓</span> ${vid} (${info.route})</div>`;
        });

        if (data.features && data.features.length > 0) {
            const bounds = geoLayer.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds, { padding: [50, 50] });
        }

        setResult(`<h4>Full Vehicle Trajectories</h4>
            <div style="font-size: 0.9rem;">
                <p>Showing complete paths of <b>${Object.keys(vehicleStats).length} vehicle(s)</b></p>
                ${legendHTML}
                <p style="font-size: 0.85rem; color: #666; margin-top: 8px;"><i>Click paths for details</i></p>
            </div>`);
    } catch (err) {
        setResult(`<span style="color: #e74c3c;">Error: ${err.message}</span>`);
    } finally {
        showSpinner(false);
    }
}

async function loadMobilityAtTime() {
    const timestamp = document.getElementById('mobilityTime')?.value;
    if (!timestamp) return setResult('Enter a timestamp (e.g., 2026-05-25 08:05:00+03)');

    showSpinner(true);
    try {
        layers.results.clearLayers();

        const res = await fetch(`${API_BASE_URL}/mobility/at-time?timestamp=${encodeURIComponent(timestamp)}`);
        if (!res.ok) throw new Error('Failed to load positions at time');

        const data = await res.json();

        const geoLayer = L.geoJSON(data, {
            pointToLayer: function(feature, latlng) {
                const vehicleId = feature.properties?.vehicle_id || 'UNKNOWN';
                return L.circleMarker(latlng, {
                    radius: 12,
                    color: getVehicleColor(vehicleId),
                    weight: 3,
                    fillOpacity: 0.9,
                    fillColor: getVehicleColor(vehicleId)
                });
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                const popup = `
                    <div style="font-family: monospace; font-size: 12px;">
                        <b style="color: ${getVehicleColor(props.vehicle_id)}">● ${props.vehicle_id}</b><br>
                        <i>Route:</i> <b>${props.route_id || 'N/A'}</b><br>
                        <i>Time:</i> ${timestamp.split('+')[0]}
                    </div>
                `;
                layer.bindPopup(popup);
                layer.openPopup();
            }
        }).addTo(layers.results);

        if (data.features && data.features.length > 0) {
            const bounds = geoLayer.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds, { padding: [80, 80] });
        }

        setResult(`<h4> Vehicle Positions at Time</h4>
            <div style="font-size: 0.9rem;">
                <p><b>Timestamp:</b> ${timestamp}</p>
                <p><b>Vehicles found:</b> ${data.features ? data.features.length : 0}</p>
                <div style="margin-top: 8px; padding: 8px; background: #f0f0f0; border-left: 3px solid #3498db;">
                    <p style="margin: 0; font-size: 0.85rem; color: #666;">Each circle shows where a vehicle was at this exact moment. Click circles for details.</p>
                </div>
            </div>`);
    } catch (err) {
        setResult(`<span style="color: #e74c3c;">Error: ${err.message}</span>`);
    } finally {
        showSpinner(false);
    }
}

async function loadMobilityWindow() {
    const minLon = parseFloat(document.getElementById('minLon')?.value);
    const minLat = parseFloat(document.getElementById('minLat')?.value);
    const maxLon = parseFloat(document.getElementById('maxLon')?.value);
    const maxLat = parseFloat(document.getElementById('maxLat')?.value);

    if (isNaN(minLon) || isNaN(minLat) || isNaN(maxLon) || isNaN(maxLat)) {
        return setResult(' Enter valid numeric bounding box values or click "Use Current Map Window"');
    }

    if (minLon >= maxLon || minLat >= maxLat) {
        return setResult(' Invalid bounds: min must be less than max');
    }

    showSpinner(true);
    try {
        layers.results.clearLayers();

        const res = await fetch(
            `${API_BASE_URL}/mobility/in-window?min_lon=${minLon}&min_lat=${minLat}&max_lon=${maxLon}&max_lat=${maxLat}`
        );
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || 'Failed to load trajectories');
        }

        const data = await res.json();
        const vehicleCount = data.features ? data.features.length : 0;

        // Draw selection window
        const windowBounds = [[parseFloat(minLat), parseFloat(minLon)], [parseFloat(maxLat), parseFloat(maxLon)]];
        L.rectangle(windowBounds, {
            color: '#2c3e50',
            weight: 3,
            fill: true,
            fillColor: '#3498db',
            fillOpacity: 0.15,
            dashArray: '5, 5'
        }).addTo(layers.results);

        // Draw trajectories with colors by vehicle
        const vehicleStats = {};
        const geoLayer = L.geoJSON(data, {
            style: function(feature) {
                const vehicleId = feature.properties?.vehicle_id || 'UNKNOWN';
                               if (!vehicleStats[vehicleId]) {
                    vehicleStats[vehicleId] = { route: feature.properties?.route_id || 'N/A' };
                }
                return {
                    color: getVehicleColor(vehicleId),
                    weight: 5,
                    opacity: 0.85,
                    lineCap: 'round',
                    lineJoin: 'round'
                };
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                const popup = `
                    <div style="font-family: monospace; font-size: 12px;">
                        <b style="color: ${getVehicleColor(props.vehicle_id)}">${props.vehicle_id}</b><br>
                        <i>Route:</i> <b>${props.route_id || 'N/A'}</b><br>
                        <i>In window:</i> Yes
                    </div>
                `;
                layer.bindPopup(popup);
            }
        }).addTo(layers.results);

        if (data.features && data.features.length > 0) {
            const bounds = geoLayer.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds, { padding: [50, 50] });
        }

        let vehicleLegend = '';
        Object.entries(vehicleStats).forEach(([vid, info]) => {
            vehicleLegend += `<div style="margin: 4px 0;"><span style="color: ${getVehicleColor(vid)}; font-weight: bold;">███</span> ${vid} (${info.route})</div>`;
        });

        const area = (parseFloat(maxLon) - parseFloat(minLon)) * (parseFloat(maxLat) - parseFloat(minLat));

        setResult(`<h4>Spatial Window Query</h4>
            <div style="font-size: 0.9rem;">
                <p><b>Bounds:</b> Lon [${minLon.toFixed(3)} → ${maxLon.toFixed(3)}], Lat [${minLat.toFixed(3)} → ${maxLat.toFixed(3)}]</p>
                <p><b>Area:</b> ~${area.toFixed(6)}° (shaded on map)</p>
                <p><b>Trajectories Found:</b> <span style="font-weight: bold; font-size: 1.1em; color: #2980b9;">${vehicleCount}</span></p>
                ${vehicleLegend ? `<div style="margin-top: 8px; padding: 8px; background: #ecf0f1; border-radius: 4px;">${vehicleLegend}</div>` : '<p style="color: #666;">No vehicles in this window.</p>'}
                <p style="font-size: 0.85rem; color: #666; margin-top: 8px;"><i>Select an area to view vehicle trajectories passing through it.</i></p>
            </div>`);
    } catch (err) {
        setResult(`<span style="color: #e74c3c;"> Error: ${err.message}</span>`);
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