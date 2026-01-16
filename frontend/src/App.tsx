import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box, CssBaseline, IconButton, Tooltip } from '@mui/material';
import {
  Dashboard as DashboardIcon,
  LibraryBooks as LibraryIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Router as RouterIcon
} from '@mui/icons-material';

import Dashboard from './pages/Dashboard';
import Manuals from './pages/Manuals';
import History from './pages/History';
import ConfigEditor from './pages/ConfigEditor';
import ChannelModels from './pages/ChannelModels';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

/**
 * 导航栏组件 - 提取出来以便使用 useTheme hook
 */
function NavigationBar() {
  const { mode, toggleTheme } = useTheme();

  return (
    <AppBar position="static" color="default" elevation={2} sx={{ mb: 2 }}>
      <Toolbar>
        {/* 系统标题 */}
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
          终端宽带标准信道验证系统
        </Typography>

        {/* 导航菜单区域 */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            color="inherit"
            component={Link}
            to="/"
            startIcon={<DashboardIcon />}
          >
            仪表监控
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/history"
            startIcon={<HistoryIcon />}
          >
            历史记录
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/config"
            startIcon={<SettingsIcon />}
          >
            配置
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/channel-models"
            startIcon={<RouterIcon />}
          >
            信道模型
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/manuals"
            startIcon={<LibraryIcon />}
          >
            手册库
          </Button>

          {/* 主题切换按钮 */}
          <Tooltip title={mode === 'dark' ? '切换到亮色模式' : '切换到深色模式'}>
            <IconButton color="inherit" onClick={toggleTheme}>
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

/**
 * 应用主体组件
 */
function AppContent() {
  return (
    <BrowserRouter>
      <Box sx={{ flexGrow: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* 顶部导航栏 */}
        <NavigationBar />

        {/* 页面路由配置区域 */}
        <Routes>
          {/* 默认首页: 仪表状态监控仪表盘 */}
          <Route path="/" element={<Dashboard />} />
          {/* 测试历史记录页面 */}
          <Route path="/history" element={<History />} />
          {/* 配置编辑器页面 */}
          <Route path="/config" element={<ConfigEditor />} />
          {/* 信道模型页面 */}
          <Route path="/channel-models" element={<ChannelModels />} />
          {/* 仪表手册库页面 */}
          <Route path="/manuals" element={<Manuals />} />
        </Routes>
      </Box>
    </BrowserRouter>
  );
}

/**
 * 应用程序根组件
 * 负责路由配置、全局主题应用以及顶部导航栏的渲染
 */
function App() {
  return (
    <ThemeProvider>
      {/* 规范化 CSS，移除浏览器默认样式差异 */}
      <CssBaseline />
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
