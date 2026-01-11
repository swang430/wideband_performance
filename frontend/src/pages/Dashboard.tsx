import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { 
  Typography, Container, Grid, Card, CardContent, CardActions, Button, Chip, Box, CircularProgress, Alert, Paper
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

/**
 * 仪表状态数据接口
 */
interface InstrumentStatus {
  id: string;        // 唯一标识符
  name: string;      // 显示名称
  address: string;   // VISA 地址
  connected: boolean;// 连接状态
  simulation: boolean;// 是否为模拟模式
  driver_info?: {    // 驱动详情
    driver_class: string;
    driver_module: string;
    idn: string;
  };
}

/**
 * 根据仪表 ID 返回对应的 Material Icon
 * @param id 仪表标识符
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
 * 展示所有已配置仪表的实时连接状态和基本信息
 */
export default function Dashboard() {
  const [instruments, setInstruments] = useState<InstrumentStatus[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // 测试控制状态
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

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

  // 组件加载时自动获取一次状态
  useEffect(() => {
    fetchStatus();
  }, []);

  // WebSocket 日志连接
  useEffect(() => {
    // 注意：路由前缀是 /api/v1
    const ws = new WebSocket('ws://127.0.0.1:8000/api/v1/ws/logs');
    
    ws.onopen = () => {
      setLogs(prev => [...prev, "[System] 连接到实时日志服务..."]);
    };

    ws.onmessage = (event) => {
      setLogs(prev => {
        // 限制日志长度，防止内存溢出
        const newLogs = [...prev, event.data];
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
    try {
      await axios.post('http://127.0.0.1:8000/api/v1/test/start');
      setIsRunning(true);
      setLogs(prev => [...prev, ">>> 发送测试启动指令..."]);
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
         <Box sx={{ display: 'flex', gap: 2 }}>
            <Button 
              variant="contained" 
              color="success"
              startIcon={<PlayIcon />} 
              onClick={handleStart} 
              disabled={isRunning}
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
              刷新状态
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

      {/* 实时日志控制台 */}
      <Typography variant="h5" sx={{ mb: 2 }}>实时运行日志</Typography>
      <Paper elevation={4} sx={{ 
        bgcolor: '#000', 
        color: '#0f0', 
        p: 2, 
        height: 300, 
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
