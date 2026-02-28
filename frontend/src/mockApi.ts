// Mock API interceptor for GitHub Pages static deployment
export const isMockMode = import.meta.env.VITE_MOCK_MODE === 'true';

let globalConnectedState = false;

const getMockInstruments = () => [
  { id: 'vna', name: 'Keysight_ENA', address: 'TCPIP0::192.168.1.100::inst0::INSTR', connected: globalConnectedState, driver_class: 'ENA' },
  { id: 'vsg', name: 'MXG_SigGen', address: 'TCPIP0::192.168.1.101::inst0::INSTR', connected: globalConnectedState, driver_class: 'KeysightMXG' },
  { id: 'channel_emulator', name: 'Spirent_Vertex', address: 'TCPIP0::192.168.1.102::inst0::INSTR', connected: globalConnectedState, driver_class: 'Vertex' },
  { id: 'integrated_tester', name: 'CMW500_Tester', address: 'TCPIP0::192.168.1.103::inst0::INSTR', connected: globalConnectedState, driver_class: 'CMW500' },
  { id: 'spectrum_analyzer', name: 'RS_FSW', address: 'TCPIP0::192.168.1.104::inst0::INSTR', connected: globalConnectedState, driver_class: 'FSW' }
];

export const mockFetch = async (url: string, options?: any) => {
  console.log(`[Mock API] Intercepted: ${url}`);
  
  if (url.includes('/api/v1/instruments/status')) {
    return { ok: true, json: async () => getMockInstruments() };
  }
  
  if (url.includes('/api/v1/instruments/connect')) {
    globalConnectedState = true;
    return { ok: true, json: async () => ({ message: "Success (Mock)" }) };
  }
  
  if (url.includes('/api/v1/instruments/disconnect')) {
    globalConnectedState = false;
    return { ok: true, json: async () => ({ message: "Disconnected (Mock)" }) };
  }
  
  if (url.includes('/api/v1/scpi/execute')) {
    const body = JSON.parse(options.body);
    const cmd = body.command.toUpperCase();
    let res = "SIM_DATA";
    if (cmd.includes('*IDN?')) {
        // Return different IDN based on the selected instrument for better realism
        const instId = body.instrument_id || "Unknown";
        res = `Simulated Vendor, ${instId.toUpperCase()}, 000000, v1.0 (Web Mock)`;
    }
    else if (cmd.includes('SYST:ERR?')) res = '0,"No error"';
    else if (!cmd.includes('?')) res = "OK";
    
    return { ok: true, json: async () => ({ response: res, command: body.command }) };
  }
  
  if (url.includes('/api/v1/scpi/batch')) {
    const body = JSON.parse(options.body);
    const results = body.commands.map((cmd: string) => {
      const isQuery = cmd.includes('?');
      let res = "OK";
      if (isQuery) {
        if (cmd.toUpperCase().includes('*IDN?')) {
            const instId = body.instrument_id || "Instrument";
            res = `Simulated Vendor, ${instId.toUpperCase()}, 000000, v1.0`;
        }
        else res = "SIM_DATA";
      }
      return { command: cmd, type: isQuery ? 'query' : 'write', status: 'success', response: isQuery ? res : null };
    });
    return { ok: true, json: async () => ({ results }) };
  }

  throw new Error(`Mock API route not implemented: ${url}`);
};

export const universalFetch = async (url: string, options?: any) => {
  if (isMockMode) {
    // Add artificial delay to make it feel like a real network request
    await new Promise(r => setTimeout(r, 300));
    return mockFetch(url, options);
  }
  return fetch(url, options);
};
