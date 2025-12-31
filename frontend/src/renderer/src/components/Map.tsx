import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import react from 'react'
import { Map as LeafletMap } from 'leaflet'
import L from 'leaflet'
import {TitleOverlay, Sig} from './TitleOverlay'

import { CircularProgress } from '@mui/material';

// Create custom icons
const defaultIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const selectedIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

export default function Map() {
    const [sigs, setSigs] = react.useState<Sig[]>([]);
    const [mapInst, setMapInst] = react.useState<LeafletMap | null>(null);
    const [selectedSig, setSelectedSig] = react.useState<Sig | null>(null);
    const [loading, setLoading] = react.useState<boolean>(false)
    const [fileSearchResults, setFileSearchResults] = react.useState<Record<string, string[]>>({});
    const [snapShotImage, setSnapShotImage] = react.useState<string | null>(null);
    const [additionalInfo, setAdditionalInfo] = react.useState<any>({});
    
    react.useEffect(() => {
        fetch('http://localhost:8811/api/get_intersections/')
            .then(response => response.json())
            .then(data => {
                console.log(data);
                const items: Sig[] = Array.isArray(data.data) ? data.data : [];
                // filter those ones that have lattitude and longitude defined
                const filtered = items.filter((it: any) => it.Latitude != null && it.Longitude != null && !isNaN(Number(it.Latitude)) && !isNaN(Number(it.Longitude)));
                console.log(filtered);
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

    const handleMarkerClick = (_: any, sig: Sig, signalId: string | null) => {
        setSelectedSig(sig);
        setLoading(true);
        setFileSearchResults({});
        setAdditionalInfo({});
        const urlAdditionalInfo = `http://localhost:8811/api/get_additional_info/`;
        fetch(urlAdditionalInfo, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ sig_id: signalId })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Additional info data:', signalId, data);
            setAdditionalInfo(data.additional_info);
        })
        .catch(error => {
            console.error('Error fetching additional info:', error);
        });


        const ws = new WebSocket(`ws://localhost:8811/ws/find_file/${signalId}/`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.done){
                ws.close();
                setLoading(false);
                return;
            }
            
            setFileSearchResults(prev => ({
                ...prev,
                [data.type]: [...(prev[data.type] || []), data.file]
            }));
        };
        ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            setLoading(false);
            ws.close();
        }
        // Fetch snapshot image
        fetch(`http://localhost:8811/api/get-snapshot/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ sig_id: signalId })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Snapshot data:', data);
            if (data.snapshot) {
                setSnapShotImage(data.snapshot);
            } else {
                setSnapShotImage(null);
            }
        })
        .catch(error => {
            console.error('Error fetching snapshot:', error);
            setSnapShotImage(null);
        });

    }

    // If user selected before map ready, run once both available
    react.useEffect(() => {
        console.log('Effect triggered: mapInst or selectedSig changed', { mapInst, selectedSig });
        if (mapInst && selectedSig) {
            const Latitutde = Number(selectedSig.Latitude);
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
                {sigs.filter(sig => {
                    const lat = Number(sig["Latitude"]);
                    const lng = Number(sig["Longitude"]);
                    return Number.isFinite(lat) && Number.isFinite(lng);
                }).map((sig, index) => {
                    const sigId = String(sig["Signal ID"]);
                    const isSelected = selectedSig && String(selectedSig["Signal ID"]) === sigId;
                    return (
                        <Marker
                            key={index}
                            position={[sig["Latitude"], sig["Longitude"]]}
                            icon={isSelected ? selectedIcon : defaultIcon}
                            eventHandlers={{
                                click: (e) => {
                                    handleMarkerClick(e, sig, sigId);
                                }
                            }}
                        >
                            <Popup>
                                <div className='flex flex-col justify-center gap-1'>
                                    <strong>{sig["Intersection Name"]}</strong>
                                    <div>
                                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                            <tbody>
                                                {additionalInfo && Object.entries(additionalInfo).map(([key, value], index) => (
                                                    <tr
                                                        key={key}
                                                        style={{
                                                            backgroundColor: index % 2 === 0 ? '#90caf9' : '#ffffff',
                                                            color: index % 2 === 0 ? '#ffffff' : '#000000',
                                                        }}
                                                    >
                                                        <td style={{ padding: '8px', fontWeight: 'bold', textAlign: 'left' }}>
                                                            {key}
                                                        </td>
                                                        <td style={{ padding: '8px', textAlign: 'right' }}>
                                                            {String(value)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        <ul className='p-2.5'>
                                            {fileSearchResults &&
                                                Object.entries(fileSearchResults).map(([key, files]) => (
                                                    <div key={key} className="p-2.5">
                                                        <strong>{key}</strong>
                                                        <ul>
                                                            {files.map((filePath, idx) => (
                                                                <li key={idx}>
                                                                    <a
                                                                        href="#"
                                                                        onClick={e => {
                                                                            e.preventDefault();
                                                                            window.api.openFile(filePath);
                                                                        }}
                                                                        style={{ color: '#1976d2', textDecoration: 'underline', cursor: 'pointer' }}
                                                                    >
                                                                        {filePath.replace(/^L:\\TO_Traffic\\TMC\\/i, '')}
                                                                    </a>
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                ))
                                            }
                                        </ul>
                                        {snapShotImage &&
                                            <div className='p-2.5'>
                                                <strong>Snapshot</strong>
                                                <div>
                                                    <img src={snapShotImage} alt="Snapshot" style={{ maxWidth: '100%' }} />
                                                </div>
                                            </div>
                                        }
                                    </div>
                                    
                                    {loading && (
                                        <div className='w-full text-center'>
                                            <CircularProgress />
                                        </div>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
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