import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Typography, Container, Box, Paper, List, ListItemButton, ListItemIcon, ListItemText,
  Button, CircularProgress, Alert, Snackbar, TextField, Dialog, DialogTitle,
  DialogContent, DialogActions, Divider
} from '@mui/material';
import {
  Settings as ConfigIcon,
  Description as ScenarioIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Add as AddIcon
} from '@mui/icons-material';
import YamlEditor from '../components/YamlEditor';
import ConfigHelp from '../components/ConfigHelp';

/**
 * 配置文件信息接口
 */
interface ConfigFileInfo {
  filename: string;
  filepath: string;
  file_type: 'config' | 'scenario';
}

/**
 * 配置编辑器页面
 */
export default function ConfigEditor() {
  // 文件列表
  const [files, setFiles] = useState<ConfigFileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 当前编辑的文件
  const [selectedFile, setSelectedFile] = useState<ConfigFileInfo | null>(null);
  const [content, setContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [saving, setSaving] = useState(false);

  // 提示消息
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  // 新建场景对话框
  const [newDialogOpen, setNewDialogOpen] = useState(false);
  const [newFilename, setNewFilename] = useState('');
  const [showHelp, setShowHelp] = useState(true);

  /**
   * 加载文件列表
   */
  const fetchFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get<ConfigFileInfo[]>('http://127.0.0.1:8000/api/v1/config/files');
      setFiles(res.data);
    } catch (err) {
      setError('无法加载配置文件列表');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 加载文件内容
   */
  const loadFileContent = async (file: ConfigFileInfo) => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/v1/config/${file.file_type}/${file.filename}`);
      setContent(res.data.content);
      setOriginalContent(res.data.content);
      setSelectedFile(file);
    } catch (err) {
      setSnackbar({ open: true, message: '加载文件失败', severity: 'error' });
      console.error(err);
    }
  };

  /**
   * 保存文件内容
   */
  const saveContent = async () => {
    if (!selectedFile) return;

    setSaving(true);
    try {
      await axios.put(
        `http://127.0.0.1:8000/api/v1/config/${selectedFile.file_type}/${selectedFile.filename}`,
        { content, filename: selectedFile.filename }
      );
      setOriginalContent(content);
      setSnackbar({ open: true, message: '保存成功', severity: 'success' });
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '保存失败';
      setSnackbar({ open: true, message: detail, severity: 'error' });
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  /**
   * 创建新场景
   */
  const createNewScenario = async () => {
    if (!newFilename) return;

    const filename = newFilename.endsWith('.yaml') ? newFilename : `${newFilename}.yaml`;
    const template = `# 新建测试场景
metadata:
  id: ${newFilename.replace('.yaml', '')}
  name: 新场景
  version: "1.0"
  description: 场景描述

config:
  type: sensitivity  # sensitivity, blocking, dynamic_scenario
  # 在此添加配置参数
`;

    try {
      await axios.post('http://127.0.0.1:8000/api/v1/config/scenario', {
        filename,
        content: template
      });
      setSnackbar({ open: true, message: '场景创建成功', severity: 'success' });
      setNewDialogOpen(false);
      setNewFilename('');
      fetchFiles();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '加载失败';
      setSnackbar({ open: true, message: detail, severity: 'error' });
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const hasChanges = content !== originalContent;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* 页面头部 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">配置编辑器</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant={showHelp ? 'contained' : 'outlined'}
            onClick={() => setShowHelp(!showHelp)}
            size="small"
          >
            {showHelp ? '隐藏帮助' : '显示帮助'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setNewDialogOpen(true)}
          >
            新建场景
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchFiles}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 250px)', minHeight: 500 }}>
        {/* 左侧文件列表 */}
        <Paper elevation={3} sx={{ width: 280, overflow: 'auto' }}>
          <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
            <Typography variant="subtitle1" fontWeight="bold">配置文件</Typography>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress size={24} />
            </Box>
          ) : (
            <List dense>
              {/* 主配置 */}
              {files.filter(f => f.file_type === 'config').map(file => (
                <ListItemButton
                  key={file.filename}
                  selected={selectedFile?.filename === file.filename}
                  onClick={() => loadFileContent(file)}
                >
                  <ListItemIcon>
                    <ConfigIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText primary={file.filename} secondary="主配置" />
                </ListItemButton>
              ))}

              <Divider sx={{ my: 1 }} />

              {/* 场景文件 */}
              <Box sx={{ px: 2, py: 1 }}>
                <Typography variant="caption" color="text.secondary">测试场景</Typography>
              </Box>
              {files.filter(f => f.file_type === 'scenario').map(file => (
                <ListItemButton
                  key={file.filename}
                  selected={selectedFile?.filename === file.filename}
                  onClick={() => loadFileContent(file)}
                >
                  <ListItemIcon>
                    <ScenarioIcon color="secondary" />
                  </ListItemIcon>
                  <ListItemText primary={file.filename} />
                </ListItemButton>
              ))}
            </List>
          )}
        </Paper>

        {/* 右侧编辑区 */}
        <Paper elevation={3} sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* 编辑区头部 */}
          <Box sx={{
            p: 2,
            bgcolor: 'grey.100',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid',
            borderColor: 'divider'
          }}>
            <Typography variant="subtitle1" fontWeight="bold">
              {selectedFile ? selectedFile.filename : '请选择文件'}
              {hasChanges && <span style={{ color: '#f57c00' }}> *</span>}
            </Typography>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={saveContent}
              disabled={!selectedFile || !hasChanges || saving}
            >
              {saving ? '保存中...' : '保存'}
            </Button>
          </Box>

          {/* 编辑器 */}
          {selectedFile ? (
            <Box sx={{ flex: 1, overflow: 'hidden' }}>
              <YamlEditor
                filename={selectedFile.filename}
                value={content}
                onChange={(newValue) => setContent(newValue || '')}
              />
            </Box>
          ) : (
            <Box sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'text.secondary'
            }}>
              <Typography>从左侧选择一个配置文件开始编辑</Typography>
            </Box>
          )}
        </Paper>

        {/* 右侧帮助面板 */}
        {showHelp && (
          <Paper
            elevation={3}
            sx={{
              width: 350,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}
          >
            <ConfigHelp />
          </Paper>
        )}
      </Box>

      {/* 新建场景对话框 */}
      <Dialog open={newDialogOpen} onClose={() => setNewDialogOpen(false)}>
        <DialogTitle>新建测试场景</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="场景文件名"
            placeholder="例如: my_test_scenario.yaml"
            value={newFilename}
            onChange={(e) => setNewFilename(e.target.value)}
            sx={{ mt: 2 }}
            helperText="文件将创建在 scenarios 目录下"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={createNewScenario} disabled={!newFilename}>
            创建
          </Button>
        </DialogActions>
      </Dialog>

      {/* 提示消息 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
