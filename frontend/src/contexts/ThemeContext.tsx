import { createContext, useContext, useState, useEffect, useMemo } from 'react';
import type { ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import { darkTheme, lightTheme } from '../theme';

/**
 * 主题模式类型
 */
type ThemeMode = 'light' | 'dark';

/**
 * 主题上下文接口
 */
interface ThemeContextType {
    /** 当前主题模式 */
    mode: ThemeMode;
    /** 切换主题 */
    toggleTheme: () => void;
    /** 设置特定主题 */
    setThemeMode: (mode: ThemeMode) => void;
}

// LocalStorage 存储键
const THEME_STORAGE_KEY = 'wideband-theme-mode';

/**
 * 获取初始主题模式
 * 优先级: localStorage > 系统偏好 > 默认深色
 */
function getInitialMode(): ThemeMode {
    // 从 localStorage 读取
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') {
        return stored;
    }

    // 检查系统偏好
    if (typeof window !== 'undefined' && window.matchMedia) {
        if (window.matchMedia('(prefers-color-scheme: light)').matches) {
            return 'light';
        }
    }

    // 默认深色主题
    return 'dark';
}

// 创建上下文
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * 主题提供者组件属性
 */
interface ThemeProviderProps {
    children: ReactNode;
}

/**
 * 主题提供者组件
 * 管理应用主题状态，并自动持久化用户偏好
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
    const [mode, setMode] = useState<ThemeMode>(getInitialMode);

    // 持久化主题偏好到 localStorage
    useEffect(() => {
        localStorage.setItem(THEME_STORAGE_KEY, mode);
    }, [mode]);

    // 切换主题
    const toggleTheme = () => {
        setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
    };

    // 设置特定主题
    const setThemeMode = (newMode: ThemeMode) => {
        setMode(newMode);
    };

    // 根据模式选择主题对象
    const theme = useMemo(() => {
        return mode === 'light' ? lightTheme : darkTheme;
    }, [mode]);

    // 上下文值
    const contextValue = useMemo(() => ({
        mode,
        toggleTheme,
        setThemeMode,
    }), [mode]);

    return (
        <ThemeContext.Provider value={contextValue}>
            <MuiThemeProvider theme={theme}>
                {children}
            </MuiThemeProvider>
        </ThemeContext.Provider>
    );
}

/**
 * 使用主题上下文的 Hook
 */
export function useTheme(): ThemeContextType {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
