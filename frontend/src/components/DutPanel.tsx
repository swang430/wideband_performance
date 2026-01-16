import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import {
    Card, CardContent, Typography, Box, Grid, Chip, LinearProgress,
    Switch, FormControlLabel, Tooltip, CircularProgress, Alert, Divider
} from '@mui/material';
import {
    PhoneAndroid as PhoneIcon,
    SignalCellular4Bar as SignalIcon,
    SignalCellularConnectedNoInternet0Bar as NoSignalIcon,
    AirplanemodeActive as AirplaneIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';

/**
 * DUT 连接状态接口
 */
interface DutStatus {
    connected: boolean;
    simulation_mode?: boolean;
    device_id?: string;
    data_connection?: string;
    error?: string;
}

/**
 * Modem 详细参数接口
 */
interface ModemStatus {
    rsrp: number | null;
    rsrq: number | null;
    sinr: number | null;
    cqi: number | null;
    pci: number | null;
    earfcn: number | null;
    band: string | null;
    network_type: string | null;
    mcc: string | null;
    mnc: string | null;
    cell_id: string | null;
}

/**
 * 信号质量摘要接口
 */
interface SignalQuality {
    level: string;
    description: string;
    bars: number;
}

/**
 * 根据 RSRP 值返回信号强度百分比
 * RSRP 范围: -140 dBm (最差) 到 -44 dBm (最佳)
 */
function rsrpToPercent(rsrp: number | null): number {
    if (rsrp === null) return 0;
    // 映射 -140 ~ -44 到 0% ~ 100%
    const percent = ((rsrp + 140) / 96) * 100;
    return Math.max(0, Math.min(100, percent));
}

/**
 * 根据信号强度返回颜色
 */
function getSignalColor(percent: number): 'success' | 'warning' | 'error' | 'inherit' {
    if (percent >= 60) return 'success';
    if (percent >= 30) return 'warning';
    return 'error';
}

/**
 * DUT 状态面板组件
 * 展示 Android 终端的连接状态、Modem 参数和信号质量
 */
export default function DutPanel() {
    const [dutStatus, setDutStatus] = useState<DutStatus | null>(null);
    const [modemStatus, setModemStatus] = useState<ModemStatus | null>(null);
    const [signalQuality, setSignalQuality] = useState<SignalQuality | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [airplaneMode, setAirplaneMode] = useState(false);
    const [togglingAirplane, setTogglingAirplane] = useState(false);

    // 获取 DUT 状态数据
    const fetchData = useCallback(async () => {
        try {
            setError(null);

            const [statusRes, modemRes, signalRes] = await Promise.all([
                axios.get('/api/v1/dut/status'),
                axios.get('/api/v1/dut/modem'),
                axios.get('/api/v1/dut/signal')
            ]);

            setDutStatus(statusRes.data);
            setModemStatus(modemRes.data);
            setSignalQuality(signalRes.data);
        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : '获取 DUT 状态失败';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    }, []);

    // 初始加载和定时刷新
    useEffect(() => {
        fetchData();
        // 每 5 秒刷新一次
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [fetchData]);

    // 切换飞行模式
    const handleAirplaneModeToggle = async () => {
        setTogglingAirplane(true);
        try {
            await axios.post(`/api/v1/dut/airplane-mode?enable=${!airplaneMode}`);
            setAirplaneMode(!airplaneMode);
            // 切换后刷新状态
            setTimeout(fetchData, 1000);
        } catch (err) {
            console.error('切换飞行模式失败:', err);
        } finally {
            setTogglingAirplane(false);
        }
    };

    // 加载中状态
    if (loading) {
        return (
            <Card sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CircularProgress size={40} />
            </Card>
        );
    }

    // 信号强度百分比
    const signalPercent = rsrpToPercent(modemStatus?.rsrp ?? null);
    const signalColor = getSignalColor(signalPercent);

    return (
        <Card sx={{ height: '100%' }}>
            <CardContent>
                {/* 标题栏 */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <PhoneIcon color="primary" />
                        <Typography variant="h6" component="span">
                            DUT 状态
                        </Typography>
                    </Box>

                    {/* 连接状态标签 */}
                    {dutStatus?.connected ? (
                        <Chip
                            icon={<SignalIcon />}
                            label={dutStatus.simulation_mode ? '模拟模式' : '已连接'}
                            color={dutStatus.simulation_mode ? 'info' : 'success'}
                            size="small"
                        />
                    ) : (
                        <Chip
                            icon={<NoSignalIcon />}
                            label="未连接"
                            color="error"
                            size="small"
                        />
                    )}
                </Box>

                {/* 错误提示 */}
                {error && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {/* 信号强度进度条 */}
                <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                            信号强度
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {modemStatus?.rsrp ? `${modemStatus.rsrp} dBm` : 'N/A'}
                        </Typography>
                    </Box>
                    <LinearProgress
                        variant="determinate"
                        value={signalPercent}
                        color={signalColor}
                        sx={{ height: 8, borderRadius: 4 }}
                    />
                    {signalQuality && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                            {signalQuality.description}
                        </Typography>
                    )}
                </Box>

                <Divider sx={{ mb: 2 }} />

                {/* Modem 参数表格 */}
                <Grid container spacing={1}>
                    <Grid size={6}>
                        <Tooltip title="Reference Signal Received Power">
                            <Box>
                                <Typography variant="caption" color="text.secondary">RSRP</Typography>
                                <Typography variant="body2" fontWeight="medium">
                                    {modemStatus?.rsrp ?? 'N/A'} dBm
                                </Typography>
                            </Box>
                        </Tooltip>
                    </Grid>
                    <Grid size={6}>
                        <Tooltip title="Reference Signal Received Quality">
                            <Box>
                                <Typography variant="caption" color="text.secondary">RSRQ</Typography>
                                <Typography variant="body2" fontWeight="medium">
                                    {modemStatus?.rsrq ?? 'N/A'} dB
                                </Typography>
                            </Box>
                        </Tooltip>
                    </Grid>
                    <Grid size={6}>
                        <Tooltip title="Signal to Interference plus Noise Ratio">
                            <Box>
                                <Typography variant="caption" color="text.secondary">SINR</Typography>
                                <Typography variant="body2" fontWeight="medium">
                                    {modemStatus?.sinr ?? 'N/A'} dB
                                </Typography>
                            </Box>
                        </Tooltip>
                    </Grid>
                    <Grid size={6}>
                        <Tooltip title="Channel Quality Indicator">
                            <Box>
                                <Typography variant="caption" color="text.secondary">CQI</Typography>
                                <Typography variant="body2" fontWeight="medium">
                                    {modemStatus?.cqi ?? 'N/A'}
                                </Typography>
                            </Box>
                        </Tooltip>
                    </Grid>
                </Grid>

                <Divider sx={{ my: 2 }} />

                {/* 网络信息 */}
                <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        网络信息
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {modemStatus?.network_type && (
                            <Chip label={modemStatus.network_type} size="small" variant="outlined" />
                        )}
                        {modemStatus?.band && (
                            <Chip label={`Band ${modemStatus.band}`} size="small" variant="outlined" />
                        )}
                        {modemStatus?.pci !== null && modemStatus?.pci !== undefined && (
                            <Chip label={`PCI ${modemStatus.pci}`} size="small" variant="outlined" />
                        )}
                    </Box>
                </Box>

                {/* 飞行模式控制 */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={airplaneMode}
                                onChange={handleAirplaneModeToggle}
                                disabled={togglingAirplane}
                                icon={<AirplaneIcon />}
                                checkedIcon={<AirplaneIcon />}
                            />
                        }
                        label={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body2">飞行模式</Typography>
                                {togglingAirplane && <CircularProgress size={16} />}
                            </Box>
                        }
                    />

                    {/* 手动刷新按钮 */}
                    <Tooltip title="刷新状态">
                        <RefreshIcon
                            sx={{ cursor: 'pointer', color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
                            onClick={fetchData}
                        />
                    </Tooltip>
                </Box>
            </CardContent>
        </Card>
    );
}
