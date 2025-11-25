import { Autocomplete, TextField } from "@mui/material";

export interface Sig {
    Name: string;
    Latitutde: number;
    Longitude: number;
    [key: string]: any; // allow additional properties
}


export function TitleOverlay({ sigs, onSelect }: { sigs: Sig[]; onSelect: (sig: Sig) => void }) {
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
                getOptionLabel={(o) =>
                    typeof o === 'string'
                        ? o
                        : (o["Intersection Name"] || o.Name || String(o["Signal ID"]) || "")
                }
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