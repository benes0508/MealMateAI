import { Outlet, Link as RouterLink } from 'react-router-dom';
import { Container, Paper, Box, Typography, Link } from '@mui/material';

const AuthLayout = () => {
  return (
    <Container component="main" maxWidth="xs" sx={{ 
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      py: 4
    }}>
      <Paper 
        elevation={3}
        sx={{ 
          p: 4, 
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          borderRadius: 2
        }}
      >
        <Typography 
          component={RouterLink} 
          to="/" 
          variant="h4" 
          color="primary" 
          sx={{ 
            textDecoration: 'none',
            fontWeight: 700,
            mb: 3
          }}
        >
          MealMateAI
        </Typography>
        
        {/* Outlet renders the child route components */}
        <Outlet />
      </Paper>
      
      <Box mt={3} textAlign="center">
        <Typography variant="body2" color="text.secondary">
          © {new Date().getFullYear()} MealMateAI
        </Typography>
        <Box mt={1}>
          <Link component={RouterLink} to="/" color="primary" variant="body2">
            Back to Home
          </Link>
        </Box>
      </Box>
    </Container>
  );
};

export default AuthLayout;