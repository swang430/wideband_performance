import { useState } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Container,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import TerminalIcon from '@mui/icons-material/Terminal';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import MenuBookIcon from '@mui/icons-material/MenuBook';

import Manuals from './pages/Manuals';
import Playground from './pages/Playground';

const drawerWidth = 240;

export default function App() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [currentTab, setCurrentTab] = useState('Playground');

  const handleDrawerToggle = () => setMobileOpen(!mobileOpen);

  const menuItems = [
    { text: 'SCPI Playground', icon: <TerminalIcon />, id: 'Playground' },
    { text: 'Manual Library', icon: <LibraryBooksIcon />, id: 'Manuals' },
  ];

  const renderContent = () => {
    switch (currentTab) {
      case 'Playground':
        return <Playground />;
      case 'Manuals':
        return <Manuals />;
      default:
        return <Playground />;
    }
  };

  const drawer = (
    <Box sx={{ height: '100%', bgcolor: 'background.paper', borderRight: '1px solid', borderColor: 'divider' }}>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="h6" fontWeight="bold" color="primary">
          UniCon Debug
        </Typography>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.id} disablePadding>
            <ListItemButton
              selected={currentTab === item.id}
              onClick={() => {
                setCurrentTab(item.id);
                setMobileOpen(false);
              }}
              sx={{
                mx: 1,
                borderRadius: 1,
                mb: 0.5,
                '&.Mui-selected': {
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  '&:hover': { bgcolor: 'primary.dark' },
                  '& .MuiListItemIcon-root': { color: 'inherit' },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
        
        {/* Link back to API Docs */}
        <ListItem disablePadding sx={{ mt: 2 }}>
            <ListItemButton
              component="a"
              href="https://swang430.github.io/wideband_performance/"
              sx={{
                mx: 1,
                borderRadius: 1,
                color: 'info.main'
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: 'info.main' }}><MenuBookIcon /></ListItemIcon>
              <ListItemText primary="API Docs" />
            </ListItemButton>
          </ListItem>
      </List>
    </Box>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        <AppBar
          position="fixed"
          sx={{
            width: { sm: `calc(100% - ${drawerWidth}px)` },
            ml: { sm: `${drawerWidth}px` },
            bgcolor: 'background.paper',
            color: 'text.primary',
            boxShadow: 1,
          }}
        >
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, display: { sm: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" fontWeight="medium">
              {menuItems.find((i) => i.id === currentTab)?.text}
            </Typography>
          </Toolbar>
        </AppBar>

        <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{ keepMounted: true }}
            sx={{
              display: { xs: 'block', sm: 'none' },
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
            }}
          >
            {drawer}
          </Drawer>
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', sm: 'block' },
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
            }}
            open
          >
            {drawer}
          </Drawer>
        </Box>

        <Box component="main" sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` }, bgcolor: 'background.default' }}>
          <Toolbar />
          <Container maxWidth="xl" sx={{ mt: 2 }}>
            {renderContent()}
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
