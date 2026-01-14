import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import {
  Typography, Container, Grid, Card, CardContent, CardActions, Button, Chip, Box, CircularProgress, Alert, Paper,
  FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  SettingsInputAntenna as AntennaIcon,
  Speed as SpeedIcon,
  DeveloperBoard as BoardIcon,
  WifiTethering as WifiIcon,
  Router as RouterIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * 仪表状态数据接口
 */
interface InstrumentStatus {
  id: string;
  name: string;
  address: string;
  connected: boolean;
  simulation: boolean;
  driver_info?: {
    driver_class: string;
    driver_module: string;
    idn: string;
  };
}

/**
 * 场景信息接口
 */
interface ScenarioInfo {
  filename: string;
  id: string;
  name: string;
  version: string;
}

/**
 * 实时指标数据点
 */
interface MetricsPoint {
  time: number;  // 相对时间 (秒)
  throughput: number;  // Mbps
  bler: number;  // 百分比
}

/**
 * 根据仪表 ID 返回对应的 Material Icon
 */
const getIcon = (id: string) => {
  if (id.includes('vna')) return <RouterIcon fontSize="large" color="primary" />;
  if (id.includes('vsg')) return <WifiIcon fontSize="large" color="secondary" />;
  if (id.includes('spec')) return <SpeedIcon fontSize="large" color="success" />;
  if (id.includes('chan')) return <AntennaIcon fontSize="large" color="warning" />;
  return <BoardIcon fontSize="large" />;
};

/**
 * 仪表盘页面组件
 * 展示仪表状态、实时指标图表和运行日志
 */
export default function Dashboard() {
  // 状态管理
  const [instruments, setInstruments] = useState<InstrumentStatus[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  // 实时指标数据 (滑动窗口 60 秒)
  const [metricsData, setMetricsData] = useState<MetricsPoint[]>([]);
  const metricsStartTime = useRef<number | null>(null);

  /**
   * 从后端 API 获取仪表状态数据
   */
  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<InstrumentStatus[]>('http://127.0.0.1:8000/api/v1/instruments/status');
      setInstruments(response.data);
    } catch (err) {
      console.error(err);
      setError('无法连接到后端服务，请确认 backend 正在运行。');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取可用测试场景列表
   */
  const fetchScenarios = async () => {
    try {
      const res = await axios.get<ScenarioInfo[]>('http://127.0.0.1:8000/api/v1/scenarios');
      setScenarios(res.data);
      if (res.data.length > 0) {
        setSelectedScenario(res.data[0].filename);
      }
    } catch (err) {
      console.error("Failed to load scenarios", err);
    }
  };

  // 组件加载时初始化
  useEffect(() => {
    fetchStatus();
    fetchScenarios();
  }, []);

  // WebSocket 日志和指标连接
  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/api/v1/ws/logs');

    ws.onopen = () => {
      setLogs(prev => [...prev, "[System] 连接到实时日志服务..."]);
    };

    ws.onmessage = (event) => {
      const rawData = event.data;

      // 尝试解析 JSON (metrics 消息)
      try {
        const parsed = JSON.parse(rawData);
        if (parsed.type === 'metrics' && parsed.data) {
          // 处理实时指标数据
          const now = Date.now() / 1000;
          if (metricsStartTime.current === null) {
            metricsStartTime.current = now;
          }
          const relativeTime = now - metricsStartTime.current;

          setMetricsData(prev => {
            const newPoint: MetricsPoint = {
              time: parseFloat(relativeTime.toFixed(1)),
              throughput: parsed.data.throughput_mbps || 0,
              bler: (parsed.data.bler || 0) * 100  // 转为百分比
            };
            // 保留最近 60 秒的数据
            const updated = [...prev, newPoint];
            if (updated.length > 120) {
              return updated.slice(-120);
            }
            return updated;
          });
          return;  // 不显示在日志区
        }
      } catch {
        // 非 JSON，作为普通日志处理
      }

      // 普通日志消息
      setLogs(prev => {
        const newLogs = [...prev, rawData];
        if (newLogs.length > 500) return newLogs.slice(-500);
        return newLogs;
      });
    };

    ws.onclose = () => {
      setLogs(prev => [...prev, "[System] 日志服务已断开"]);
    };

    return () => {
      ws.close();
    };
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // 开始测试
  const handleStart = async () => {
    // 重置指标数据
    setMetricsData([]);
    metricsStartTime.current = null;

    try {
      const url = selectedScenario
        ? `http://127.0.0.1:8000/api/v1/test/start?filename=${selectedScenario}`
        : 'http://127.0.0.1:8000/api/v1/test/start';

      await axios.post(url);
      setIsRunning(true);
      setLogs(prev => [...prev, `>>> 发送启动指令: ${selectedScenario || 'Default'}...`]);
    } catch (err) {
      alert("启动失败");
    }
  };

  // 停止测试
  const handleStop = async () => {
    try {
      await axios.post('http://127.0.0.1:8000/api/v1/test/stop');
      setIsRunning(false);
      setLogs(prev => [...prev, ">>> 发送停止指令..."]);
    } catch (err) {
      alert("停止失败");
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* 页面头部: 标题与操作栏 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">仪表状态监控</Typography>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {/* 场景选择器 */}
          <FormControl sx={{ minWidth: 220 }} size="small">
            <InputLabel>选择测试场景</InputLabel>
            <Select
              value={selectedScenario}
              label="选择测试场景"
              onChange={(e) => setSelectedScenario(e.target.value)}
              disabled={isRunning}
            >
              {scenarios.map((s) => (
                <MenuItem key={s.filename} value={s.filename}>
                  {s.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="contained"
            color="success"
            startIcon={<PlayIcon />}
            onClick={handleStart}
            disabled={isRunning || !selectedScenario}
          >
            开始测试
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<StopIcon />}
            onClick={handleStop}
            disabled={!isRunning}
          >
            停止测试
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchStatus}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
      </Box>

      {/* 错误提示区域 */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* 仪表卡片区域 */}
      {loading && instruments.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5, mb: 5 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {instruments.map((inst) => (
            <Grid item xs={12} sm={6} md={4} key={inst.id}>
              <Card elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ mr: 2 }}>{getIcon(inst.id)}</Box>
                    <Box>
                      <Typography variant="h6">{inst.name}</Typography>
                      <Typography variant="body2" color="text.secondary">ID: {inst.id}</Typography>
                    </Box>
                  </Box>

                  <Typography variant="body2" sx={{ mb: 1.5 }} color="text.secondary">
                    地址: {inst.address}
                  </Typography>

                  {inst.driver_info && (
                    <Box sx={{ mb: 2, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="caption" display="block" color="text.secondary">
                        Driver: <Box component="span" sx={{ color: 'primary.main', fontWeight: 'bold' }}>
                          {inst.driver_info.driver_class}
                        </Box>
                      </Typography>
                      <Typography variant="caption" display="block" noWrap title={inst.driver_info.idn} sx={{ fontSize: '0.7rem' }}>
                        IDN: {inst.driver_info.idn.split(',')[0]}...
                      </Typography>
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      icon={inst.connected ? <CheckCircleIcon /> : <WarningIcon />}
                      label={inst.connected ? "已连接" : "断开"}
                      color={inst.connected ? "success" : "error"}
                      size="small"
                      variant="outlined"
                    />
                    {inst.simulation && (
                      <Chip label="模拟模式" color="warning" size="small" variant="outlined" />
                    )}
                  </Box>
                </CardContent>
                <CardActions sx={{ mt: 'auto', justifyContent: 'flex-end' }}>
                  <Button size="small">详情</Button>
                  <Button size="small" color="warning">重连</Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* 实时指标图表区域 */}
      <Typography variant="h5" sx={{ mb: 2 }}>实时性能指标</Typography>
      <Paper elevation={3} sx={{ p: 2, mb: 4 }}>
        {metricsData.length === 0 ? (
          <Box sx={{ height: 250, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography color="text.secondary">运行测试后将显示实时数据...</Typography>
          </Box>
        ) : (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={metricsData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                label={{ value: '时间 (秒)', position: 'insideBottomRight', offset: -5 }}
              />
              <YAxis
                yAxisId="left"
                label={{ value: 'Throughput (Mbps)', angle: -90, position: 'insideLeft' }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                label={{ value: 'BLER (%)', angle: 90, position: 'insideRight' }}
                domain={[0, 10]}
              />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="throughput"
                stroke="#2196f3"
                strokeWidth={2}
                dot={false}
                name="吞吐量 (Mbps)"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="bler"
                stroke="#f44336"
                strokeWidth={2}
                dot={false}
                name="BLER (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Paper>

      {/* 实时日志控制台 */}
      <Typography variant="h5" sx={{ mb: 2 }}>实时运行日志</Typography>
      <Paper elevation={4} sx={{
        bgcolor: '#000',
        color: '#0f0',
        p: 2,
        height: 200,
        overflowY: 'auto',
        fontFamily: 'Consolas, monospace',
        fontSize: '0.9rem',
        borderRadius: 2
      }}>
        {logs.map((log, idx) => (
          <div key={idx}>{log}</div>
        ))}
        <div ref={logEndRef} />
      </Paper>
    </Container>
  );
}