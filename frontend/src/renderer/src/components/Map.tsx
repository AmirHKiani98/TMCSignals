import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import react from 'react'
import { Map as LeafletMap } from 'leaflet'
import {TitleOverlay, Sig} from './TitleOverlay'

import { CircularProgress } from '@mui/material';



export default function Map() {
    const [sigs, setSigs] = react.useState<Sig[]>([]);
    const [mapInst, setMapInst] = react.useState<LeafletMap | null>(null);
    const [selectedSig, setSelectedSig] = react.useState<Sig | null>(null);
    const [loading, setLoading] = react.useState<boolean>(false)
    const [fileSearchResults, setFileSearchResults] = react.useState<Record<string, string[]>>({});

    react.useEffect(() => {
        fetch('http://localhost:8811/api/get_intersections/')
            .then(response => response.json())
            .then(data => {
                console.log(data);
                const items: Sig[] = Array.isArray(data.data) ? data.data : [];
                // filter those ones that have lattitude and longitude defined
                const filtered = items.filter((it: any) => it.Latitude != null && it.Longitude != null && !isNaN(Number(it.Latitude)) && !isNaN(Number(it.Longitude)));
                setSigs(filtered)
            })
            .catch(error => {
                console.error('Error fetching intersections:', error);
                setSigs([]);
            });
    }, []);

    const handleSelect = (sig: Sig) => {
        setSelectedSig(sig);
        console.log('Selected sig:', sig);
        if (!mapInst) return; // effect will handle once mapInst ready
        const Latitutde = Number(sig.Latitude);
        const lng = Number(sig.Longitude);
        if (Number.isFinite(Latitutde) && Number.isFinite(lng)) {
            const currentZoom = 15;
            mapInst.flyTo([Latitutde, lng], Math.max(currentZoom, 15), { duration: 1.0 });
        } else {
            console.warn('Invalid coordinates for sig', sig);
        }
    };

    const handleMarkerClick = (e: any, signalId: string | null) => {
        console.log('Marker clicked for signalId:', e);
        setLoading(true);
        fetch('http://localhost:8811/api/find_file_live/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            sig_id: signalId || '',
        }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Files found for sigId', signalId, ':', data);
            setFileSearchResults(data.data)
            setLoading(false);
        })
        .catch(error => {
            console.error('Error fetching found files:', error);
            setFileSearchResults({});
            setLoading(false);
        });
    }

    // If user selected before map ready, run once both available
    react.useEffect(() => {
        console.log('Effect triggered: mapInst or selectedSig changed', { mapInst, selectedSig });
        if (mapInst && selectedSig) {
            const Latitutde = Number(selectedSig.Latitutde);
            const lng = Number(selectedSig.Longitude);
            
            if (Number.isFinite(Latitutde) && Number.isFinite(lng)) {
                const currentZoom = mapInst.getZoom?.() ?? 13;
                mapInst.flyTo([Latitutde, lng], Math.max(currentZoom, 15), { duration: 1.0 });
            }
        }
    }, [mapInst, selectedSig]);


    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <TitleOverlay sigs={sigs} onSelect={handleSelect} />
            <MapContainer
                center={[45.0042759530404, -93.4120200643662]}
                zoom={13}
                style={{ height: '100vh', width: '100%' }}
            >
                <MapInstanceGrabber onMap={setMapInst} />
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                { sigs.filter(sig => {
                    const lat = Number(sig["Latitude"]);
                    const lng = Number(sig["Longitude"]);
                    return Number.isFinite(lat) && Number.isFinite(lng);
                }).map((sig, index) => {
                    const sigId = String(sig["Signal ID"]);
                    return (
                        <Marker
                            key={index}
                            position={[sig["Latitude"], sig["Longitude"]]}
                            eventHandlers={{
                                click: (e) => {
                                    handleMarkerClick(e, sigId);
                                }
                            }}
                        >
                            <Popup>
                                <div>
                                    <strong>{sig["Intersection Name"]}</strong>
                                    {loading ? (
                                        <CircularProgress />
                                    ) : (
                                        <div>
                                            <strong>Signal timing files</strong>
                                            <ul>
                                                {fileSearchResults && Array.isArray(fileSearchResults["signal_timing"]) && fileSearchResults["signal_timing"].length > 0 ? (
                                                    fileSearchResults["signal_timing"].map((filePath, idx) => (
                                                        <li key={idx}>{filePath}</li>
                                                    ))
                                                ) : (
                                                    <li>No signal timing files found.</li>
                                                )}
                                                {fileSearchResults && Array.isArray(fileSearchResults["fya"]) && fileSearchResults["fya"].length > 0 ? (
                                                    <>
                                                        <strong>FYA files</strong>
                                                        {fileSearchResults["fya"].map((filePath, idx) => (
                                                            <li key={idx}>{filePath}</li>
                                                        ))}
                                                    </>
                                                ) : (
                                                    <li>No FYA files found.</li>
                                                )}
                                                {fileSearchResults && Array.isArray(fileSearchResults["front_page_sheets"]) && fileSearchResults["front_page_sheets"].length > 0 ? (
                                                    <>
                                                        <strong>Front page sheets</strong>
                                                        {fileSearchResults["front_page_sheets"].map((filePath, idx) => (
                                                            <li key={idx}>{filePath}</li>
                                                        ))}
                                                    </>
                                                ) : (
                                                    <li>No front page sheets found.</li>
                                                )}

                                            </ul>
                                        </div>
                                    )}

                                </div>
                            </Popup>
                        </Marker>
                    );
                }) }
            </MapContainer>
        </div>
    );
}

// Separate component to reliably obtain map instance once available
function MapInstanceGrabber({ onMap }: { onMap: (map: LeafletMap) => void }) {
    const map = useMap();
    react.useEffect(() => {
        if (map) onMap(map);
    }, [map, onMap]);
    return null;
}