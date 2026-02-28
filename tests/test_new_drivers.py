"""UniCon driver smoke tests (Simulation Mode).

Goal: ensure every driver can be instantiated, connected, and its core API
methods run without raising, even when no real instrument is present.

NOTE: These are *smoke tests* (API contract + import graph), not measurement
validations.
"""

import pytest

from unicon.instruments.base_instrument import BaseInstrument

# Integrated testers
from unicon.instruments.rohde_schwarz.cmw500 import CMW500
from unicon.instruments.anritsu.mt8000a import MT8000A

# VSG
from unicon.instruments.keysight.mxg import KeysightMXG
from unicon.instruments.rohde_schwarz.smw200a import SMW200A

# Spectrum / Signal analyzers
from unicon.instruments.rohde_schwarz.fsw import FSW
from unicon.instruments.keysight.vsa import KeysightVSA

# VNAs
from unicon.instruments.keysight.ena import ENA
from unicon.instruments.keysight.pna import PNA
from unicon.instruments.rohde_schwarz.zna import ZNA

# Channel emulators
from unicon.instruments.spirent.vertex import Vertex
from unicon.instruments.keysight.propsim import Propsim


def test_base_instrument_simulation_connect():
    inst = BaseInstrument("TCPIP::127.0.0.1::INSTR", name="SimInst", simulation_mode=True)
    assert inst._connected is False
    inst.connect()
    assert inst._connected is True
    assert "Simulated" in inst.query("*IDN?")
    inst.disconnect()
    assert inst._connected is False


def test_cmw500_wlan_smoke():
    cmw = CMW500("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    cmw.connect()

    cmw.wlan.set_routing()
    cmw.wlan.configure_rf(tx_power_dbm=-20)
    cmw.wlan.configure_network(ssid="TestAP")

    assert cmw.wlan.start_signaling() is True
    assert cmw.wlan.wait_for_connection(timeout=1.0) is True

    evm = cmw.wlan.fetch_evm()
    pwr = cmw.wlan.fetch_tx_power()
    assert "evm_avg_db" in evm
    assert "power_avg_dbm" in pwr

    cmw.disconnect()


def test_cmw500_lte_smoke():
    cmw = CMW500("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    cmw.connect()

    cmw.lte.set_routing()
    cmw.lte.configure_rf()
    cmw.lte.configure_network(bandwidth="B100", cell_id=1, mimo_mode="SISO")
    cmw.lte.configure_resource_blocks(num_rb=50, start_rb=0, link_dir="DL")

    assert cmw.lte.start_signaling() is True
    assert cmw.lte.wait_for_connection(timeout=1.0) is True

    cmw.disconnect()


def test_mt8000a_smoke_simulation_only():
    mt = MT8000A("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    mt.connect()

    mt.set_rf_frequency(3.5e9, band="n78")
    mt.set_output_power(-40.0)
    assert mt.start_call() is True

    thr = mt.fetch_throughput()
    assert "dl_mbps" in thr and "ul_mbps" in thr

    mt.disconnect()


def test_keysight_mxg_smoke():
    mxg = KeysightMXG("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    mxg.connect()

    mxg.set_frequency(2.4e9)
    mxg.set_power(-10)
    mxg.set_rf_output(True)
    mxg.load_arb_waveform("test_wave")

    mxg.disconnect()


def test_r_s_smw200a_smoke():
    smw = SMW200A("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    smw.connect()

    smw.set_frequency(3.5e9, channel=1)
    smw.set_power(-20, channel=1)
    smw.set_awgn_snr(15, channel=1)
    smw.set_awgn_state(True, channel=1)

    smw.disconnect()


def test_fsw_smoke():
    fsw = FSW("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    fsw.connect()

    fsw.set_frequency_center(2.4e9)
    fsw.set_span(20e6)
    fsw.run_single_sweep()

    x, y = fsw.perform_peak_search()
    assert x == 2.4e9
    assert y == -15.2

    raw = fsw.fetch_trace_data_binary(trace=1)
    assert isinstance(raw, (bytes, bytearray))

    fsw.disconnect()


def test_keysight_vsa_smoke():
    vsa = KeysightVSA("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    vsa.connect()

    vsa.set_frequency_center(2.4e9)
    vsa.set_span(10e6)
    vsa.set_resolution_bandwidth(100e3)
    vsa.run_single_sweep()

    x, y = vsa.perform_peak_search()
    assert x == 2.4e9
    assert y == -15.2

    vsa.disconnect()


def test_ena_smoke():
    ena = ENA("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    ena.connect()

    ena.set_frequency_range(1e9, 3e9)
    ena.set_sweep_points(401)
    ena.set_s_parameter(trace=1, parameter="S21")
    ena.run_single_sweep()

    data = ena.fetch_formatted_data(trace=1)
    assert len(data) == 40

    ena.disconnect()


def test_pna_smoke():
    pna = PNA("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    pna.connect()

    pna.set_frequency_range(1e9, 3e9)
    pna.set_sweep_points(201)
    pna.set_s_parameter(measurement_name="CH1_S21_1", parameter="S21")
    pna.run_single_sweep()

    data = pna.fetch_formatted_data(measurement_name="CH1_S21_1")
    assert len(data) == 40

    pna.disconnect()


def test_zna_smoke():
    zna = ZNA("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    zna.connect()

    zna.set_frequency_range(1e9, 2e9)
    zna.set_sweep_points(201)
    data = zna.measure_s_parameter("S21")
    assert isinstance(data, list)

    zna.disconnect()


def test_vertex_smoke():
    vertex = Vertex("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    vertex.connect()

    vertex.load_scenario("DemoScenario")
    vertex.set_awgn_snr(port_id=1, snr_db=15.0)
    vertex.start_emulation()

    vertex.disconnect()


def test_propsim_smoke():
    ps = Propsim("TCPIP::127.0.0.1::INSTR", simulation_mode=True)
    ps.connect()

    ps.load_scenario("DemoScenario.gcm")
    ps.set_awgn_snr(link_index=1, snr_db=12.0)
    ps.start_emulation()
    ps.stop_emulation()

    ps.disconnect()
