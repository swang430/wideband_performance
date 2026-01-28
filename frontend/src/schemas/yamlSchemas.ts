const channelModelEnum = [
  '3GPP_HST_SCENARIO.scn',
  'HST_300kmh',
  'HST_Cell1.scn',
  'InH_Office',
  'RMa_LOS',
  'Static_LOS.scn',
  'Tunnel_Entry',
  'Tunnel_Leaky_Coax',
  'UMa_LOS',
  'UMa_NLOS',
  'Urban_Macro.scn',
  'WLAN_Model_B_40MHz'
];

export const configSchema = {
  $schema: 'http://json-schema.org/draft-07/schema#',
  title: 'WideBand Performance config.yaml',
  type: 'object',
  required: ['instruments', 'dut'],
  properties: {
    instruments: {
      type: 'object',
      description: 'Instrument definitions keyed by name used in scenario timeline.target',
      properties: {
        vna: { $ref: '#/$defs/instrument' },
        vsg: { $ref: '#/$defs/instrument' },
        channel_emulator: { $ref: '#/$defs/instrument' },
        integrated_tester: { $ref: '#/$defs/instrument' },
        spectrum_analyzer: { $ref: '#/$defs/instrument' },
        tcu: { $ref: '#/$defs/instrument' },
        power_meter: { $ref: '#/$defs/instrument' },
        emgen: { $ref: '#/$defs/instrument' },
        field_probe: { $ref: '#/$defs/instrument' },
        positioner: { $ref: '#/$defs/instrument' }
      },
      additionalProperties: { $ref: '#/$defs/instrument' }
    },
    dut: {
      type: 'object',
      properties: {
        device_id: { type: ['string', 'null'] },
        wifi_interface: { type: 'string' }
      },
      additionalProperties: true
    },
    test_cases: {
      type: 'array',
      items: { $ref: '#/$defs/testCase' }
    }
  },
  additionalProperties: true,
  $defs: {
    instrument: {
      type: 'object',
      required: ['address'],
      properties: {
        address: { type: 'string' },
        name: { type: 'string' },
        timeout: { type: 'number' },
        reset: { type: 'boolean' },
        slot: { type: ['number', 'string'] },
        port: { type: 'string' },
        type: { type: 'string' },
        driver_hint: { type: 'string' }
      },
      additionalProperties: true
    },
    channelModelName: {
      type: 'string',
      enum: channelModelEnum
    },
    testCase: {
      type: 'object',
      properties: {
        name: { type: 'string' },
        type: { type: 'string' },
        duration: { type: 'number' },
        frequencies: {
          type: 'array',
          items: { type: 'number' }
        },
        channel_model: { $ref: '#/$defs/channelModelName' }
      },
      additionalProperties: true
    }
  }
};

export const scenarioSchema = {
  $schema: 'http://json-schema.org/draft-07/schema#',
  title: 'WideBand Performance scenario',
  type: 'object',
  required: ['metadata', 'config'],
  properties: {
    metadata: {
      type: 'object',
      required: ['id', 'name', 'version'],
      properties: {
        id: { type: 'string' },
        name: { type: 'string' },
        version: { type: 'string' },
        author: { type: 'string' },
        description: { type: 'string' }
      },
      additionalProperties: true
    },
    config: {
      type: 'object',
      required: ['type'],
      properties: {
        type: { enum: ['sensitivity', 'blocking', 'dynamic_scenario'] },
        strategy: { type: 'string' },
        carrier_freq_hz: { type: 'number' },
        bandwidth_mhz: { type: 'number' },
        subcarrier_spacing_khz: { type: 'number' },
        total_duration: { type: 'number', minimum: 0 },
        channel: { $ref: '#/$defs/channel' },
        setup: { type: 'object', additionalProperties: true },
        timeline: {
          type: 'array',
          items: { $ref: '#/$defs/timelineEvent' }
        },
        search: { $ref: '#/$defs/search' },
        main_signal: { $ref: '#/$defs/mainSignal' },
        interferer: { $ref: '#/$defs/interferer' },
        limit: { $ref: '#/$defs/limit' },
        metrics: { $ref: '#/$defs/metrics' },
        limits: { $ref: '#/$defs/limits' },
        instruments: { type: 'object', additionalProperties: true }
      },
      additionalProperties: true,
      allOf: [
        {
          if: { properties: { type: { const: 'sensitivity' } } },
          then: { required: ['search'] }
        },
        {
          if: { properties: { type: { const: 'blocking' } } },
          then: { required: ['main_signal', 'interferer'] }
        },
        {
          if: { properties: { type: { const: 'dynamic_scenario' } } },
          then: { required: ['total_duration', 'timeline'] }
        }
      ]
    }
  },
  additionalProperties: true,
  $defs: {
    channelModelName: {
      type: 'string',
      enum: channelModelEnum
    },
    channel: {
      type: 'object',
      properties: {
        model: { $ref: '#/$defs/channelModelName' },
        velocity_kmh: { type: 'number' }
      },
      additionalProperties: true
    },
    timelineEvent: {
      type: 'object',
      required: ['time', 'target', 'action'],
      properties: {
        time: { type: 'number', minimum: 0 },
        target: {
          enum: [
            'channel_emulator',
            'integrated_tester',
            'vsg',
            'tcu',
            'dut',
            'vna',
            'spectrum_analyzer',
            'power_meter',
            'emgen',
            'signal_generator',
            'field_probe',
            'positioner'
          ]
        },
        action: {
          enum: [
            'load_channel_model',
            'set_velocity',
            'set_distance',
            'set_path_loss',
            'set_fading_profile',
            'rf_on',
            'rf_off',
            'set_tech_standard',
            'start_signaling',
            'stop_signaling',
            'configure_cell',
            'set_frequency',
            'set_power',
            'enable_output',
            'load_waveform',
            'switch_rf_path',
            'set_attenuation',
            'enable_amplifier',
            'get_switch_state',
            'trigger_handover',
            'start_traffic',
            'configure_wlan',
            'set_wlan_indices'
          ]
        },
        params: { type: 'object' },
        comment: { type: 'string' }
      },
      additionalProperties: false,
      allOf: [
        {
          if: { properties: { action: { const: 'load_channel_model' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/loadChannelModelParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'configure_wlan' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/configureWlanParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'set_wlan_indices' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setWlanIndicesParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'set_velocity' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setVelocityParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'set_distance' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setDistanceParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'set_path_loss' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setPathLossParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'set_fading_profile' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setFadingProfileParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'rf_on' } } },
          then: { properties: { params: { maxProperties: 0 } } }
        },
        {
          if: { properties: { action: { const: 'rf_off' } } },
          then: { properties: { params: { maxProperties: 0 } } }
        },
        {
          if: { properties: { action: { const: 'set_tech_standard' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setTechStandardParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'start_signaling' } } },
          then: { properties: { params: { $ref: '#/$defs/startSignalingParams' } } }
        },
        {
          if: { properties: { action: { const: 'stop_signaling' } } },
          then: { properties: { params: { maxProperties: 0 } } }
        },
        {
          if: { properties: { action: { const: 'configure_cell' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/configureCellParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'set_frequency' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setFrequencyParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'set_power' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setPowerParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'enable_output' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/enableOutputParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'load_waveform' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/loadWaveformParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'switch_rf_path' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/switchRfPathParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'set_attenuation' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/setAttenuationParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'enable_amplifier' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/enableAmplifierParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'get_switch_state' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/getSwitchStateParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'trigger_handover' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/triggerHandoverParams' } }
          }
        },
        {
          if: { properties: { action: { const: 'start_traffic' } } },
          then: {
            required: ['params'],
            properties: { params: { $ref: '#/$defs/startTrafficParams' } }
          }
        }
      ]
    },
    search: {
      type: 'object',
      properties: {
        start_power_dbm: { type: 'number' },
        end_power_dbm: { type: 'number' },
        step_db: { type: 'number' },
        target_bler: { type: 'number', minimum: 0, maximum: 1 },
        settling_time_s: { type: 'number', minimum: 0 }
      },
      additionalProperties: true
    },
    mainSignal: {
      type: 'object',
      properties: {
        freq_hz: { type: 'number' },
        power_dbm: { type: 'number' }
      },
      additionalProperties: true
    },
    interferer: {
      type: 'object',
      properties: {
        type: { type: 'string' },
        freq_offsets_mhz: {
          type: 'array',
          items: { type: 'number' }
        },
        start_power_dbm: { type: 'number' },
        end_power_dbm: { type: 'number' },
        step_db: { type: 'number' }
      },
      additionalProperties: true
    },
    limit: {
      type: 'object',
      properties: {
        max_bler: { type: 'number', minimum: 0, maximum: 1 }
      },
      additionalProperties: true
    },
    metrics: {
      type: 'object',
      properties: {
        interval: { type: 'number', minimum: 0 },
        collect: { type: 'array', items: { type: 'string' } },
        targets: { type: 'array', items: { type: 'string' } }
      },
      additionalProperties: true
    },
    limits: {
      type: 'object',
      additionalProperties: { type: 'number' }
    },
    loadChannelModelParams: {
      type: 'object',
      required: ['model'],
      properties: { model: { $ref: '#/$defs/channelModelName' } },
      additionalProperties: false
    },
    setVelocityParams: {
      type: 'object',
      required: ['kmh'],
      properties: { kmh: { type: 'number' } },
      additionalProperties: false
    },
    setDistanceParams: {
      type: 'object',
      required: ['km'],
      properties: { km: { type: 'number' } },
      additionalProperties: false
    },
    setPathLossParams: {
      type: 'object',
      required: ['db'],
      properties: { db: { type: 'number' } },
      additionalProperties: false
    },
    setFadingProfileParams: {
      type: 'object',
      required: ['profile'],
      properties: {
        profile: { type: 'string' },
        duration_ms: { type: 'number', minimum: 0 }
      },
      additionalProperties: false
    },
    setTechStandardParams: {
      type: 'object',
      required: ['standard'],
      properties: { standard: { type: 'string' } },
      additionalProperties: false
    },
    startSignalingParams: {
      type: 'object',
      properties: { tech: { type: 'string' } },
      additionalProperties: false
    },
    configureCellParams: {
      type: 'object',
      required: ['freq_hz', 'bandwidth_mhz', 'power_dbm'],
      properties: {
        freq_hz: { type: 'number' },
        bandwidth_mhz: { type: 'number' },
        power_dbm: { type: 'number' }
      },
      additionalProperties: false
    },
    configureWlanParams: {
      type: 'object',
      properties: {
        standard: { type: 'string' },
        ssid: { type: 'string' },
        channel: { type: 'number' },
        frequency_hz: { type: 'number' },
        bandwidth_mhz: { type: 'number' },
        tx_power_dbm: { type: 'number' },
        security_type: { type: 'string' },
        passphrase: { type: 'string' },
        sign_index: { type: 'number' }
      },
      additionalProperties: false
    },
    setWlanIndicesParams: {
      type: 'object',
      required: ['sign_index', 'station_index'],
      properties: {
        sign_index: { type: 'number' },
        station_index: { type: 'number' }
      },
      additionalProperties: false
    },
    setFrequencyParams: {
      type: 'object',
      required: ['hz'],
      properties: { hz: { type: 'number' } },
      additionalProperties: false
    },
    setPowerParams: {
      type: 'object',
      required: ['dbm'],
      properties: { dbm: { type: 'number' } },
      additionalProperties: false
    },
    enableOutputParams: {
      type: 'object',
      required: ['enable'],
      properties: { enable: { type: 'boolean' } },
      additionalProperties: false
    },
    loadWaveformParams: {
      type: 'object',
      required: ['waveform_name'],
      properties: { waveform_name: { type: 'string' } },
      additionalProperties: false
    },
    switchRfPathParams: {
      type: 'object',
      required: ['path'],
      properties: { path: { type: 'string' } },
      additionalProperties: false
    },
    setAttenuationParams: {
      type: 'object',
      required: ['port', 'db'],
      properties: {
        port: { type: 'string' },
        db: { type: 'number' }
      },
      additionalProperties: false
    },
    enableAmplifierParams: {
      type: 'object',
      required: ['port', 'enable'],
      properties: {
        port: { type: 'string' },
        enable: { type: 'boolean' }
      },
      additionalProperties: false
    },
    getSwitchStateParams: {
      type: 'object',
      required: ['path'],
      properties: { path: { type: 'string' } },
      additionalProperties: false
    },
    triggerHandoverParams: {
      oneOf: [
        {
          type: 'object',
          required: ['target_cell'],
          properties: { target_cell: { type: 'number' } },
          additionalProperties: false
        },
        {
          type: 'object',
          required: ['target_config'],
          properties: { target_config: { type: 'object' } },
          additionalProperties: true
        }
      ]
    },
    startTrafficParams: {
      type: 'object',
      required: ['server_ip'],
      properties: {
        server_ip: { type: 'string' },
        duration: { type: 'number', minimum: 0 },
        bandwidth: { type: 'string' }
      },
      additionalProperties: false
    }
  }
};
