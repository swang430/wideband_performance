// Mock API interceptor for GitHub Pages static deployment
export const isMockMode = import.meta.env.VITE_MOCK_MODE === 'true';

let globalConnectedState = false;

const getMockInstruments = () => [
  { id: 'vna', name: 'Keysight_ENA', address: 'TCPIP0::192.168.1.100::inst0::INSTR', connected: globalConnectedState, driver_class: 'ENA' },
  { id: 'vna2', name: 'Keysight_PNA', address: 'TCPIP0::192.168.1.105::inst0::INSTR', connected: globalConnectedState, driver_class: 'PNA' },
  { id: 'vna3', name: 'RS_ZNA', address: 'TCPIP0::192.168.1.106::inst0::INSTR', connected: globalConnectedState, driver_class: 'ZNA' },
  { id: 'vsg', name: 'MXG_SigGen', address: 'TCPIP0::192.168.1.101::inst0::INSTR', connected: globalConnectedState, driver_class: 'KeysightMXG' },
  { id: 'channel_emulator', name: 'Spirent_Vertex', address: 'TCPIP0::192.168.1.102::inst0::INSTR', connected: globalConnectedState, driver_class: 'Vertex' },
  { id: 'channel_emulator2', name: 'Keysight_PROPSIM', address: 'TCPIP0::192.168.1.107::inst0::INSTR', connected: globalConnectedState, driver_class: 'Propsim' },
  { id: 'integrated_tester', name: 'CMW500_Tester', address: 'TCPIP0::192.168.1.103::inst0::INSTR', connected: globalConnectedState, driver_class: 'CMW500' },
  { id: 'integrated_tester2', name: 'Anritsu_MT8000A', address: 'TCPIP0::192.168.1.108::inst0::INSTR', connected: globalConnectedState, driver_class: 'MT8000A' },
  { id: 'spectrum_analyzer', name: 'RS_FSW', address: 'TCPIP0::192.168.1.104::inst0::INSTR', connected: globalConnectedState, driver_class: 'FSW' },
  { id: 'spectrum_analyzer2', name: 'Keysight_VSA', address: 'TCPIP0::192.168.1.109::inst0::INSTR', connected: globalConnectedState, driver_class: 'KeysightVSA' }
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
  
  if (url.includes('/api/v1/instruments/probe')) {
    const body = options.body ? JSON.parse(options.body) : {};
    const results = [
      { address: 'TCPIP0::192.168.1.100::inst0::INSTR', idn: 'Simulated Keysight, E5071C', status: 'success', configured_as: 'vna' },
      { address: 'TCPIP0::192.168.1.101::inst0::INSTR', idn: 'Simulated Keysight, N5182B', status: 'success', configured_as: 'vsg' },
      { address: 'TCPIP0::192.168.1.102::inst0::INSTR', idn: 'Simulated Spirent, Vertex', status: 'success', configured_as: 'channel_emulator' },
      { address: 'TCPIP0::192.168.1.254::inst0::INSTR', idn: 'Unknown Device (Not Configured)', status: 'success', configured_as: null }
    ];
    if (body.manual_address) {
      results.push({ address: body.manual_address, idn: 'Manual Probe Success (Mock)', status: 'success', configured_as: null });
    }
    return { ok: true, json: async () => results };
  }
  
  if (url.includes('/api/v1/config/instruments')) {
    return { ok: true, json: async () => ({ message: "Config updated successfully (Mock)" }) };
  }
  
  if (url.match(/\/api\/v1\/instruments\/[^\/]+\/methods$/)) {
    const methods = [
      { name: 'connect', signature: '()', doc: '连接到仪器' },
      { name: 'disconnect', signature: '()', doc: '断开与仪器的连接' },
      { name: 'reset', signature: '()', doc: '重置仪器' },
      { name: 'set_frequency', signature: '(freq_hz: float)', doc: '设置中心频率 (Hz)' },
      { name: 'check_system_errors', signature: '() -> list[str]', doc: '检查系统错误队列' }
    ];
    return { ok: true, json: async () => ({ instrument_id: 'mock_inst', methods }) };
  }
  
  if (url.match(/\/api\/v1\/instruments\/[^\/]+\/methods\/execute$/)) {
    const body = JSON.parse(options.body);
    return { ok: true, json: async () => ({ status: 'success', result: `Mock execution of ${body.method_name}`, system_errors: [] }) };
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
