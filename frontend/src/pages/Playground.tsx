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
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import BoltIcon from '@mui/icons-material/Bolt';
import LinkIcon from '@mui/icons-material/Link';
import LinkOffIcon from '@mui/icons-material/LinkOff';

import { universalFetch } from '../mockApi';

interface Instrument {
  id: string;
  name: string;
  address: string;
  connected: boolean;
  driver_class: string;
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

  const api = (path: string) => `http://localhost:8000${path}`;

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

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3} flexWrap="wrap" gap={2}>
        <Typography variant="h4" fontWeight="bold">
          SCPI Playground & Validation
        </Typography>
        <Box gap={2} display="flex">
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

      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}
