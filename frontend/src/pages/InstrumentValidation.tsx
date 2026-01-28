import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, FactCheck as FactCheckIcon } from '@mui/icons-material';

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

interface InstrumentVerifyStep {
  name: string;
  status: 'pass' | 'fail' | 'skip';
  message: string;
  duration_ms: number;
  error?: string;
}

interface InstrumentVerifyResult {
  instrument_id: string;
  mode: string;
  simulation_mode: boolean;
  duration_ms: number;
  summary: Record<string, number>;
  steps: InstrumentVerifyStep[];
  driver_info?: {
    driver_class: string;
    driver_module: string;
    idn: string;
  };
}

const statusColor = (status: string) => {
  if (status === 'pass') return 'success';
  if (status === 'fail') return 'error';
  return 'warning';
};

export default function InstrumentValidation() {
  const { instrumentId } = useParams();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<InstrumentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyResult, setVerifyResult] = useState<InstrumentVerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = async () => {
    if (!instrumentId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get<InstrumentStatus>(
        `http://127.0.0.1:8000/api/v1/instruments/${instrumentId}`
      );
      setDetail(res.data);
    } catch (err) {
      console.error(err);
      setError('无法获取仪表信息，请确认后端服务正常。');
    } finally {
      setLoading(false);
    }
  };

  const runVerify = async (mode: 'quick' | 'full' | 'full_scpi') => {
    if (!instrumentId) return;
    setVerifyLoading(true);
    setError(null);
    try {
      const res = await axios.post<InstrumentVerifyResult>(
        `http://127.0.0.1:8000/api/v1/instruments/${instrumentId}/scpi/verify`,
        { mode }
      );
      setVerifyResult(res.data);
      await fetchDetail();
    } catch (err) {
      console.error(err);
      setError('SCPI 验证失败，请检查仪表连接或配置。');
    } finally {
      setVerifyLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [instrumentId]);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)}>
          返回
        </Button>
        <Typography variant="h4">仪表 SCPI 验证</Typography>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Stack spacing={3}>
          {error && (
            <Paper elevation={1} sx={{ p: 2, bgcolor: 'error.main', color: 'white' }}>
              <Typography variant="body2">{error}</Typography>
            </Paper>
          )}

          {detail && (
            <Card elevation={3}>
              <CardContent>
                <Stack spacing={1.5}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="h6">{detail.name}</Typography>
                      <Typography variant="body2" color="text.secondary">ID: {detail.id}</Typography>
                    </Box>
                    <Stack direction="row" spacing={1}>
                      <Chip
                        label={detail.connected ? '已连接' : '断开'}
                        color={detail.connected ? 'success' : 'error'}
                        variant="outlined"
                      />
                      {detail.simulation && <Chip label="模拟模式" color="warning" variant="outlined" />}
                    </Stack>
                  </Box>
                  <Typography variant="body2" color="text.secondary">地址: {detail.address}</Typography>
                  {detail.driver_info && (
                    <Box>
                      <Typography variant="caption" display="block" color="text.secondary">
                        Driver: {detail.driver_info.driver_class}
                      </Typography>
                      <Typography variant="caption" display="block" color="text.secondary">
                        IDN: {detail.driver_info.idn}
                      </Typography>
                    </Box>
                  )}
                  <Divider />
                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      startIcon={<FactCheckIcon />}
                      onClick={() => runVerify('quick')}
                      disabled={verifyLoading}
                    >
                      快速验证
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<FactCheckIcon />}
                      onClick={() => runVerify('full')}
                      disabled={verifyLoading}
                    >
                      完整验证
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<FactCheckIcon />}
                      onClick={() => runVerify('full_scpi')}
                      disabled={verifyLoading}
                    >
                      全量SCPI
                    </Button>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          )}

          {verifyLoading && (
            <Paper elevation={2} sx={{ p: 2 }}>
              <Stack direction="row" spacing={2} alignItems="center">
                <CircularProgress size={20} />
                <Typography variant="body2">正在执行 SCPI 验证，请稍候...</Typography>
              </Stack>
            </Paper>
          )}

          {verifyResult && (
            <Paper elevation={2} sx={{ p: 2 }}>
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6">验证结果 ({verifyResult.mode})</Typography>
                  <Typography variant="body2" color="text.secondary">
                    耗时 {verifyResult.duration_ms} ms
                  </Typography>
                </Box>
                <Stack direction="row" spacing={1}>
                  <Chip label={`通过 ${verifyResult.summary.pass ?? 0}`} color="success" />
                  <Chip label={`失败 ${verifyResult.summary.fail ?? 0}`} color="error" />
                  <Chip label={`跳过 ${verifyResult.summary.skip ?? 0}`} color="warning" />
                </Stack>
                <Divider />
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>步骤</TableCell>
                      <TableCell>状态</TableCell>
                      <TableCell>说明</TableCell>
                      <TableCell>耗时(ms)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {verifyResult.steps.map((step, idx) => (
                      <TableRow key={`${step.name}-${idx}`}>
                        <TableCell>{step.name}</TableCell>
                        <TableCell>
                          <Chip size="small" label={step.status} color={statusColor(step.status)} />
                        </TableCell>
                        <TableCell>{step.message}</TableCell>
                        <TableCell>{step.duration_ms.toFixed(1)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Stack>
            </Paper>
          )}
        </Stack>
      )}
    </Container>
  );
}
