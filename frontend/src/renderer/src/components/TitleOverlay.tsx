import { Autocomplete, TextField } from "@mui/material";

export interface Sig {
    Name: string;
    Latitutde: number;
    Longitude: number;
    [key: string]: any; // allow additional properties
}


export function TitleOverlay({ sigs, onSelect }: { sigs: Sig[]; onSelect: (sig: Sig) => void }) {
    const handleSearch = (inputValue: string) => {
        if (!inputValue) return null;
        
        // Search by Signal ID or Intersection Name
        const found = sigs.find(sig => 
            String(sig["Signal ID"]) === inputValue ||
            sig["Intersection Name"]?.toLowerCase().includes(inputValue.toLowerCase())
        );
        
        return found || null;
    };

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
                getOptionLabel={(o) => {
                    if (typeof o === 'string') return o;
                    return `${o["Signal ID"]} - ${o["Intersection Name"] || ""}`
                }}
                isOptionEqualToValue={(option, value) => 
                    String(option["Signal ID"]) === String(value["Signal ID"])
                }
                sx={{ width: 360 }}
                onChange={(_, value) => value && onSelect(value)}
                filterOptions={(options, state) => {
                    const input = state.inputValue;
                    if (!input) return options;
                    
                    return options.filter(sig =>
                        String(sig["Signal ID"]).includes(input) ||
                        sig["Intersection Name"]?.toLowerCase().includes(input.toLowerCase())
                    );
                }}
                renderInput={(params) => <TextField {...params} size="small" label="Search signals" />}
            />
            <div style={{ fontSize: '12px', color: '#555' }}>
                Showing {sigs.length} signal points. Search by Signal ID or Intersection Name.
            </div>
        </div>
    );
}