import { useMemo } from 'react';
import {
    Box, Typography, LinearProgress, Paper, List, ListItem, ListItemIcon,
    ListItemText, Chip, Divider
} from '@mui/material';
import {
    PlayArrow as PlayIcon,
    Schedule as ScheduleIcon,
    CheckCircle as CheckIcon,
    RadioButtonUnchecked as PendingIcon,
    Speed as SpeedIcon
} from '@mui/icons-material';

/**
 * 时间轴事件接口
 */
interface TimelineEvent {
    time: number;
    target: string;
    action: string;
    comment?: string;
    params?: Record<string, unknown>;
}

/**
 * 测试进度组件属性
 */
interface TestProgressProps {
    /** 当前经过时间 (秒) */
    elapsedTime: number;
    /** 总时长 (秒) */
    totalDuration: number;
    /** 时间轴事件列表 */
    events?: TimelineEvent[];
    /** 测试是否正在运行 */
    isRunning: boolean;
    /** 当前场景名称 */
    scenarioName?: string;
}

/**
 * 格式化秒为 MM:SS 格式
 */
function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 根据 action 名称返回友好显示名称
 */
function getActionLabel(action: string): string {
    const actionMap: Record<string, string> = {
        'load_channel_model': '加载信道模型',
        'set_velocity': '设置移动速度',
        'set_path_loss': '设置路损',
        'trigger_handover': '触发小区切换',
        'set_power': '设置功率',
        'rf_on': '开启射频',
        'rf_off': '关闭射频',
    };
    return actionMap[action] || action;
}

/**
 * 测试进度可视化组件
 * 展示测试执行进度条和事件时间轴
 */
export default function TestProgress({
    elapsedTime,
    totalDuration,
    events = [],
    isRunning,
    scenarioName
}: TestProgressProps) {
    // 计算进度百分比
    const progress = totalDuration > 0 ? (elapsedTime / totalDuration) * 100 : 0;

    // 分类事件：已完成、进行中、待执行
    const { pastEvents, currentEvent, upcomingEvents } = useMemo(() => {
        const past: TimelineEvent[] = [];
        const upcoming: TimelineEvent[] = [];
        let current: TimelineEvent | null = null;

        // 按时间排序
        const sortedEvents = [...events].sort((a, b) => a.time - b.time);

        for (const event of sortedEvents) {
            if (event.time < elapsedTime - 2) {
                past.push(event);
            } else if (event.time <= elapsedTime + 2 && !current) {
                current = event;
            } else {
                upcoming.push(event);
            }
        }

        return { pastEvents: past, currentEvent: current, upcomingEvents: upcoming.slice(0, 3) };
    }, [events, elapsedTime]);

    // 如果测试未运行，显示待机状态
    if (!isRunning) {
        return (
            <Paper elevation={2} sx={{ p: 2, mb: 3, bgcolor: 'background.paper' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <ScheduleIcon color="disabled" />
                    <Typography variant="subtitle1" color="text.secondary">
                        测试进度
                    </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                    选择场景并点击"开始测试"以查看进度
                </Typography>
            </Paper>
        );
    }

    return (
        <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
            {/* 标题栏 */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PlayIcon color="success" sx={{ animation: 'pulse 1s infinite' }} />
                    <Typography variant="subtitle1" fontWeight="medium">
                        {scenarioName || '测试进行中'}
                    </Typography>
                </Box>
                <Chip
                    icon={<SpeedIcon />}
                    label="运行中"
                    color="success"
                    size="small"
                />
            </Box>

            {/* 进度条 */}
            <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                        进度: {formatTime(elapsedTime)} / {formatTime(totalDuration)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        {progress.toFixed(1)}%
                    </Typography>
                </Box>
                <LinearProgress
                    variant="determinate"
                    value={Math.min(progress, 100)}
                    sx={{
                        height: 10,
                        borderRadius: 5,
                        '& .MuiLinearProgress-bar': {
                            transition: 'transform 0.3s linear',
                        }
                    }}
                />
            </Box>

            {/* 事件时间轴 */}
            {events.length > 0 && (
                <>
                    <Divider sx={{ my: 1.5 }} />
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        事件时间轴
                    </Typography>

                    <List dense sx={{ py: 0 }}>
                        {/* 当前事件 */}
                        {currentEvent && (
                            <ListItem sx={{ bgcolor: 'action.selected', borderRadius: 1, mb: 0.5 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    <PlayIcon color="primary" fontSize="small" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Typography variant="body2" fontWeight="medium">
                                                {getActionLabel(currentEvent.action)}
                                            </Typography>
                                            <Chip label={formatTime(currentEvent.time)} size="small" variant="outlined" />
                                        </Box>
                                    }
                                    secondary={currentEvent.comment || `目标: ${currentEvent.target}`}
                                />
                            </ListItem>
                        )}

                        {/* 即将到来的事件 */}
                        {upcomingEvents.map((event, idx) => (
                            <ListItem key={`upcoming-${idx}`} sx={{ opacity: 0.7 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    <PendingIcon fontSize="small" color="disabled" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Typography variant="body2">
                                                {getActionLabel(event.action)}
                                            </Typography>
                                            <Chip label={formatTime(event.time)} size="small" variant="outlined" />
                                        </Box>
                                    }
                                    secondary={event.comment || `目标: ${event.target}`}
                                />
                            </ListItem>
                        ))}

                        {/* 已完成事件计数 */}
                        {pastEvents.length > 0 && (
                            <ListItem>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    <CheckIcon color="success" fontSize="small" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={
                                        <Typography variant="body2" color="text.secondary">
                                            已完成 {pastEvents.length} 个事件
                                        </Typography>
                                    }
                                />
                            </ListItem>
                        )}
                    </List>
                </>
            )}

            {/* CSS 动画 */}
            <style>
                {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}
            </style>
        </Paper>
    );
}
