import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  Container,
  Avatar,
  Button,
  Tooltip,
  MenuItem,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  useMediaQuery
} from '@mui/material';
import {
  Menu as MenuIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  RestaurantMenu as RecipeIcon,
  CalendarMonth as PlannerIcon,
  AccountCircle as ProfileIcon,
  Logout as LogoutIcon,
  Dashboard as DashboardIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import Footer from '../Footer';

const MainLayout = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const { mode, toggleColorMode } = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery('(max-width:900px)');

  const [anchorElUser, setAnchorElUser] = useState<null | HTMLElement>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleOpenUserMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  const toggleDrawer = (open: boolean) => () => {
    setDrawerOpen(open);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) setDrawerOpen(false);
    if (anchorElUser) handleCloseUserMenu();
  };

  const handleLogout = () => {
    handleCloseUserMenu();
    logout();
  };

  const navItems = [
    { title: 'Dashboard', path: '/dashboard', icon: <DashboardIcon />, requireAuth: true },
    { title: 'Recipes', path: '/recipes', icon: <RecipeIcon />, requireAuth: false },
    { title: 'Meal Planner', path: '/meal-planner', icon: <PlannerIcon />, requireAuth: true },
  ];

  const userMenuItems = [
    { title: 'Dashboard', path: '/dashboard', icon: <DashboardIcon />, action: () => handleNavigation('/dashboard') },
    { title: 'Profile', path: '/profile', icon: <ProfileIcon />, action: () => handleNavigation('/profile') },
    { title: 'Logout', icon: <LogoutIcon />, action: handleLogout },
  ];

  const filteredNavItems = navItems.filter(item => !item.requireAuth || isAuthenticated);

  const drawer = (
    <Box sx={{ width: 250 }} role="presentation">
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" component="div">
          MealMateAI
        </Typography>
      </Box>
      <Divider />
      <List>
        {filteredNavItems.map((item) => (
          <ListItem 
            button 
            key={item.title} 
            onClick={() => handleNavigation(item.path)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.title} />
          </ListItem>
        ))}
      </List>
      <Divider />
      <List>
        {isAuthenticated && userMenuItems.map((item) => (
          <ListItem 
            button 
            key={item.title} 
            onClick={item.action}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.title} />
          </ListItem>
        ))}
        <ListItem button onClick={toggleColorMode}>
          <ListItemIcon>
            {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </ListItemIcon>
          <ListItemText primary={mode === 'dark' ? 'Light Mode' : 'Dark Mode'} />
        </ListItem>
      </List>
    </Box>
  );

  return (
    <Box display="flex" flexDirection="column" minHeight="100vh">
      <AppBar position="sticky">
        <Container maxWidth="xl">
          <Toolbar disableGutters>
            {/* Logo - always visible */}
            <Typography
              variant="h6"
              noWrap
              component="a"
              href="/"
              sx={{
                mr: 2,
                display: 'flex',
                fontWeight: 700,
                color: 'inherit',
                textDecoration: 'none',
              }}
            >
              MealMateAI
            </Typography>

            {/* Mobile menu button */}
            {isMobile && (
              <IconButton
                size="large"
                aria-label="menu"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={toggleDrawer(true)}
                color="inherit"
                sx={{ mr: 'auto' }}
              >
                <MenuIcon />
              </IconButton>
            )}

            {/* Desktop navigation */}
            {!isMobile && (
              <Box sx={{ flexGrow: 1, display: 'flex' }}>
                {filteredNavItems.map((item) => (
                  <Button
                    key={item.title}
                    onClick={() => handleNavigation(item.path)}
                    sx={{ my: 2, color: 'white', display: 'block' }}
                  >
                    {item.title}
                  </Button>
                ))}
              </Box>
            )}

            {/* Theme toggle */}
            <IconButton onClick={toggleColorMode} color="inherit" sx={{ ml: 1 }}>
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>

            {/* User menu (if authenticated) or login button */}
            {isAuthenticated ? (
              <Box sx={{ flexGrow: 0, ml: 1 }}>
                <Tooltip title="Open settings">
                  <IconButton onClick={handleOpenUserMenu} sx={{ p: 0 }}>
                    <Avatar alt={user?.name || 'User'}>
                      {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
                    </Avatar>
                  </IconButton>
                </Tooltip>
                <Menu
                  sx={{ mt: '45px' }}
                  id="menu-appbar"
                  anchorEl={anchorElUser}
                  anchorOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                  }}
                  keepMounted
                  transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                  }}
                  open={Boolean(anchorElUser)}
                  onClose={handleCloseUserMenu}
                >
                  {userMenuItems.map((item) => (
                    <MenuItem key={item.title} onClick={item.action}>
                      <ListItemIcon>{item.icon}</ListItemIcon>
                      <Typography textAlign="center">{item.title}</Typography>
                    </MenuItem>
                  ))}
                </Menu>
              </Box>
            ) : (
              <Button 
                color="inherit" 
                onClick={() => navigate('/login')}
                sx={{ ml: 1 }}
              >
                Login
              </Button>
            )}
          </Toolbar>
        </Container>
      </AppBar>

      {/* Mobile drawer */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer(false)}
      >
        {drawer}
      </Drawer>

      {/* Main content */}
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          p: { xs: 2, sm: 3 }, 
          width: '100%' 
        }}
      >
        <Outlet />
      </Box>

      {/* Footer */}
      <Footer />
    </Box>
  );
};

export default MainLayout;