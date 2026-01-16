import {
    Box,
    Typography,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Chip,
    List,
    ListItem,
    ListItemText
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';

export default function ConfigHelp() {
    return (
        <Box sx={{ height: '100%', overflow: 'auto', p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <InfoIcon color="primary" />
                <Typography variant="h6">配置参数说明</Typography>
            </Box>

            {/* 主配置 config.yaml */}
            <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" fontWeight="bold">主配置 (config.yaml)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <List dense>
                        <ListItem>
                            <ListItemText
                                primary={<Typography variant="body2" fontWeight="bold">instruments</Typography>}
                                secondary="仪表配置对象，包含 VNA、VSG、信道模拟器等设备的 VISA 地址和超时设置"
                            />
                        </ListItem>
                        <ListItem>
                            <ListItemText
                                primary={<Typography variant="body2" fontWeight="bold">dut.device_id</Typography>}
                                secondary="Android 设备序列号，设为 null 时自动检测"
                            />
                        </ListItem>
                        <ListItem>
                            <ListItemText
                                primary={<Typography variant="body2" fontWeight="bold">dut.wifi_interface</Typography>}
                                secondary="WiFi 网络接口名称，默认 'wlan0'"
                            />
                        </ListItem>
                    </List>
                </AccordionDetails>
            </Accordion>

            {/* 场景配置 */}
            <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" fontWeight="bold">场景配置 (Scenario YAML)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {/* metadata */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>metadata</Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="id"
                                        secondary="场景唯一标识符"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="name"
                                        secondary="场景显示名称"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="version"
                                        secondary="版本号，默认 '1.0'"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* config.type */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom component="div">
                                config.type <Chip label="必需" size="small" color="error" sx={{ ml: 1 }} />
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                                测试场景类型，可选值：
                            </Typography>
                            <Box sx={{ pl: 2 }}>
                                <Chip label="sensitivity" size="small" sx={{ mr: 1, mb: 0.5 }} /> 灵敏度测试<br />
                                <Chip label="blocking" size="small" sx={{ mr: 1, mb: 0.5 }} /> 阻塞测试<br />
                                <Chip label="dynamic_scenario" size="small" sx={{ mr: 1 }} /> 动态场景测试
                            </Box>
                        </Box>

                        {/* sensitivity 参数 */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" color="primary.main" gutterBottom>
                                灵敏度测试专用参数 (type: sensitivity)
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.start_power_dbm"
                                        secondary="起始功率 (dBm)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.end_power_dbm"
                                        secondary="终止功率 (dBm)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.step_db"
                                        secondary="功率步进 (dB)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.search.target_bler"
                                        secondary="目标误块率，例如 0.05 表示 5%"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* dynamic_scenario 参数 */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" color="success.main" gutterBottom>
                                动态场景专用参数 (type: dynamic_scenario)
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.total_duration"
                                        secondary="总测试时长 (秒)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.channel.model"
                                        secondary="信道模型名称 (如 'Urban_Macro.scn')"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.channel.velocity_kmh"
                                        secondary="移动速度 (km/h)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="config.timeline"
                                        secondary="时间轴事件数组"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>

                        {/* timeline 事件 */}
                        <Box>
                            <Typography variant="body2" fontWeight="bold" gutterBottom>
                                timeline 事件结构
                            </Typography>
                            <List dense disablePadding>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="time"
                                        secondary="触发时间 (秒)"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="target"
                                        secondary="目标设备: channel_emulator, dut, tester, vsg"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="action"
                                        secondary="执行动作: load_channel_model, set_velocity, set_path_loss 等"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                                <ListItem sx={{ pl: 2 }}>
                                    <ListItemText
                                        primary="params"
                                        secondary="动作参数对象"
                                        primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                                    />
                                </ListItem>
                            </List>
                        </Box>
                    </Box>
                </AccordionDetails>
            </Accordion>

            {/* 常见示例 */}
            <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1" fontWeight="bold">常见配置示例</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Typography variant="caption" component="pre" sx={{
                        bgcolor: 'grey.900',
                        color: 'grey.100',
                        p: 1.5,
                        borderRadius: 1,
                        overflow: 'auto',
                        fontSize: '11px',
                        fontFamily: 'monospace'
                    }}>
                        {`# 动态场景时间轴事件示例
timeline:
  - time: 0
    target: channel_emulator
    action: load_channel_model
    params:
      model: "Urban_Macro.scn"
    comment: "加载城市宏站信道模型"
  
  - time: 10
    target: channel_emulator
    action: set_path_loss
    params:
      loss_db: 80
    comment: "设置路损为 80dB"`}
                    </Typography>
                </AccordionDetails>
            </Accordion>
        </Box>
    );
}
