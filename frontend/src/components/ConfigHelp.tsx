import {
    Box,
    Typography,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Chip,
    List,
    ListItem,
    ListItemText
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';

export default function ConfigHelp() {
    return (
        <Box sx={{ height: '100%', overflow: 'auto', p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <InfoIcon color="primary" />
                <Typography variant="h6">配置参数说明</Typography>
            </Box>

            {/* 主配置 config.yaml */}
            <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" fontWeight="bold">主配置 (config.yaml)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>instruments</Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="instruments"
                                        secondary={
                                            <Typography variant="caption" color="text.secondary" component="span">
                                                仪表配置对象，键名需与场景的 timeline.target 一致。常见键：
                                                vna, vsg, channel_emulator, integrated_tester, spectrum_analyzer, tcu,
                                                power_meter, emgen, field_probe, positioner
                                            </Typography>
                                        }
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="instruments.<key>.address"
                                        secondary="VISA 资源地址 (必填)，如 TCPIP0::192.168.1.101::inst0::INSTR"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="instruments.<key>.name"
                                        secondary="显示名称 (可选)，用于日志展示"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="instruments.<key>.timeout"
                                        secondary="超时时间 (毫秒，可选)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="instruments.<key>.reset"
                                        secondary="上电是否复位 (可选)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="instruments.<key>.slot / port"
                                        secondary="机箱模块槽位或端口标识 (EMCenter 等设备可选)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="instruments.<key>.type"
                                        secondary="自定义设备类型/型号 (可选，如 attenuator, amplifier)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="instruments.<key>.driver_hint"
                                        secondary="强制驱动匹配关键字 (可选，综测仪可填 UXM / CMW / E7515B 等)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>dut</Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="dut.device_id"
                                        secondary="Android 设备序列号，设为 null 时自动检测"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="dut.wifi_interface"
                                        secondary="WiFi 网络接口名称，默认 'wlan0'"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>test_cases</Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="test_cases"
                                        secondary="预留字段，当前未接入执行器逻辑"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>
                    </Box>
                </AccordionDetails>
            </Accordion>

            {/* 场景配置 */}
            <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" fontWeight="bold">场景配置 (Scenario YAML)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {/* metadata */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>metadata</Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="id"
                                        secondary="场景唯一标识符"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="name"
                                        secondary="场景显示名称"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="version"
                                        secondary="版本号，默认 '1.0'"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="author"
                                        secondary="作者/维护人 (可选)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="description"
                                        secondary="场景描述 (可选)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* config.type */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom component="div">
                                config.type <Chip label="必需" size="small" color="error" sx={{ ml: 1 }} />
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                                测试场景类型，可选值：
                            </Typography>
                            <Box sx={{ pl: 2 }}>
                                <Chip label="sensitivity" size="small" sx={{ mr: 1, mb: 0.5 }} /> 灵敏度测试<br />
                                <Chip label="blocking" size="small" sx={{ mr: 1, mb: 0.5 }} /> 阻塞测试<br />
                                <Chip label="dynamic_scenario" size="small" sx={{ mr: 1 }} /> 动态场景测试
                            </Box>
                            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                                可选字段: config.strategy (如 algorithm, hybrid)
                            </Typography>
                        </Box>

                        {/* sensitivity 参数 */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" color="primary.main" gutterBottom>
                                灵敏度测试专用参数 (type: sensitivity)
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.start_power_dbm"
                                        secondary="起始功率 (dBm)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.end_power_dbm"
                                        secondary="终止功率 (dBm)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.step_db"
                                        secondary="功率步进 (dB)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.target_bler"
                                        secondary="目标误块率，例如 0.05 表示 5%"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.settling_time_s"
                                        secondary="每步稳定等待时间 (秒，可选)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.carrier_freq_hz / bandwidth_mhz / subcarrier_spacing_khz"
                                        secondary="射频基础参数 (可选，用于记录/配置)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* blocking 参数 */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" color="warning.main" gutterBottom>
                                阻塞测试专用参数 (type: blocking)
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.main_signal.freq_hz / power_dbm"
                                        secondary="主信号频率与功率"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.interferer.type"
                                        secondary="干扰类型 (如 CW)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.interferer.freq_offsets_mhz"
                                        secondary="干扰频偏列表 (MHz)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.interferer.start_power_dbm / end_power_dbm / step_db"
                                        secondary="干扰功率扫描范围与步进"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.limit.max_bler"
                                        secondary="阻塞判定阈值 (可选)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* dynamic_scenario 参数 */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" color="success.main" gutterBottom>
                                动态场景专用参数 (type: dynamic_scenario)
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.total_duration"
                                        secondary="总测试时长 (秒)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.channel.model"
                                        secondary="信道模型名称 (如 'Urban_Macro.scn')"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.channel.velocity_kmh"
                                        secondary="移动速度 (km/h)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.setup"
                                        secondary="初始环境参数 (可选，如 carrier_freq_hz, cell_power_dbm)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.timeline"
                                        secondary="时间轴事件数组"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* metrics / limits */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>
                                metrics / limits (可选)
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.metrics.interval"
                                        secondary="采样周期 (秒)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.metrics.collect"
                                        secondary="采样指标列表 (如 throughput_mbps, bler, rsrp, sinr)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.metrics.targets"
                                        secondary="采样目标 (如 integrated_tester)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.limits.*"
                                        secondary="判定阈值 (如 min_throughput_mbps, max_bler)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* timeline 事件 */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>
                                timeline 事件结构
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="time"
                                        secondary="触发时间 (秒)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="target"
                                        secondary="目标设备: channel_emulator, integrated_tester, vsg, tcu, dut 等"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="action"
                                        secondary="执行动作: 直接调用目标对象的方法名"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="params"
                                        secondary="动作参数对象"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="comment"
                                        secondary="可选注释"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* 常用 target / action */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>
                                常用 target / action 速查
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="channel_emulator"
                                        secondary="load_channel_model(model), set_velocity(kmh), set_distance(km), set_path_loss(db), set_fading_profile(profile, duration_ms), rf_on, rf_off"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="integrated_tester"
                                        secondary="set_tech_standard(standard), start_signaling(tech), stop_signaling(), configure_cell(freq_hz, bandwidth_mhz, power_dbm)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="vsg"
                                        secondary="set_frequency(hz), set_power(dbm), enable_output(enable), load_waveform(waveform_name)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="tcu"
                                        secondary="switch_rf_path(path), set_attenuation(port, db), enable_amplifier(port, enable)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="dut"
                                        secondary="start_traffic(server_ip, duration, bandwidth) 等"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>
                    </Box>
                </AccordionDetails>
            </Accordion>

            {/* 常见示例 */}
            <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" fontWeight="bold">常见配置示例</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Typography variant="caption" component="pre" sx={{
                        bgcolor: 'grey.900',
                        color: 'grey.100',
                        p: 1.5,
                        borderRadius: 1,
                        overflow: 'auto',
                        fontSize: '11px',
                        fontFamily: 'monospace'
                    }}>
                        {`# 灵敏度测试示例
metadata:
  id: "SENS_DEMO"
  name: "灵敏度测试示例"
  version: "1.0"

config:
  type: "sensitivity"
  carrier_freq_hz: 3500e6
  bandwidth_mhz: 100
  subcarrier_spacing_khz: 30
  search:
    start_power_dbm: -70
    end_power_dbm: -110
    step_db: 1
    target_bler: 0.05

# 阻塞测试示例
config:
  type: "blocking"
  main_signal:
    freq_hz: 3500e6
    power_dbm: -90
  interferer:
    type: "CW"
    freq_offsets_mhz: [-20, 20]
    start_power_dbm: -60
    end_power_dbm: -30
    step_db: 2
  limit:
    max_bler: 0.05

# 动态场景时间轴事件示例
timeline:
  - time: 0
    target: channel_emulator
    action: load_channel_model
    params:
      model: "WLAN_Model_B_40MHz"
    comment: "加载 WiFi 信道模型"
  
  - time: 10
    target: channel_emulator
    action: set_path_loss
    params:
      db: 80
    comment: "设置路损为 80 dB"

  - time: 12
    target: integrated_tester
    action: start_signaling
    params:
      tech: "WLAN"`}
                    </Typography>
                </AccordionDetails>
            </Accordion>
        </Box>
    );
}
