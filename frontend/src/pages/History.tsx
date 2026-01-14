import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Typography, Container, Box, Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, IconButton, Chip, Dialog, DialogTitle, DialogContent,
  DialogActions, Button, CircularProgress, Alert, Tooltip
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  HourglassEmpty as RunningIcon,
  Cancel as StoppedIcon,
  Refresh as RefreshIcon,
  PictureAsPdf as PdfIcon,
  Code as HtmlIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * 测试运行记录接口
 */
interface TestRunInfo {
  id: number;
  scenario_id: string;
  scenario_name: string;
  test_type: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  result_summary: string | null;
}

/**
 * 指标采样数据
 */
interface MetricsSample {
  elapsed_time: number;
  throughput_mbps: number | null;
  bler: number | null;
  power_dbm: number | null;
}

/**
 * 测试详情接口
 */
interface TestRunDetail {
  run_info: TestRunInfo;
  metrics: MetricsSample[];
  statistics: {
    sample_count: number;
    avg_throughput: number | null;
    max_throughput: number | null;
    min_throughput: number | null;
    avg_bler: number | null;
    max_bler: number | null;
    min_power: number | null;
    max_power: number | null;
  };
}

/**
 * 根据状态返回对应的图标和颜色
 */
const getStatusChip = (status: string) => {
  switch (status) {
    case 'completed':
      return <Chip icon={<SuccessIcon />} label="完成" color="success" size="small" />;
    case 'failed':
      return <Chip icon={<ErrorIcon />} label="失败" color="error" size="small" />;
    case 'running':
      return <Chip icon={<RunningIcon />} label="运行中" color="primary" size="small" />;
    case 'stopped':
      return <Chip icon={<StoppedIcon />} label="已停止" color="warning" size="small" />;
    default:
      return <Chip label={status} size="small" />;
  }
};

/**
 * 格式化日期时间
 */
const formatDateTime = (dt: string | null) => {
  if (!dt) return '-';
  const date = new Date(dt);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

/**
 * 历史记录页面组件
 */
export default function History() {
  const [runs, setRuns] = useState<TestRunInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 详情弹窗状态
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState<TestRunDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  /**
   * 加载历史记录列表
   */
  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get<TestRunInfo[]>('http://127.0.0.1:8000/api/v1/history');
      setRuns(res.data);
    } catch (err) {
      setError('无法加载历史记录，请确认后端服务正在运行。');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 查看测试详情
   */
  const handleViewDetail = async (runId: number) => {
    setDetailLoading(true);
    setDetailOpen(true);
    try {
      const res = await axios.get<TestRunDetail>(`http://127.0.0.1:8000/api/v1/history/${runId}`);
      setSelectedDetail(res.data);
    } catch (err) {
      console.error(err);
      setSelectedDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  /**
   * 删除测试记录
   */
  const handleDelete = async (runId: number) => {
    if (!confirm('确定要删除这条测试记录吗？此操作不可恢复。')) return;

    try {
      await axios.delete(`http://127.0.0.1:8000/api/v1/history/${runId}`);
      setRuns(prev => prev.filter(r => r.id !== runId));
    } catch (err) {
      alert('删除失败');
      console.error(err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* 页面头部 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">测试历史记录</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchHistory}
          disabled={loading}
        >
          刷新
        </Button>
      </Box>

      {/* 错误提示 */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* 加载状态 */}
      {loading && runs.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5 }}>
          <CircularProgress />
        </Box>
      ) : runs.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">暂无测试记录</Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper} elevation={3}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'primary.main' }}>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>ID</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>场景名称</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>测试类型</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>状态</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>开始时间</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>结束时间</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.id} hover>
                  <TableCell>{run.id}</TableCell>
                  <TableCell>{run.scenario_name}</TableCell>
                  <TableCell>
                    <Chip label={run.test_type} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>{getStatusChip(run.status)}</TableCell>
                  <TableCell>{formatDateTime(run.start_time)}</TableCell>
                  <TableCell>{formatDateTime(run.end_time)}</TableCell>
                  <TableCell>
                    <Tooltip title="查看详情">
                      <IconButton
                        color="primary"
                        onClick={() => handleViewDetail(run.id)}
                        size="small"
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="HTML报告">
                      <IconButton
                        color="info"
                        onClick={() => window.open(`http://127.0.0.1:8000/api/v1/report/${run.id}/html`, '_blank')}
                        size="small"
                      >
                        <HtmlIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="PDF报告">
                      <IconButton
                        color="secondary"
                        onClick={() => window.open(`http://127.0.0.1:8000/api/v1/report/${run.id}/pdf`, '_blank')}
                        size="small"
                      >
                        <PdfIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="删除">
                      <IconButton
                        color="error"
                        onClick={() => handleDelete(run.id)}
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* 详情弹窗 */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          测试详情 {selectedDetail && `#${selectedDetail.run_info.id}`}
        </DialogTitle>
        <DialogContent>
          {detailLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : selectedDetail ? (
            <Box>
              {/* 基本信息 */}
              <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Typography variant="subtitle2" gutterBottom>基本信息</Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1 }}>
                  <Typography variant="body2">场景: {selectedDetail.run_info.scenario_name}</Typography>
                  <Typography variant="body2">类型: {selectedDetail.run_info.test_type}</Typography>
                  <Typography variant="body2">开始: {formatDateTime(selectedDetail.run_info.start_time)}</Typography>
                  <Typography variant="body2">结束: {formatDateTime(selectedDetail.run_info.end_time)}</Typography>
                  <Typography variant="body2" sx={{ gridColumn: 'span 2' }}>
                    结果: {selectedDetail.run_info.result_summary || '-'}
                  </Typography>
                </Box>
              </Paper>

              {/* 统计信息 */}
              <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Typography variant="subtitle2" gutterBottom>统计摘要</Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1 }}>
                  <Typography variant="body2">采样点数: {selectedDetail.statistics.sample_count || 0}</Typography>
                  <Typography variant="body2">
                    平均吞吐: {selectedDetail.statistics.avg_throughput?.toFixed(2) || '-'} Mbps
                  </Typography>
                  <Typography variant="body2">
                    平均BLER: {selectedDetail.statistics.avg_bler ? (selectedDetail.statistics.avg_bler * 100).toFixed(2) : '-'}%
                  </Typography>
                </Box>
              </Paper>

              {/* 指标图表 */}
              {selectedDetail.metrics.length > 0 ? (
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>性能曲线</Typography>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={selectedDetail.metrics}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="elapsed_time" label={{ value: '时间 (s)', position: 'bottom' }} />
                      <YAxis yAxisId="left" label={{ value: 'Throughput', angle: -90, position: 'insideLeft' }} />
                      <YAxis yAxisId="right" orientation="right" label={{ value: 'BLER %', angle: 90, position: 'insideRight' }} />
                      <ChartTooltip />
                      <Legend />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="throughput_mbps"
                        stroke="#2196f3"
                        dot={false}
                        name="吞吐量 (Mbps)"
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey={(d: MetricsSample) => d.bler ? d.bler * 100 : null}
                        stroke="#f44336"
                        dot={false}
                        name="BLER (%)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Paper>
              ) : (
                <Typography color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  无指标数据
                </Typography>
              )}
            </Box>
          ) : (
            <Typography color="error">加载失败</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>关闭</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
