import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Paper,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import BoltIcon from '@mui/icons-material/Bolt';
import LinkIcon from '@mui/icons-material/Link';
import LinkOffIcon from '@mui/icons-material/LinkOff';
import SearchIcon from '@mui/icons-material/Search';
import CodeIcon from '@mui/icons-material/Code';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { universalFetch } from '../mockApi';

interface Instrument {
  id: string;
  name: string;
  address: string;
  connected: boolean;
  driver_class: string;
}

interface DriverMethod {
  name: string;
  signature: string;
  doc: string;
}

export default function Playground() {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [selectedInst, setSelectedInst] = useState<string>('');
  const [singleCmd, setSingleCmd] = useState<string>('*IDN?');
  const [singleResponse, setSingleResponse] = useState<string>('');
  const [batchCmds, setBatchCmds] = useState<string>('*IDN?\n*OPT?\nSYST:ERR?');
  const [batchResults, setBatchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Probe states
  const [probeOpen, setProbeOpen] = useState(false);
  const [probeResults, setProbeResults] = useState<any[]>([]);
  const [manualProbeAddr, setManualProbeAddr] = useState<string>('');
  const [probing, setProbing] = useState(false);

  // Driver Verification states
  const [driverMethods, setDriverMethods] = useState<DriverMethod[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [methodArgs, setMethodArgs] = useState<string>('{}');
  const [methodResult, setMethodResult] = useState<any>(null);

  const api = (path: string) => import.meta.env.DEV ? `http://localhost:8000${path}` : path;

  const fetchStatus = async () => {
    try {
      const res = await universalFetch(api('/api/v1/instruments/status'));
      const data = await res.json();
      setInstruments(data);
      if (data.length > 0 && !selectedInst) setSelectedInst(data[0].id);
    } catch (e) {
      // ignore
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedInst) {
      // Fetch available methods when an instrument is selected
      const fetchMethods = async () => {
        try {
          const res = await universalFetch(api(`/api/v1/instruments/${selectedInst}/methods`));
          const data = await res.json();
          setDriverMethods(data.methods || []);
          setSelectedMethod('');
          setMethodResult(null);
        } catch (e) {
          console.error(e);
          setDriverMethods([]);
        }
      };
      fetchMethods();
    }
  }, [selectedInst]);

  const handleConnect = async (simulation: boolean) => {
    setLoading(true);
    try {
      await universalFetch(api(`/api/v1/instruments/connect?simulation_mode=${simulation}`), { method: 'POST' });
      await fetchStatus();
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setLoading(true);
    try {
      await universalFetch(api('/api/v1/instruments/disconnect'), { method: 'POST' });
      await fetchStatus();
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleProbe = async () => {
    setProbing(true);
    setProbeResults([]);
    try {
      const res = await universalFetch(api('/api/v1/instruments/probe'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manual_address: manualProbeAddr || null })
      });
      const data = await res.json();
      setProbeResults(data || []);
      if (data && data.length > 0) {
        setSuccessMsg(`Probe completed: Found ${data.length} device(s).`);
      } else {
        setSuccessMsg(`Probe completed: No VISA devices found on the network.`);
      }
    } catch (e: any) {
      setError(`Probe Error: ${e?.message ?? String(e)}`);
    } finally {
      setProbing(false);
    }
  };

  const handleSingleScpi = async () => {
    if (!selectedInst) return;
    setLoading(true);
    setSingleResponse('');
    try {
      const res = await universalFetch(api('/api/v1/scpi/execute'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instrument_id: selectedInst, command: singleCmd, is_query: singleCmd.includes('?') }),
      });
      const data = await res.json();
      setSingleResponse(data.error ? `ERROR: ${data.error}` : data.response || 'OK');
    } catch (e: any) {
      setSingleResponse(`Fetch Error: ${e?.message ?? String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchScpi = async () => {
    if (!selectedInst) return;
    setLoading(true);
    setBatchResults([]);
    try {
      const cmds = batchCmds
        .split('\n')
        .map((c) => c.trim())
        .filter((c) => c.length > 0);

      const res = await universalFetch(api('/api/v1/scpi/batch'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instrument_id: selectedInst, commands: cmds }),
      });
      const data = await res.json();
      setBatchResults(data.results || []);
    } catch (e: any) {
      setError(`Batch Error: ${e?.message ?? String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteMethod = async () => {
    if (!selectedInst || !selectedMethod) return;
    setLoading(true);
    setMethodResult(null);
    try {
      let kwargs = {};
      try {
        kwargs = JSON.parse(methodArgs);
      } catch (err) {
        throw new Error("Invalid JSON arguments format");
      }

      const res = await universalFetch(api(`/api/v1/instruments/${selectedInst}/methods/execute`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method_name: selectedMethod, kwargs }),
      });
      const data = await res.json();
      setMethodResult(data);
    } catch (e: any) {
      setMethodResult({ status: 'error', error: e?.message ?? String(e), system_errors: [], traceback: '' });
    } finally {
      setLoading(false);
    }
  };

  const handleSyncToConfig = async () => {
    if (!probeResults || probeResults.length === 0) return;
    
    // Auto-map found devices to default roles based on IDN heuristic
    const mappedInstruments = probeResults.filter(r => r.status === 'success').map((r, i) => {
      let role = r.configured_as || `instrument_${i}`;
      let dclass = 'BaseInstrument';
      
      const idn = r.idn.toUpperCase();
      if (idn.includes('CMW')) { role = 'integrated_tester'; dclass = 'CMW500'; }
      else if (idn.includes('FSW')) { role = 'spectrum_analyzer'; dclass = 'FSW'; }
      else if (idn.includes('MXG') || idn.includes('N5182B')) { role = 'vsg'; dclass = 'KeysightMXG'; }
      else if (idn.includes('SMW')) { role = 'vsg'; dclass = 'SMW200A'; }
      else if (idn.includes('ENA') || idn.includes('E5071C')) { role = 'vna'; dclass = 'ENA'; }
      else if (idn.includes('VERTEX')) { role = 'channel_emulator'; dclass = 'Vertex'; }
      
      return {
        id: role,
        address: r.address,
        driver_class: dclass,
        name: `${dclass}_${i}`
      };
    });

    try {
      const res = await universalFetch(api('/api/v1/config/instruments'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruments: mappedInstruments })
      });
      if (res.ok) {
        setSuccessMsg("Synced successfully to config.yaml!");
        fetchStatus();
      } else {
        const errData = await res.json();
        setError(`Sync Failed: ${errData.detail || 'Unknown error'}`);
      }
    } catch (e: any) {
      setError(`Sync Error: ${e?.message ?? String(e)}`);
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3} flexWrap="wrap" gap={2}>
        <Typography variant="h4" fontWeight="bold">
          SCPI Playground & Validation
        </Typography>
        <Box gap={2} display="flex">
          <Button
            variant="outlined"
            color="info"
            startIcon={<SearchIcon />}
            onClick={() => setProbeOpen(true)}
            disabled={loading}
          >
            Probe
          </Button>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<LinkIcon />}
            onClick={() => handleConnect(true)}
            disabled={loading}
          >
            Connect (Sim)
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<LinkOffIcon />}
            onClick={handleDisconnect}
            disabled={loading}
          >
            Disconnect All
          </Button>
        </Box>
      </Box>

      <Box
        sx={{
          display: 'flex',
          gap: 3,
          flexDirection: { xs: 'column', md: 'row' },
          alignItems: 'stretch',
        }}
      >
        {/* Instruments */}
        <Paper sx={{ p: 2, width: { xs: '100%', md: 360 }, flexShrink: 0 }}>
          <Typography variant="h6" mb={2}>
            Instruments
          </Typography>
          {instruments.map((inst) => (
            <Box
              key={inst.id}
              onClick={() => setSelectedInst(inst.id)}
              sx={{
                p: 1.5,
                mb: 1,
                borderRadius: 1,
                cursor: 'pointer',
                border: '1px solid',
                borderColor: selectedInst === inst.id ? 'primary.main' : 'divider',
                bgcolor: selectedInst === inst.id ? 'primary.light' : 'background.paper',
                color: selectedInst === inst.id ? 'primary.contrastText' : 'text.primary',
              }}
            >
              <Typography variant="subtitle1">{inst.name}</Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                {inst.address}
              </Typography>
              <Box mt={1}>
                <Chip
                  size="small"
                  label={inst.connected ? 'Connected' : 'Offline'}
                  color={inst.connected ? 'success' : 'default'}
                />
                <Chip size="small" label={inst.driver_class} sx={{ ml: 1 }} />
              </Box>
            </Box>
          ))}
          {instruments.length === 0 && (
            <Typography variant="body2" color="textSecondary">
              No instruments found (or not connected yet).
            </Typography>
          )}
        </Paper>

        {/* Main */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" mb={2}>
              Single SCPI Execution
            </Typography>
            <Box display="flex" gap={2}>
              <TextField
                fullWidth
                label="SCPI Command"
                variant="outlined"
                value={singleCmd}
                onChange={(e) => setSingleCmd(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSingleScpi();
                }}
              />
              <Button
                variant="contained"
                endIcon={<PlayArrowIcon />}
                onClick={handleSingleScpi}
                disabled={!selectedInst || loading}
              >
                Send
              </Button>
            </Box>
            {singleResponse && (
              <Box mt={2} p={2} bgcolor="grey.900" color="success.main" borderRadius={1} fontFamily="monospace">
                {singleResponse}
              </Box>
            )}
          </Paper>

          {/* Driver Verification */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" mb={2}>
              Driver API Verification
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={2}>
              Test high-level Python driver methods directly. Exceptions and system errors are captured for driver debugging.
            </Typography>
            <Box display="flex" gap={2} mb={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Select Driver Method</InputLabel>
                <Select
                  value={selectedMethod}
                  label="Select Driver Method"
                  onChange={(e) => setSelectedMethod(e.target.value)}
                  disabled={!selectedInst || driverMethods.length === 0}
                >
                  {driverMethods.map((m) => (
                    <MenuItem key={m.name} value={m.name}>
                      {m.name} {m.signature}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box display="flex" gap={2} mb={2}>
              <TextField
                fullWidth
                label='Arguments (JSON format, e.g. {"freq_hz": 2.4e9})'
                variant="outlined"
                size="small"
                value={methodArgs}
                onChange={(e) => setMethodArgs(e.target.value)}
                disabled={!selectedMethod}
                sx={{ fontFamily: 'monospace' }}
              />
              <Button
                variant="contained"
                color="primary"
                startIcon={<CodeIcon />}
                onClick={handleExecuteMethod}
                disabled={!selectedMethod || loading}
                sx={{ whiteSpace: 'nowrap' }}
              >
                Execute Method
              </Button>
            </Box>

            {methodResult && (
              <Box mt={2}>
                <Alert severity={methodResult.status === 'success' ? 'success' : 'error'} sx={{ mb: 1 }}>
                  Status: {methodResult.status.toUpperCase()}
                  {methodResult.error && ` - ${methodResult.error}`}
                </Alert>
                
                {methodResult.result !== undefined && methodResult.result !== null && (
                  <Box p={2} bgcolor="grey.900" color="success.main" borderRadius={1} fontFamily="monospace" mb={1} overflow="auto">
                    {typeof methodResult.result === 'object' ? JSON.stringify(methodResult.result, null, 2) : String(methodResult.result)}
                  </Box>
                )}

                {(methodResult.system_errors?.length > 0 || methodResult.traceback) && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography color="error.main">View Debug Details (Traceback & Hardware Errors)</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      {methodResult.system_errors?.length > 0 && (
                        <Box mb={2}>
                          <Typography variant="subtitle2" color="error">Hardware System Errors (SYST:ERR?):</Typography>
                          <Box p={1} bgcolor="#2b0000" color="#ffb3b3" borderRadius={1} fontFamily="monospace" fontSize="0.85rem">
                            {methodResult.system_errors.map((e: string, i: number) => <div key={i}>{e}</div>)}
                          </Box>
                        </Box>
                      )}
                      {methodResult.traceback && (
                        <Box>
                          <Typography variant="subtitle2" color="error">Python Traceback:</Typography>
                          <Box p={1} bgcolor="#2b0000" color="#ffb3b3" borderRadius={1} fontFamily="monospace" fontSize="0.85rem" whiteSpace="pre-wrap">
                            {methodResult.traceback}
                          </Box>
                        </Box>
                      )}
                    </AccordionDetails>
                  </Accordion>
                )}
              </Box>
            )}
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" mb={2}>
              Batch Interoperability Test
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={2}>
              Paste multiple SCPI commands (one per line). Lines starting with # are ignored by the backend.
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={6}
              variant="outlined"
              value={batchCmds}
              onChange={(e) => setBatchCmds(e.target.value)}
              sx={{ mb: 2, fontFamily: 'monospace' }}
            />
            <Button
              variant="contained"
              color="secondary"
              startIcon={<BoltIcon />}
              onClick={handleBatchScpi}
              disabled={!selectedInst || loading}
            >
              Run Batch Test
            </Button>

            {batchResults.length > 0 && (
              <TableContainer component={Box} sx={{ mt: 3, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'action.hover' }}>
                      <TableCell width="40%">Command</TableCell>
                      <TableCell width="10%">Type</TableCell>
                      <TableCell width="10%">Status</TableCell>
                      <TableCell width="40%">Response / Error</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {batchResults.map((r, i) => (
                      <TableRow key={i}>
                        <TableCell sx={{ fontFamily: 'monospace' }}>{r.command}</TableCell>
                        <TableCell>
                          <Chip size="small" label={String(r.type).toUpperCase()} />
                        </TableCell>
                        <TableCell>
                          <Chip size="small" color={r.status === 'success' ? 'success' : 'error'} label={String(r.status).toUpperCase()} />
                        </TableCell>
                        <TableCell
                          sx={{
                            fontFamily: 'monospace',
                            color: r.status === 'error' ? 'error.main' : 'text.secondary',
                          }}
                        >
                          {r.response || r.error || '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Box>
      </Box>

      <Dialog open={probeOpen} onClose={() => setProbeOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Instrument Probe & Discovery</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" mb={2}>
            Scan the local network for available VISA resources (e.g. TCPIP, GPIB). You can also provide a specific IP/address to verify manually.
          </Typography>
          <Box display="flex" gap={2} mb={3}>
            <TextField 
              label="Manual Address (e.g. TCPIP0::192.168.1.100::INSTR)" 
              variant="outlined" 
              size="small"
              fullWidth
              value={manualProbeAddr}
              onChange={(e) => setManualProbeAddr(e.target.value)}
            />
            <Button variant="contained" onClick={handleProbe} disabled={probing}>
              {probing ? 'Probing...' : 'Run Probe'}
            </Button>
          </Box>
          
          {probeResults.length > 0 && (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'action.hover' }}>
                    <TableCell>Address</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>IDN Response</TableCell>
                    <TableCell>Configured As</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {probeResults.map((r, i) => (
                    <TableRow key={i}>
                      <TableCell sx={{ fontFamily: 'monospace' }}>{r.address}</TableCell>
                      <TableCell>
                        <Chip size="small" color={r.status === 'success' ? 'success' : 'error'} label={String(r.status).toUpperCase()} />
                      </TableCell>
                      <TableCell sx={{ fontFamily: 'monospace' }}>{r.idn}</TableCell>
                      <TableCell>
                        {r.configured_as ? <Chip size="small" label={r.configured_as} color="primary" /> : <Typography variant="body2" color="textSecondary">Unconfigured</Typography>}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProbeOpen(false)}>Close</Button>
          <Button variant="contained" color="success" onClick={handleSyncToConfig} disabled={probeResults.length === 0}>
            Sync to config.yaml
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
      <Snackbar open={!!successMsg} autoHideDuration={6000} onClose={() => setSuccessMsg(null)}>
        <Alert severity="success" onClose={() => setSuccessMsg(null)}>
          {successMsg}
        </Alert>
      </Snackbar>
    </Box>
  );
}
