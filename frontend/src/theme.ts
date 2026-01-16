import { createTheme } from '@mui/material/styles';
import type { Theme } from '@mui/material/styles';

/**
 * 通用组件样式定义
 */
const commonComponents = {
  // 统一卡片样式
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        transition: 'transform 0.2s',
        '&:hover': {
          boxShadow: '0 8px 16px rgba(0,0,0,0.2)',
        },
      },
    },
  },
  // 统一按钮圆角
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        textTransform: 'none' as const,
      },
    },
  },
  // 统一 Chip 标签样式
  MuiChip: {
    styleOverrides: {
      root: {
        fontWeight: 'bold' as const,
      },
    },
  },
};

/**
 * 通用字体定义
 */
const commonTypography = {
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
};

/**
 * 深色主题
 * 采用深色模式以适应实验室低光环境和专业仪表风格
 */
export const darkTheme: Theme = createTheme({
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
  typography: commonTypography,
  components: {
    ...commonComponents,
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'transform 0.2s',
          '&:hover': {
            boxShadow: '0 8px 16px rgba(0,0,0,0.4)',
          },
        },
      },
    },
  },
});

/**
 * 亮色主题
 * 提供明亮的界面选项，适合日间使用
 */
export const lightTheme: Theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2', // 蓝色
    },
    secondary: {
      main: '#e91e63', // 粉色
    },
    background: {
      default: '#f5f5f5', // 浅灰背景
      paper: '#ffffff',   // 白色卡片背景
    },
    success: {
      main: '#4caf50', // 绿色
    },
    warning: {
      main: '#ff9800', // 橙色
    },
    error: {
      main: '#f44336', // 红色
    },
  },
  typography: commonTypography,
  components: commonComponents,
});

// 默认导出深色主题以保持向后兼容
export default darkTheme;
