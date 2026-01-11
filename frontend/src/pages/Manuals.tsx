import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Container, Typography, Box, Accordion, AccordionSummary, AccordionDetails,
  List, ListItem, ListItemText, ListItemSecondaryAction, Button,
  Chip, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  FormControl, InputLabel, Select, MenuItem, Alert, CircularProgress
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Description as PdfIcon,
  CloudUpload as UploadIcon,
  Language as WebIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';

// --- 数据接口定义 ---

/**
 * 单本手册的数据结构
 */
interface ManualEntry {
  title: string;      // 手册标题
  type: string;       // 手册类型 (如 user_guide)
  url: string;        // 下载链接或本地文件名
  notes?: string;     // 备注信息
  is_local: boolean;  // 是否已缓存到本地
  local_url?: string; // 本地静态资源访问路径
}

/**
 * 仪器系列的数据结构
 * 包含该系列下的所有型号和手册列表
 */
interface SeriesEntry {
  vendor: string;     // 厂商 (如 Keysight)
  series: string;     // 系列名 (如 X-Series)
  models: string[];   // 包含的型号列表
  manuals: ManualEntry[]; // 手册列表
}

/**
 * 完整目录响应结构
 */
interface CatalogResponse {
  categories: Record<string, SeriesEntry[]>; // 按类别分组的系列列表
}

// --- 组件定义 ---

/**
 * 仪表手册库页面组件
 * 提供手册浏览、在线预览以及 PDF 上传功能
 */
export default function Manuals() {
  // 状态管理
  const [catalog, setCatalog] = useState<CatalogResponse['categories']>({});
  const [loading, setLoading] = useState(false);
  
  // 上传对话框状态
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadVendor, setUploadVendor] = useState('');
  const [uploadSeries, setUploadSeries] = useState('');
  const [uploading, setUploading] = useState(false);

  /**
   * 获取手册目录数据
   */
  const fetchCatalog = async () => {
    setLoading(true);
    try {
      const res = await axios.get<CatalogResponse>('http://127.0.0.1:8000/api/v1/manuals');
      setCatalog(res.data.categories);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    fetchCatalog();
  }, []);

  /**
   * 处理文件上传逻辑
   */
  const handleUpload = async () => {
    if (!selectedFile || !uploadCategory || !uploadVendor || !uploadSeries) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('category', uploadCategory);
    formData.append('vendor', uploadVendor);
    formData.append('series', uploadSeries);

    try {
      await axios.post('http://127.0.0.1:8000/api/v1/manuals/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      // 上传成功后关闭对话框并刷新列表
      setUploadOpen(false);
      setSelectedFile(null);
      fetchCatalog(); 
    } catch (err) {
      alert("上传失败，请查看控制台日志。");
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const categories = Object.keys(catalog);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* 页面头部: 标题与操作按钮 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">仪表手册库</Typography>
        <Button 
          variant="contained" 
          startIcon={<UploadIcon />} 
          onClick={() => setUploadOpen(true)}
        >
          上传手册
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box>
          {categories.length === 0 && <Alert severity="info">暂无手册数据</Alert>}
          
          {categories.map((cat) => (
            <Box key={cat} sx={{ mb: 4 }}>
              {/* 分类标题 (如 Spectrum Analyzer) */}
              <Typography variant="h5" sx={{ mb: 2, textTransform: 'capitalize', borderLeft: '4px solid #90caf9', pl: 2 }}>
                {cat.replace('_', ' ')}
              </Typography>
              
              {catalog[cat].map((series, idx) => {
                // --- 智能过滤逻辑 ---
                // 目的: 如果用户已手动上传了某个手册 (is_local=true)，
                // 则自动隐藏那些提示“需登录下载”或“联系厂商”的占位条目，避免列表冗余。
                
                // 1. 检查该系列下是否存在任何本地手册
                const hasLocal = series.manuals.some(m => m.is_local);
                
                // 2. 过滤列表
                const visibleManuals = series.manuals.filter(m => {
                  if (hasLocal && !m.is_local) {
                    // 检查是否是占位符 (支持英文和中文关键词)
                    const note = m.notes ? m.notes.toLowerCase() : "";
                    const url = m.url.toLowerCase();
                    
                    const isPlaceholder = 
                      url.includes("unavailable") || 
                      note.includes("login") || 
                      note.includes("contact") ||
                      note.includes("需登录") ||
                      note.includes("联系");
                    
                    if (isPlaceholder) return false; // 如果是占位符且已有本地版，则隐藏它
                  }
                  return true;
                });

                return (
                  <Accordion key={`${series.vendor}-${series.series}-${idx}`} sx={{ mb: 1 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography sx={{ width: '33%', flexShrink: 0, fontWeight: 'bold' }}>
                        {series.vendor} {series.series}
                      </Typography>
                      <Typography sx={{ color: 'text.secondary' }}>
                        支持型号: {series.models.join(', ')}
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List>
                        {visibleManuals.map((manual, mIdx) => (
                          <ListItem key={mIdx} divider>
                            <ListItemText 
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <PdfIcon color={manual.is_local ? "success" : "action"} />
                                  {manual.title}
                                  {manual.is_local && <Chip label="本地已存" color="success" size="small" />}
                                </Box>
                              }
                              secondary={manual.notes}
                            />
                            <ListItemSecondaryAction>
                              {manual.is_local && manual.local_url ? (
                                <Button 
                                  variant="outlined" 
                                  size="small" 
                                  startIcon={<ViewIcon />}
                                  href={`http://127.0.0.1:8000${manual.local_url}`}
                                  target="_blank"
                                >
                                  预览
                                </Button>
                              ) : (
                                <Button 
                                  variant="text" 
                                  size="small" 
                                  startIcon={<WebIcon />}
                                  href={manual.url}
                                  target="_blank"
                                  disabled={manual.url.includes("unavailable")}
                                >
                                  {manual.url.includes("unavailable") ? "不可用" : "官网链接"}
                                </Button>
                              )}
                            </ListItemSecondaryAction>
                          </ListItem>
                        ))}
                        {visibleManuals.length === 0 && (
                          <Typography variant="body2" sx={{ p: 2, color: 'text.secondary' }}>
                            暂无手册记录
                          </Typography>
                        )}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                );
              })}
            </Box>
          ))}
        </Box>
      )}

      {/* --- 上传对话框 --- */}
      <Dialog open={uploadOpen} onClose={() => setUploadOpen(false)}>
        <DialogTitle>上传 PDF 手册</DialogTitle>
        <DialogContent sx={{ minWidth: 400, pt: 2 }}>
          <Alert severity="info" sx={{ mb: 2 }}>
             为保持库结构整洁，仅支持上传到现有的厂商系列中。
          </Alert>

          {/* 1. 仪器类型选择 */}
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>仪器类型</InputLabel>
            <Select 
              value={uploadCategory} 
              label="仪器类型"
              onChange={(e) => {
                setUploadCategory(e.target.value);
                setUploadVendor(''); // 重置厂商
                setUploadSeries(''); // 重置系列
              }}
            >
              {categories.map(c => <MenuItem key={c} value={c}>{c.replace('_', ' ')}</MenuItem>)}
            </Select>
          </FormControl>
          
          {/* 2. 厂商选择 (级联) */}
          <FormControl fullWidth sx={{ mb: 2 }} disabled={!uploadCategory}>
            <InputLabel>厂商 (Vendor)</InputLabel>
            <Select 
              value={uploadVendor} 
              label="厂商 (Vendor)"
              onChange={(e) => {
                setUploadVendor(e.target.value);
                setUploadSeries(''); // 重置系列
              }}
            >
              {uploadCategory && catalog[uploadCategory]
                // 提取该分类下所有唯一的厂商名
                .map(s => s.vendor)
                .filter((v, i, a) => a.indexOf(v) === i)
                .map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)
              }
            </Select>
          </FormControl>

          {/* 3. 系列选择 (级联) */}
          <FormControl fullWidth sx={{ mb: 2 }} disabled={!uploadVendor}>
            <InputLabel>系列 (Series)</InputLabel>
            <Select 
              value={uploadSeries} 
              label="系列 (Series)"
              onChange={(e) => setUploadSeries(e.target.value)}
            >
              {uploadCategory && uploadVendor && catalog[uploadCategory]
                // 提取该厂商下的所有系列
                .filter(s => s.vendor === uploadVendor)
                .map(s => <MenuItem key={s.series} value={s.series}>{s.series}</MenuItem>)
              }
            </Select>
          </FormControl>
          
          <Button
            variant="outlined"
            component="label"
            fullWidth
            startIcon={<UploadIcon />}
          >
            {selectedFile ? selectedFile.name : "选择文件 (.pdf / .html)"}
            <input 
              type="file" 
              hidden 
              accept=".pdf,.html,.htm"
              onChange={(e) => e.target.files && setSelectedFile(e.target.files[0])} 
            />
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadOpen(false)}>取消</Button>
          <Button 
            onClick={handleUpload} 
            variant="contained" 
            disabled={uploading || !selectedFile || !uploadSeries}
          >
            {uploading ? "上传中..." : "开始上传"}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
