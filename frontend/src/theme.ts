import { createTheme } from '@mui/material/styles';

/**
 * 全局应用主题定义
 * 采用深色模式 (Dark Mode) 以适应实验室低光环境和专业仪表风格
 */
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9', // 浅蓝色，用于主要操作按钮
    },
    secondary: {
      main: '#f48fb1', // 粉色，用于辅助操作
    },
    background: {
      default: '#121212', // 极深灰背景
      paper: '#1e1e1e',   // 稍浅的卡片背景
    },
    success: {
      main: '#66bb6a', // 绿色，用于状态正常
    },
    warning: {
      main: '#ffa726', // 橙色，用于模拟模式或警告
    },
    error: {
      main: '#f44336', // 红色，用于断开或错误
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h4: {
      fontWeight: 600,
      letterSpacing: '0.05rem',
      marginBottom: '1.5rem',
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    // 统一卡片样式
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12, // 圆角
          transition: 'transform 0.2s', // 悬停动画准备
          '&:hover': {
            boxShadow: '0 8px 16px rgba(0,0,0,0.4)',
          },
        },
      },
    },
    // 统一按钮圆角
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none', // 取消全大写
        },
      },
    },
    // 统一 Chip 标签样式
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 'bold',
        },
      },
    },
  },
});

export default theme;
