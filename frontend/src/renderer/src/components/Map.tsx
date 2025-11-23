import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import react from 'react'
import { Map as LeafletMap } from 'leaflet'
import {Autocomplete, TextField} from '@mui/material';

interface Sig {
    Name: string;
    lat: number;
    long: number;
    [key: string]: any; // allow additional properties
}

function TitleOverlay({ sigs, onSelect }: { sigs: Sig[]; onSelect: (sig: Sig) => void }) {
    return (
        <div style={{
            position: 'absolute',
            top: '40px',
            left: '40px',
            zIndex: 1000,
            padding: '8px',
            borderRadius: '6px',
            width: '384px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            background: 'rgba(255,255,255,0.95)',
            pointerEvents: 'auto'
        }}>
            <Autocomplete
                disablePortal
                options={sigs}
                getOptionLabel={(o) => o.Name}
                sx={{ width: 360 }}
                onChange={(_, value) => value && onSelect(value)}
                renderInput={(params) => <TextField {...params} size="small" label="Search signals" />}
            />
            <div style={{ fontSize: '12px', color: '#555' }}>
                Showing {sigs.length} signal points. Select one to fly to location.
            </div>
        </div>
    );
}

export default function Map() {
    const [sigs, setSigs] = react.useState<Sig[]>([]);
    const [mapInst, setMapInst] = react.useState<LeafletMap | null>(null);
    const [selectedSig, setSelectedSig] = react.useState<Sig | null>(null);

    const [fileSearchResults, setFileSearchResults] = react.useState<Record<string, string[]>>({});
    
    const findFiles = (sigId: string, lookingText: string) => {
        fetch('http://localhost:8811/api/find_file/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                sig_id: sigId,
                looking_text: lookingText,
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Files found for sigId', sigId, ':', data);
            if (data.found_files) {
                setFileSearchResults(prev => ({ ...prev, [sigId]: data.found_files }));
            } else {
                setFileSearchResults(prev => ({ ...prev, [sigId]: [] }));
            }
        })
        .catch(error => {
            console.error('Error fetching found files:', error);
            setFileSearchResults(prev => ({ ...prev, [sigId]: [] }));
        });
    };

    react.useEffect(() => {
        fetch('http://localhost:8811/api/get_intersections/')
            .then(response => response.json())
            .then(data => {
                const items: Sig[] = Array.isArray(data.data) ? data.data : [];
                const filtered = items.filter((it: any) => typeof it?.Name === 'string' && /sig/i.test(it.Name));
                setSigs(filtered);
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
        const lat = Number(sig.lat);
        const lng = Number(sig.long);
        if (Number.isFinite(lat) && Number.isFinite(lng)) {
            const currentZoom = mapInst.getZoom?.() ?? 13;
            mapInst.flyTo([lat, lng], Math.max(currentZoom, 15), { duration: 1.0 });
        } else {
            console.warn('Invalid coordinates for sig', sig);
        }
    };

    const getSignalIdFromName = (name: string): string | null => {
        // break signal name into parts based on space
        const parts = name.split(' ');
        if (parts.length < 2) return null;
        return parts[parts.length - 1]; // assume last part is the ID
    };
    const handleMarkerClick = (e: any, signalId: string | null) => {
        const marker = e.target;
        const position = marker.getLatLng();
        console.log('Marker clicked at position:', position, 'with signal ID:', signalId);
    }

    // If user selected before map ready, run once both available
    react.useEffect(() => {
        console.log('Effect triggered: mapInst or selectedSig changed', { mapInst, selectedSig });
        if (mapInst && selectedSig) {
            const lat = Number(selectedSig.lat);
            const lng = Number(selectedSig.long);
            
            if (Number.isFinite(lat) && Number.isFinite(lng)) {
                const currentZoom = mapInst.getZoom?.() ?? 13;
                mapInst.flyTo([lat, lng], Math.max(currentZoom, 15), { duration: 1.0 });
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
                {sigs.map((sig, index) => {
                    const sigId = getSignalIdFromName(sig.Name);
                    const foundFilesForSig = sigId ? (fileSearchResults[sigId] || []) : [];
                    return (
                        <Marker key={index} position={[sig.lat, sig.long]} eventHandlers={{
                            click: (e)=>{
                                handleMarkerClick(e, sigId);
                            }
                        }}>
                            <Popup>
                                <div className='w-[400px]'>
                                    <strong>{sig.Name}</strong>
                                    <Autocomplete
                                            disablePortal
                                            options={foundFilesForSig}
                                            getOptionLabel={(o) => o}
                                            // sx={{ width: 360 }}
                                            className='w-[300px] mt-2'
                                            onInputChange={(_, value) => {
                                                if (value && value.length >= 2) {
                                                    findFiles(sigId || '', value);
                                                }
                                            }}
                                            onChange={(_, selectedFile) => {
                                                if (selectedFile) {
                                                    window.api.openFile(selectedFile).then((error) => {
                                                        if (error) {
                                                            console.error('Failed to open file:', error);
                                                        } else {
                                                            console.log('File opened successfully:', selectedFile);
                                                        }
                                                    });
                                                }
                                            }}
                                            renderInput={(params) => <TextField {...params} size="small" label="Search files" />}
                                        />
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